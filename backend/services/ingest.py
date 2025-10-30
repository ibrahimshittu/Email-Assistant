from __future__ import annotations

from typing import List, Dict, Any, Tuple
from datetime import datetime
import hashlib

from openai import OpenAI

from .config import load_config
from .utils.text import html_to_text, strip_quotes_and_signature, normalize_text
from .services.vectorstore import upsert_chunks


config = load_config()
_client = OpenAI(api_key=config.openai_api_key)


def _hash_id(*parts: str) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update(p.encode("utf-8"))
    return h.hexdigest()


def normalize_message(nylas_msg: Dict[str, Any]) -> Dict[str, Any]:
    body_html = nylas_msg.get("body") or ""
    body_text = html_to_text(body_html)
    body_text = strip_quotes_and_signature(body_text)
    body_text = normalize_text(body_text)

    return {
        "message_id": str(nylas_msg.get("id")),
        "thread_id": str(nylas_msg.get("thread_id")),
        "from_addr": (nylas_msg.get("from") or [{}])[0].get("email", ""),
        "to_addrs": ", ".join(
            [x.get("email", "") for x in (nylas_msg.get("to") or [])]
        ),
        "cc_addrs": ", ".join(
            [x.get("email", "") for x in (nylas_msg.get("cc") or [])]
        ),
        "date": datetime.fromtimestamp(nylas_msg.get("received_at", 0)),
        "subject": nylas_msg.get("subject") or "",
        "body_text": body_text,
        "body_html": body_html,
        "has_attachments": bool(nylas_msg.get("has_attachments")),
        "snippet": nylas_msg.get("snippet") or "",
    }


def chunk_text(text: str, max_tokens: int = 800, overlap: int = 200) -> List[str]:
    # Simple char-based chunking as placeholder; can be replaced with token-aware
    if not text:
        return []
    max_chars = max_tokens * 4
    overlap_chars = overlap * 4
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        if end == len(text):
            break
        start = end - overlap_chars
        if start < 0:
            start = 0
    return chunks


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    resp = _client.embeddings.create(model=config.embedding_model, input=texts)
    return [d.embedding for d in resp.data]


def index_messages(
    account_id: int, normalized_messages: List[Dict[str, Any]]
) -> Tuple[int, int]:
    chunk_ids: List[str] = []
    texts: List[str] = []
    metas: List[Dict[str, Any]] = []

    for m in normalized_messages:
        chunks = chunk_text(m["body_text"]) or ([m["subject"]] if m["subject"] else [])
        for idx, ch in enumerate(chunks):
            cid = _hash_id(str(account_id), m["message_id"], str(idx))
            chunk_ids.append(cid)
            texts.append(ch)
            metas.append(
                {
                    "message_id": m["message_id"],
                    "thread_id": m["thread_id"],
                    "subject": m["subject"],
                    "from_addr": m["from_addr"],
                    "date": m["date"].isoformat(),
                    "chunk_index": idx,
                }
            )

    embeddings = embed_texts(texts) if texts else []
    if texts:
        upsert_chunks(account_id, chunk_ids, texts, metas, embeddings)
    return (len(normalized_messages), len(texts))
