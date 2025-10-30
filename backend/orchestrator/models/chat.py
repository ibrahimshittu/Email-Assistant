from __future__ import annotations

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class ChatState(BaseModel):
    """State for chat workflow orchestration"""
    # Input
    account_id: int
    question: str
    top_k: int = 6
    use_hyde: bool = False
    temperature: float = 0.2
    max_tokens: int = 500
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)

    # Processing state
    intent: Optional[Literal["retrieve", "direct", "clarify"]] = None
    hyde_question: Optional[str] = None  # Generated hypothetical document
    raw_contexts: List[Dict[str, Any]] = Field(default_factory=list)
    reranked_contexts: List[Dict[str, Any]] = Field(default_factory=list)

    # Output
    answer: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Flow control
    current_step: str = "classify_intent"
    error: Optional[str] = None
