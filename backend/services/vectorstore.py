from __future__ import annotations

from typing import List, Dict, Any
from pathlib import Path

import chromadb
from chromadb.config import Settings

from config import load_config


config = load_config()
Path(config.chroma_dir).mkdir(parents=True, exist_ok=True)


def get_client() -> chromadb.Client:
    return chromadb.PersistentClient(
        path=config.chroma_dir, settings=Settings(anonymized_telemetry=False)
    )


def collection_name_for_account(account_id: int) -> str:
    return f"emails_{account_id}"


def get_or_create_collection(account_id: int):
    client = get_client()
    name = collection_name_for_account(account_id)
    try:
        col = client.get_collection(name)
    except Exception:
        col = client.create_collection(name)
    return col


def upsert_chunks(
    account_id: int,
    chunk_ids: List[str],
    texts: List[str],
    metadatas: List[Dict[str, Any]],
    embeddings: List[List[float]] | None = None,
):
    col = get_or_create_collection(account_id)
    col.upsert(
        ids=chunk_ids, documents=texts, metadatas=metadatas, embeddings=embeddings
    )


def query_chunks(
    account_id: int, query_embedding: List[float], top_k: int = 6
) -> Dict[str, Any]:
    col = get_or_create_collection(account_id)
    res = col.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    return res
