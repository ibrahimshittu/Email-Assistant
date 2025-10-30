from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import load_config
from database import SessionLocal, Account, EmailMessage
from services import run_eval
from orchestrator import build_chat_workflow, ChatState


router = APIRouter()
config = load_config()
_workflow = build_chat_workflow()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/eval/run")
async def eval_run(db: Session = Depends(get_db)):
    """
    Run evaluation on synthetic Q&A dataset
    """
    acct = db.query(Account).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No connected account")

    # Build trivial synthetic dataset from existing messages
    msgs = (
        db.query(EmailMessage)
        .filter(EmailMessage.account_id == acct.id)
        .order_by(EmailMessage.date.desc())
        .limit(5)
        .all()
    )

    if not msgs:
        raise HTTPException(status_code=400, detail="No messages to evaluate")

    # Generate sample questions
    samples = []
    for m in msgs:
        # Question 1: Subject query
        q1 = f"What is the subject of the email with message_id={m.message_id}?"
        ref1 = m.subject or ""
        samples.append({"question": q1, "reference": ref1})

        # Question 2: Sender query
        q2 = f"Who sent the email with subject '{m.subject}'?"
        ref2 = m.from_addr or ""
        samples.append({"question": q2, "reference": ref2})

    def ask_fn(question: str):
        """Execute workflow for each question"""
        state = ChatState(
            account_id=acct.id,
            question=question,
            top_k=config.top_k
        )
        result = _workflow.invoke(state)
        return result.answer or "", result.sources or []

    # Run evaluation
    results = run_eval(samples, ask_fn)

    # Format results
    payload = [r.__dict__ if hasattr(r, '__dict__') else r for r in results]

    return {"items": payload, "total": len(payload)}
