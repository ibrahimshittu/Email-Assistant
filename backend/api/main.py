from __future__ import annotations

import os

# Disable ChromaDB telemetry completely to avoid version compatibility issues
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPL"] = "None"
os.environ["POSTHOG_DISABLED"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import load_config
from database import Base, engine
from api.routers import auth, sync, chat, eval_deepeval, eval_llm_judge


config = load_config()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Email Assistant RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        config.frontend_base_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


# Routers
app.include_router(auth.router, tags=["auth"])
app.include_router(sync.router, tags=["sync"])
app.include_router(chat.router, tags=["chat"])
app.include_router(eval_deepeval.router, tags=["eval"])
app.include_router(eval_llm_judge.router, tags=["eval"])
