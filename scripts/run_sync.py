#!/usr/bin/env python3
"""
CLI script to sync emails from Nylas for the connected account
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir.parent))

from backend.config import load_config
from backend.database import SessionLocal
from backend.database import Account, EmailMessage, EmailThread, SyncState
from backend.services.nylas_client import NylasClient
from backend.services.ingest import normalize_message, index_messages
from backend.utils.logger import setup_logger


logger = setup_logger(__name__)


def main():
    """Sync emails from Nylas"""
    logger.info("=" * 60)
    logger.info("Email Sync Script")
    logger.info("=" * 60)

    config = load_config()
    nylas = NylasClient()
    db = SessionLocal()

    try:
        # Get connected account
        acct = db.query(Account).first()
        if not acct:
            logger.error("No connected account found")
            logger.error("Please connect an account first via the web UI")
            return 1

        logger.info(f"Syncing emails for account: {acct.email}")
        logger.info("Fetching last 200 messages from Nylas...")

        # Fetch messages
        messages = nylas.fetch_last_messages(acct.access_token, limit=200)
        logger.info(f"Fetched {len(messages)} messages from Nylas")

        # Normalize
        norm_msgs = [normalize_message(m) for m in messages]

        # Persist to database
        inserted = 0
        updated_threads = 0

        for m in norm_msgs:
            # Check if message exists
            existing = (
                db.query(EmailMessage)
                .filter(EmailMessage.message_id == m["message_id"])
                .first()
            )

            if existing:
                continue

            # Insert message
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
                updated_threads += 1

            inserted += 1

        db.commit()
        logger.info(f"Inserted {inserted} new messages")
        logger.info(f"Updated {updated_threads} threads")

        # Index into Chroma
        logger.info("Indexing messages into vector store...")
        _, chunks = index_messages(acct.id, norm_msgs)
        logger.info(f"Indexed {chunks} chunks into Chroma")

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

        logger.info("=" * 60)
        logger.info("Sync complete!")
        logger.info(f"Total messages in database: {state.total_messages}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
