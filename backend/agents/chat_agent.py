from __future__ import annotations

from typing import List, Dict, Any
from time import perf_counter
from datetime import datetime

from pydantic_ai import Agent
from openai import OpenAI

from config import load_config
from services.ingest import embed_texts
from services.vectorstore import query_chunks
from utils.template_loader import render_template
from agents.models.chat import ChatRequest, ChatResponse, Source


config = load_config()
_openai_client = OpenAI(api_key=config.openai_api_key)


def format_contexts(contexts: List[Dict[str, Any]]) -> str:
    """Format retrieved contexts for prompt inclusion"""
    parts: List[str] = []
    for c in contexts:
        meta = c.get("metadata", {})
        parts.append(f"[message_id={meta.get('message_id')}] {c.get('text','')}")
    return "\n\n".join(parts)


def retrieve_contexts(
    account_id: int, question: str, top_k: int
) -> List[Dict[str, Any]]:
    """Retrieve relevant email contexts using vector similarity"""
    q_emb = embed_texts([question])[0]
    res = query_chunks(account_id, q_emb, top_k=top_k)
    docs: List[Dict[str, Any]] = []
    for i in range(len(res.get("ids", [[]])[0])):
        docs.append(
            {
                "text": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i],
            }
        )
    return docs


def contexts_to_sources(contexts: List[Dict[str, Any]]) -> List[Source]:
    """Convert raw contexts to Source models"""
    sources = []
    for ctx in contexts:
        meta = ctx.get("metadata", {})
        # Parse date if it's a string
        date_val = meta.get("date")
        if isinstance(date_val, str):
            try:
                date_val = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
            except:
                date_val = None

        sources.append(
            Source(
                message_id=meta.get("message_id", ""),
                subject=meta.get("subject"),
                from_addr=meta.get("from"),
                date=date_val,
                distance=ctx.get("distance"),
                snippet=ctx.get("text", "")[:200] if ctx.get("text") else None,
            )
        )
    return sources


class ChatAgent:
    """Main chat agent using Pydantic AI for structured interaction with emails"""

    def __init__(self) -> None:
        system = render_template("chat/system_prompt.j2")
        # PydanticAI agent for structured responses
        self.agent = Agent(model=f"openai:{config.model_name}", system_prompt=system)

    def run(self, request: ChatRequest) -> ChatResponse:
        """
        Execute chat request and return structured response

        Args:
            request: ChatRequest with question, account_id, and options

        Returns:
            ChatResponse with answer, sources, and metadata
        """
        start_time = perf_counter()

        # Retrieve contexts
        retrieve_start = perf_counter()
        contexts = retrieve_contexts(
            request.account_id, request.question, request.top_k
        )
        retrieve_time = (perf_counter() - retrieve_start) * 1000

        # Format contexts for prompt
        context_text = format_contexts(contexts)
        prompt = render_template(
            "chat/user_prompt.j2", context_text=context_text, question=request.question
        )

        # Run agent with PydanticAI
        generation_start = perf_counter()
        result = self.agent.run_sync(prompt)
        generation_time = (perf_counter() - generation_start) * 1000

        # Extract answer from result
        answer = (
            getattr(result, "data", None)
            or getattr(result, "output", None)
            or str(result)
        )

        total_time = (perf_counter() - start_time) * 1000

        # Convert contexts to sources
        sources = contexts_to_sources(contexts)

        return ChatResponse(
            answer=answer,
            sources=sources,
            metadata={
                "latency_ms": round(total_time),
                "retrieve_ms": round(retrieve_time),
                "generation_ms": round(generation_time),
                "top_k": request.top_k,
                "use_hyde": request.use_hyde,
                "temperature": request.temperature,
            },
        )

    def run_legacy(
        self, account_id: int, question: str, top_k: int = None
    ) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        if top_k is None:
            top_k = config.top_k

        request = ChatRequest(account_id=account_id, question=question, top_k=top_k)
        response = self.run(request)

        # Convert to legacy format
        return {
            "answer": response.answer,
            "sources": [s.model_dump(exclude_none=True) for s in response.sources],
            "metadata": response.metadata,
        }
