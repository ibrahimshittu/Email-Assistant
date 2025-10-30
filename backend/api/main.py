from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import load_config
from ..database import Base, engine
from .routers import auth, sync, chat, eval as eval_router


config = load_config()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Email Assistant RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        config.frontend_base_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
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
app.include_router(eval_router.router, tags=["eval"])
