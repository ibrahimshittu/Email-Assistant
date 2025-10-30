from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Source(BaseModel):
    """Represents a source email for citation"""
    message_id: str = Field(..., description="Unique message identifier")
    subject: Optional[str] = Field(None, description="Email subject")
    from_addr: Optional[str] = Field(None, description="Sender email address")
    date: Optional[datetime] = Field(None, description="Email date")
    distance: Optional[float] = Field(None, description="Embedding similarity distance")
    snippet: Optional[str] = Field(None, description="Short snippet from email")


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str = Field(..., description="User's question about emails", min_length=1)
    account_id: int = Field(..., description="Account ID for the user")
    top_k: int = Field(6, description="Number of documents to retrieve", ge=1, le=20)
    use_hyde: bool = Field(False, description="Whether to use HyDE for retrieval")
    temperature: float = Field(0.2, description="LLM temperature", ge=0.0, le=2.0)
    max_tokens: int = Field(500, description="Maximum tokens in response", ge=50, le=2000)
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )


class ChatResponse(BaseModel):
    """Response model from chat agent"""
    answer: str = Field(..., description="Generated answer to the question")
    sources: List[Source] = Field(
        default_factory=list,
        description="Source emails used for answer"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (latency, tokens used, etc.)"
    )
