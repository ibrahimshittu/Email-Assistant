from __future__ import annotations

from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse
from openai import OpenAI

from config import load_config
from database import SessionLocal, Account
from orchestrator import build_chat_workflow, ChatState
from services import embed_texts, query_chunks
from utils.template_loader import render_template


router = APIRouter()
config = load_config()
_workflow = build_chat_workflow()
_client = OpenAI(api_key=config.openai_api_key)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/chat")
async def chat(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Synchronous chat endpoint using LangGraph orchestrator workflow
    """
    acct = db.query(Account).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No connected account")

    question: str = (payload or {}).get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Missing question")

    # Build ChatState from payload
    state = ChatState(
        account_id=acct.id,
        question=question,
        top_k=int((payload or {}).get("top_k", config.top_k)),
        temperature=float((payload or {}).get("temperature", 0.2)),
        max_tokens=int((payload or {}).get("max_tokens", 500)),
        conversation_history=(payload or {}).get("conversation_history", [])
    )

    # Run workflow
    result = _workflow.invoke(state)

    if result.error:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "answer": result.answer,
        "sources": result.sources,
        "metadata": result.metadata
    }


@router.get("/chat/stream")
async def chat_stream(
    question: str,
    top_k: Optional[int] = None,
    temperature: float = 0.2,
    db: Session = Depends(get_db)
):
    """
    Streaming chat endpoint with Server-Sent Events (SSE)
    """
    acct = db.query(Account).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No connected account")

    if top_k is None:
        top_k = config.top_k

    # Use original question for retrieval
    query_text = question
    q_emb = embed_texts([query_text])[0]
    res = query_chunks(acct.id, q_emb, top_k=top_k)
    contexts = []
    for i in range(len(res.get("ids", [[]])[0])):
        contexts.append({
            "text": res["documents"][0][i],
            "metadata": res["metadatas"][0][i],
            "distance": res["distances"][0][i],
        })

    async def event_publisher():
        # Send sources first
        yield {
            "event": "sources",
            "data": {"sources": [c["metadata"] for c in contexts]},
        }

        # Build prompt
        system = render_template("chat/system_prompt.j2")
        context_text = "\n\n".join([
            f"[message_id={c['metadata'].get('message_id')}] {c['text']}"
            for c in contexts
        ])
        prompt = render_template(
            "chat/user_prompt.j2",
            context_text=context_text,
            question=question
        )

        # Stream response
        stream = _client.chat.completions.create(
            model=config.model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=500,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield {"event": "token", "data": {"token": delta}}

        yield {"event": "done", "data": {}}

    return EventSourceResponse(event_publisher())
