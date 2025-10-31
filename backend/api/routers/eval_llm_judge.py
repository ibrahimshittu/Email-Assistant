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
        # Extract sender name (email address or display name)
        sender_name = m.from_addr.split('@')[0] if m.from_addr and '@' in m.from_addr else (m.from_addr or "unknown")

        # Question 1: Check for updates from sender
        q1 = f"Do we have any updates from {sender_name}?"
        ref1 = f"Yes, there is an email from {m.from_addr} with subject: {m.subject}"
        samples.append({"question": q1, "reference": ref1})

        # Question 2: What did sender say/send
        q2 = f"What did {sender_name} send about?"
        ref2 = m.subject or "No subject"
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
