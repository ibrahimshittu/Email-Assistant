from __future__ import annotations

import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv


class AppConfig(BaseModel):
    openai_api_key: str
    nylas_client_id: str
    nylas_client_secret: str
    nylas_api_uri: str = "https://api.us.nylas.com"
    frontend_base_url: str = "http://localhost:3000"
    backend_base_url: str = "http://localhost:8000"
    chroma_dir: str = "./storage/chroma"
    sqlite_path: str = "./storage/app.db"

    model_name: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    top_k: int = 6


def load_config() -> AppConfig:
    env_path = Path(".env")
    load_dotenv(env_path)  # loads if exists; no-op otherwise

    return AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        nylas_client_id=os.getenv("NYLAS_CLIENT_ID", ""),
        nylas_client_secret=os.getenv("NYLAS_CLIENT_SECRET", ""),
        nylas_api_uri=os.getenv("NYLAS_API_URI", "https://api.us.nylas.com"),
        frontend_base_url=os.getenv("FRONTEND_BASE_URL", "http://localhost:3000"),
        backend_base_url=os.getenv("BACKEND_BASE_URL", "http://localhost:8000"),
        chroma_dir=os.getenv("CHROMA_DIR", "./storage/chroma"),
        sqlite_path=os.getenv("SQLITE_PATH", "./storage/app.db"),
        model_name=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        top_k=int(os.getenv("TOP_K", 6)),
    )
