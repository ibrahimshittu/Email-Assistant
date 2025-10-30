from __future__ import annotations

from typing import Optional, Dict, Any, List
from time import perf_counter
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
from openai import OpenAI

from .config import load_config
from .db import SessionLocal, engine
from .models import Base, Account, EmailMessage, EmailThread, SyncState
from .nylas_client import NylasClient, new_state
from .ingest import normalize_message, index_messages, embed_texts
from .vectorstore import query_chunks
from .graph import build_graph
from .eval import run_eval


config = load_config()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Email Assistant RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        config.frontend_base_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_client = OpenAI(api_key=config.openai_api_key)
nylas = NylasClient()
_graph = build_graph()


# Dependency


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/auth/nylas/url")
async def get_auth_url():
    state = new_state()
    return {"auth_url": nylas.get_auth_url(state), "state": state}


@app.get("/nylas/callback")
async def nylas_callback(
    code: str, state: Optional[str] = None, db: Session = Depends(get_db)
):
    try:
        token_data = nylas.exchange_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")

    grant = token_data.get("grant_id") or token_data.get("grant", {}).get("id")
    access_token = token_data.get("access_token") or token_data.get("access_token", "")

    if not grant or not access_token:
        raise HTTPException(
            status_code=400, detail="Missing grant/access token from Nylas response"
        )

    # Upsert account (no email in exchange payload; optional profile fetch could be added)
    acct = db.query(Account).filter(Account.nylas_grant_id == grant).first()
    if not acct:
        acct = Account(
            email="unknown@example.com",
            nylas_grant_id=grant,
            access_token=access_token,
            provider="nylas",
        )
        db.add(acct)
    else:
        acct.access_token = access_token
    db.commit()

    # Redirect to frontend connect page
    redirect_url = f"{config.frontend_base_url}/connect?success=1"
    return RedirectResponse(url=redirect_url, status_code=302)


@app.get("/auth/me")
async def auth_me(db: Session = Depends(get_db)):
    acct = db.query(Account).first()
    if not acct:
        return {"account": None}
    return {"account": {"id": acct.id, "email": acct.email}}


@app.post("/sync/latest")
async def sync_latest(db: Session = Depends(get_db)):
    acct = db.query(Account).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No connected account")

    messages = nylas.fetch_last_messages(acct.access_token, limit=200)
    norm_msgs = [normalize_message(m) for m in messages]

    # Persist message metadata
    inserted = 0
    for m in norm_msgs:
        existing = (
            db.query(EmailMessage)
            .filter(EmailMessage.message_id == m["message_id"])
            .first()
        )
        if existing:
            continue
        row = EmailMessage(
            account_id=acct.id,
            thread_id=m["thread_id"],
            message_id=m["message_id"],
            from_addr=m["from_addr"],
            to_addrs=m["to_addrs"],
            cc_addrs=m["cc_addrs"],
            date=m["date"],
            subject=m["subject"],
            body_text=m["body_text"],
            body_html=m["body_html"],
            has_attachments=m["has_attachments"],
        )
        db.add(row)
        # Upsert thread
        thr = (
            db.query(EmailThread)
            .filter(EmailThread.thread_id == m["thread_id"])
            .first()
        )
        if not thr:
            thr = EmailThread(
                account_id=acct.id,
                thread_id=m["thread_id"],
                subject=m["subject"],
                latest_from=m["from_addr"],
                latest_snippet=m["snippet"],
                updated_at=m["date"],
            )
            db.add(thr)
        else:
            thr.subject = thr.subject or m["subject"]
            thr.latest_from = m["from_addr"]
            thr.latest_snippet = m["snippet"]
            thr.updated_at = max(thr.updated_at or m["date"], m["date"])
        inserted += 1

    db.commit()

    # Index into Chroma
    _, chunks = index_messages(acct.id, norm_msgs)

    # Update sync state
    state = db.query(SyncState).filter(SyncState.account_id == acct.id).first()
    if not state:
        state = SyncState(
            account_id=acct.id,
            last_synced_at=datetime.utcnow(),
            total_messages=inserted,
        )
        db.add(state)
    else:
        state.last_synced_at = datetime.utcnow()
        state.total_messages = (state.total_messages or 0) + inserted
    db.commit()

    return {"synced": len(norm_msgs), "indexed_chunks": chunks}


@app.post("/chat")
async def chat(payload: Dict[str, Any], db: Session = Depends(get_db)):
    acct = db.query(Account).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No connected account")

    question: str = (payload or {}).get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Missing question")

    top_k: int = int((payload or {}).get("top_k", config.top_k))

    # Run minimal graph synchronously
    state = {"account_id": acct.id, "question": question, "top_k": top_k}
    out = _graph.invoke(state)
    return {"answer": out.get("answer"), "sources": out.get("sources", [])}


@app.get("/chat/stream")
async def chat_stream(
    question: str, top_k: int = config.top_k, db: Session = Depends(get_db)
):
    acct = db.query(Account).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No connected account")

    # Precompute contexts once (we don't stream retrieval)
    q_emb = embed_texts([question])[0]
    res = query_chunks(acct.id, q_emb, top_k=top_k)
    contexts = []
    for i in range(len(res.get("ids", [[]])[0])):
        contexts.append(
            {
                "text": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i],
            }
        )

    async def event_publisher():
        # First send sources
        yield {
            "event": "sources",
            "data": {"sources": [c["metadata"] for c in contexts]},
        }
        # Stream answer tokens from OpenAI directly with the same prompt the graph uses
        system = (
            "You are an email assistant. Answer strictly using the provided email excerpts. "
            "Cite sources by message_id. If unsure, say you don't know."
        )
        context_text = "\n\n".join(
            [
                f"[message_id={c['metadata'].get('message_id')}] {c['text']}"
                for c in contexts
            ]
        )
        prompt = f"Context:\n{context_text}\n\nQuestion: {question}\nAnswer:"
        stream = _client.chat.completions.create(
            model=config.model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=500,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield {"event": "token", "data": {"token": delta}}
        yield {"event": "done", "data": {}}

    return EventSourceResponse(event_publisher())


@app.post("/eval/run")
async def eval_run(db: Session = Depends(get_db)):
    acct = db.query(Account).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No connected account")

    # Build trivial synthetic dataset from existing messages
    msgs = (
        db.query(EmailMessage)
        .filter(EmailMessage.account_id == acct.id)
        .order_by(EmailMessage.date.desc())
        .limit(3)
        .all()
    )
    if not msgs:
        raise HTTPException(status_code=400, detail="No messages to evaluate")

    samples = []
    for m in msgs:
        q = f"What is the subject of the email with message_id={m.message_id}?"
        ref = m.subject or ""
        samples.append({"question": q, "reference": ref})

    def ask_fn(question: str):
        state = {"account_id": acct.id, "question": question, "top_k": config.top_k}
        out = _graph.invoke(state)
        return out.get("answer", ""), out.get("sources", [])

    results = run_eval(samples, ask_fn)
    payload = [r.__dict__ for r in results]
    return {"items": payload}
