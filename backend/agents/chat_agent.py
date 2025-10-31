from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
import tiktoken

from config import load_config
from utils.template_loader import render_template
from agents.models.chat import EmailAnswer, IntentRoute


config = load_config()


def trim_conversation_history(messages: List[ModelMessage]) -> List[ModelMessage]:
    """
    Trim messages based on token count to prevent exceeding context limits.
    Keeps the most recent messages within a 2000 token budget.
    """
    if not messages:
        return messages

    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    max_tokens = 2000
    total_tokens = 0
    trimmed_messages = []

    for message in reversed(messages):
        message_str = str(message)
        message_tokens = len(encoding.encode(message_str))

        if total_tokens + message_tokens > max_tokens:
            break

        total_tokens += message_tokens
        trimmed_messages.insert(0, message)

    return trimmed_messages if trimmed_messages else messages[-1:]


class ChatAgent:
    """
    Chat agent responsible for LLM generation only using Pydantic AI.

    The workflow handles retrieval, reranking, etc.
    This agent only generates answers from provided contexts.
    """

    def __init__(self) -> None:
        self.config = config

        system_prompt = render_template("chat/email_assistant_system.j2")
        self.answer_agent = Agent(
            model=f"openai:{config.answer_model}",
            system_prompt=system_prompt,
            output_type=EmailAnswer,
            history_processors=[trim_conversation_history],
        )

        self.intent_router_agent = Agent(
            model=f"openai:{config.intent_router_model}",
            output_type=IntentRoute,
        )

    async def generate_answer(
        self,
        question: str,
        contexts: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate an answer using the LLM based on retrieved contexts.

        Args:
            question: User's question
            contexts: List of retrieved email contexts with 'text' and 'metadata'
            conversation_history: Optional conversation history for multi-turn chat
            temperature: LLM temperature (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens in response

        Returns:
            Generated answer as string
        """
        context_parts = []
        for ctx in contexts:
            meta = ctx.get("metadata", {})
            text = ctx.get("text", "")
            message_id = meta.get("message_id", "unknown")
            subject = meta.get("subject", "")
            from_addr = meta.get("from_addr", "")

            context_parts.append(
                f"[message_id={message_id} | from={from_addr} | subject={subject}]\n{text}"
            )

        context_text = "\n\n".join(context_parts)

        today = datetime.now().strftime("%B %d, %Y")
        user_prompt = render_template(
            "chat/email_question_prompt.j2",
            context_text=context_text,
            question=question,
            today=today
        )

        result = await self.answer_agent.run(
            user_prompt,
            message_history=conversation_history or [],
            model_settings={
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )

        email_answer: EmailAnswer = result.output
        return email_answer.answer

    async def clarify_and_route(
        self,
        question: str,
        contexts: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 2000,
    ) -> IntentRoute:
        """
        Clarify intent and route to appropriate action using a single LLM call.

        This method serves as an intelligent router that:
        1. Classifies simple questions (greetings, help) -> output directly
        2. Identifies email queries without contexts -> retrieve
        3. Evaluates sufficiency of provided contexts -> generate or output error

        Args:
            question: User's question
            contexts: Optional retrieved contexts with metadata and distance scores

        Returns:
            IntentRoute with routing decision containing:
            - intent_type: 'simple' or 'email_query'
            - needs_retrieval: bool
            - has_sufficient_context: Optional[bool]
            - route_to: 'output', 'retrieve', or 'generate'
            - reason: explanation
            - simple_response: Optional direct response for simple intents
        """
        today = datetime.now().strftime("%B %d, %Y")
        intent_prompt = render_template(
            "chat/intent_routing_prompt.j2",
            question=question,
            contexts=contexts or [],
            today=today
        )

        result = await self.intent_router_agent.run(
            intent_prompt,
            model_settings={
                "temperature": 0.0,
                "max_tokens": max_tokens
            }
        )
        return result.output
