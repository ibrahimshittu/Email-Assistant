from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database.session import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), nullable=False, index=True)
    nylas_grant_id = Column(String(255), nullable=False, unique=True, index=True)
    access_token = Column(String(512), nullable=False)
    provider = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    threads = relationship("EmailThread", back_populates="account")
    messages = relationship("EmailMessage", back_populates="account")


class EmailThread(Base):
    __tablename__ = "email_threads"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    thread_id = Column(String(255), index=True)
    subject = Column(String(400), nullable=True)
    latest_from = Column(String(400), nullable=True)
    latest_snippet = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)

    account = relationship("Account", back_populates="threads")
    messages = relationship("EmailMessage", back_populates="thread")


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    email_thread_id = Column(Integer, ForeignKey("email_threads.id"), nullable=True, index=True)
    thread_id = Column(String(255), index=True)  # Nylas thread ID
    message_id = Column(String(255), unique=True, index=True)
    from_addr = Column(String(400))
    to_addrs = Column(Text)
    cc_addrs = Column(Text)
    date = Column(DateTime, index=True)
    subject = Column(String(400))
    body_text = Column(Text)
    body_html = Column(Text)
    has_attachments = Column(Boolean, default=False)

    account = relationship("Account", back_populates="messages")
    thread = relationship("EmailThread", back_populates="messages")


class SyncState(Base):
    __tablename__ = "sync_state"

    account_id = Column(Integer, ForeignKey("accounts.id"), primary_key=True)
    last_synced_at = Column(DateTime, nullable=True)
    total_messages = Column(Integer, default=0)


class QAHistory(Base):
    __tablename__ = "qa_history"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    question = Column(Text)
    answer = Column(Text)
    latency_ms = Column(Integer)
    used_hyde = Column(Boolean, default=False)
    top_k = Column(Integer, default=6)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    config_json = Column(Text)


class EvalItem(Base):
    __tablename__ = "eval_items"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("eval_runs.id"), index=True)
    question = Column(Text)
    reference = Column(Text)
    answer = Column(Text)
    faithfulness = Column(Integer)  # 0-1 scaled as int percent
    relevance = Column(Integer)  # 0-1 scaled as int percent
    latency_ms = Column(Integer)
