from __future__ import annotations

from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec

from config import load_config


config = load_config()

# Initialize Pinecone client
_pc_client = None


def get_client() -> Pinecone:
    """Get or create Pinecone client instance."""
    global _pc_client
    if _pc_client is None:
        _pc_client = Pinecone(api_key=config.pinecone_api_key)
    return _pc_client


def index_name_for_account(account_id: int) -> str:
    """Generate Pinecone index name for a specific account."""
    return f"{config.pinecone_index_prefix}-{account_id}"


def get_or_create_index(account_id: int):
    """
    Get or create a Pinecone index for the given account.

    Note: Pinecone indexes are created with a specific dimension size.
    For OpenAI's text-embedding-3-small, the dimension is 1536.
    """
    pc = get_client()
    index_name = index_name_for_account(account_id)

    # Check if index exists
    existing_indexes = pc.list_indexes()
    index_exists = any(idx.name == index_name for idx in existing_indexes)

    if not index_exists:
        # Create serverless index
        # Dimension 1536 for text-embedding-3-small
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=config.pinecone_environment
            )
        )

    return pc.Index(index_name)


def upsert_chunks(
    account_id: int,
    chunk_ids: List[str],
    texts: List[str],
    metadatas: List[Dict[str, Any]],
    embeddings: List[List[float]] | None = None,
):
    """
    Upsert chunks into Pinecone index.

    Args:
        account_id: Account identifier
        chunk_ids: List of unique IDs for each chunk
        texts: List of text documents (stored in metadata)
        metadatas: List of metadata dictionaries
        embeddings: List of embedding vectors (required for Pinecone)
    """
    if embeddings is None:
        raise ValueError("Embeddings are required for Pinecone upserts")

    index = get_or_create_index(account_id)

    # Prepare vectors for upsert
    # Pinecone format: (id, vector, metadata)
    vectors = []
    for i, (chunk_id, embedding, text, metadata) in enumerate(
        zip(chunk_ids, embeddings, texts, metadatas)
    ):
        # Add text to metadata so we can retrieve it later
        metadata_with_text = {**metadata, "text": text}
        vectors.append((chunk_id, embedding, metadata_with_text))

    # Upsert in batches of 100 (Pinecone recommended batch size)
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)


def query_chunks(
    account_id: int, query_embedding: List[float], top_k: int = 6
) -> Dict[str, Any]:
    """
    Query Pinecone index for similar chunks.

    Returns a dictionary compatible with ChromaDB's query response format:
    {
        'ids': [[...]],
        'documents': [[...]],
        'metadatas': [[...]],
        'distances': [[...]]
    }
    """
    index = get_or_create_index(account_id)

    # Query Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        include_values=False
    )

    ids = []
    documents = []
    metadatas = []
    distances = []

    for match in results.matches:
        ids.append(match.id)
        # Extract text from metadata
        metadata = dict(match.metadata)
        text = metadata.pop("text", "")
        documents.append(text)
        metadatas.append(metadata)
        # Pinecone returns similarity scores (higher is better)
        # Convert to distance (lower is better) for consistency
        distances.append(1.0 - match.score)

    return {
        "ids": [ids],
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances]
    }
