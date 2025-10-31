from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from config import load_config
from database import SessionLocal, Account
from orchestrator import build_chat_workflow, ChatState
from agents.models.chat import ChatRequest


router = APIRouter()
config = load_config()
_workflow = build_chat_workflow()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat endpoint using workflow"""
    acct = db.query(Account).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No connected account")

    state = ChatState(
        account_id=acct.id,
        question=request.question,
        top_k=request.top_k,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        conversation_history=[]
    )

    result = await _workflow.ainvoke(
        state,
        config={"configurable": {"thread_id": f"chat_{acct.id}"}}
    )

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "answer": result.get("answer"),
        "sources": result.get("sources", []),
        "metadata": result.get("metadata", {})
    }


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """Streaming chat with SSE using workflow"""
    acct = db.query(Account).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No connected account")

    state = ChatState(
        account_id=acct.id,
        question=request.question,
        top_k=request.top_k,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        conversation_history=[]
    )

    async def event_publisher():
        final_answer = None
        final_sources = None

        async for chunk in _workflow.astream(
            state,
            config={"configurable": {"thread_id": f"chat_stream_{acct.id}"}}
        ):
            for node_name, node_output in chunk.items():
                if "sources" in node_output and node_output.get("sources"):
                    final_sources = node_output["sources"]
                    yield {
                        "event": "sources",
                        "data": {"sources": final_sources},
                    }

                if "answer" in node_output and node_output.get("answer"):
                    final_answer = node_output["answer"]

        if final_answer:
            for char in final_answer:
                yield {"event": "token", "data": {"token": char}}

        yield {"event": "done", "data": {"sources": final_sources or []}}

    return EventSourceResponse(event_publisher())
