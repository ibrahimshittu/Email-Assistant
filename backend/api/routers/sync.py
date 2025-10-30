from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal, Account, EmailMessage, EmailThread, SyncState
from services import NylasClient, normalize_message, index_messages


router = APIRouter()
nylas = NylasClient()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/sync/latest")
async def sync_latest(db: Session = Depends(get_db)):
    acct = db.query(Account).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No connected account")

    messages = nylas.fetch_last_messages(acct.nylas_grant_id, limit=200)
    norm_msgs = [normalize_message(m) for m in messages]

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

    _, chunks = index_messages(acct.id, norm_msgs)

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
