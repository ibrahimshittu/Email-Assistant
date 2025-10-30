from __future__ import annotations

import os
from pathlib import Path
from pydantic import BaseModel, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


class AppConfig(BaseSettings):
    # Core keys
    openai_api_key: str = ""
    nylas_client_id: str = ""
    nylas_client_secret: str = ""

    # URLs
    nylas_api_uri: str = "https://api.us.nylas.com"
    frontend_base_url: str = "http://localhost:3000"
    backend_base_url: str = "http://localhost:8000"

    # Storage paths
    chroma_dir: str = "./storage/chroma"
    sqlite_path: str = "./storage/app.db"

    # Models/knobs
    model_name: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    top_k: int = 6

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=('settings_',)  # Fix Pydantic warning
    )

    @field_validator("backend_base_url", mode="before")
    @classmethod
    def normalize_backend_url(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            return "http://localhost:8000"
        return v.rstrip("/")

    @field_validator("frontend_base_url", "nylas_api_uri", mode="before")
    @classmethod
    def normalize_urls(cls, v: str) -> str:
        v = (v or "").strip()
        return v.rstrip("/") if v else v


def load_config() -> AppConfig:
    # Ensure .env is respected for non-Settings consumers too
    load_dotenv(Path(".env"))
    return AppConfig()
