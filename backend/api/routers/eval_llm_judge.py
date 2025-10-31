"""LLM-as-a-Judge evaluation endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, Account, EmailMessage
from orchestrator import build_chat_workflow, ChatState
from services.eval import run_eval
from config import load_config

router = APIRouter()
config = load_config()


@router.post("/eval/llm-judge")
async def eval_llm_judge_run(db: Session = Depends(get_db)):
    """
    Run LLM-as-a-Judge evaluation with binary metrics:
    - Faithfulness (0 or 1)
    - Relevance (0 or 1)
    """
    # Get first connected account
    acct = db.query(Account).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No connected account")

    # Build evaluation dataset from existing messages
    msgs = (
        db.query(EmailMessage)
        .filter(EmailMessage.account_id == acct.id)
        .order_by(EmailMessage.date.desc())
        .limit(1)
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

    async def ask_fn(question: str):
        """Execute workflow for each question"""
        workflow = build_chat_workflow()
        state = ChatState(
            account_id=acct.id,
            question=question,
            top_k=config.top_k
        )
        workflow_config = {"configurable": {"thread_id": f"eval-{acct.id}"}}
        result = await workflow.ainvoke(state, config=workflow_config)
        return result.get("answer") or "", result.get("sources") or []

    # Run LLM Judge evaluation
    results = await run_eval(samples, ask_fn)
    payload = [r.__dict__ if hasattr(r, '__dict__') else r for r in results]
    
    return {
        "evaluation_type": "llm_judge",
        "items": payload,
        "total": len(payload)
    }
