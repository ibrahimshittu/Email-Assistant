from __future__ import annotations

from typing import List, Optional, Dict, Any, Literal
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
    """Client request model for chat endpoints"""
    question: str = Field(..., description="User's question about emails", min_length=1)
    top_k: int = Field(6, description="Number of documents to retrieve", ge=1, le=20)
    temperature: float = Field(0.2, description="LLM temperature", ge=0.0, le=2.0)
    max_tokens: int = Field(500, description="Maximum tokens in response", ge=50, le=2000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "What updates do I have today?",
                "top_k": 5,
                "temperature": 0.5,
                "max_tokens": 1000
            }
        }
    }


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


# Pydantic AI structured output models

class EmailAnswer(BaseModel):
    """Structured answer from the email assistant"""
    answer: str = Field(
        ...,
        description="The answer to the user's question based on email contexts"
    )
    confidence: Optional[str] = Field(
        None,
        description="Confidence level: 'high', 'medium', or 'low'"
    )
    cited_message_ids: List[str] = Field(
        default_factory=list,
        description="List of message IDs referenced in the answer"
    )


class IntentRoute(BaseModel):
    """Structured response for intent routing and classification"""
    intent_type: str = Field(
        ...,
        description="Type of intent: 'simple' for greetings/help, 'email_query' for email questions"
    )
    needs_retrieval: bool = Field(
        ...,
        description="Whether RAG retrieval is needed"
    )
    has_sufficient_context: Optional[bool] = Field(
        None,
        description="If contexts provided, whether they're sufficient to answer. None if no contexts."
    )
    route_to: Literal["output", "retrieve", "generate"] = Field(
        ...,
        description="Next action: 'output' (simple response), 'retrieve' (fetch emails), or 'generate' (use existing contexts)"
    )
    reason: str = Field(
        ...,
        description="Brief explanation of the routing decision"
    )
    simple_response: Optional[str] = Field(
        None,
        description="For simple intents (greetings, help), provide direct response here"
    )
