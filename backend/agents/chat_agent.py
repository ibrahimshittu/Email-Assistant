from __future__ import annotations

from typing import List, Dict, Any, Optional

from pydantic_ai import Agent

from config import load_config
from utils.template_loader import render_template
from agents.models.chat import EmailAnswer, IntentRoute


config = load_config()


class ChatAgent:
    """
    Chat agent responsible for LLM generation only using Pydantic AI.

    The workflow handles retrieval, reranking, etc.
    This agent only generates answers from provided contexts.
    """

    def __init__(self) -> None:
        self.config = config

        # Create Pydantic AI agent for answer generation with structured output
        system_prompt = render_template("chat/email_assistant_system.j2")
        self.answer_agent = Agent(
            model=f"openai:{config.model_name}",
            system_prompt=system_prompt,
            result_type=EmailAnswer,
        )

        # Create Pydantic AI agent for intent routing
        self.intent_router_agent = Agent(
            model=f"openai:{config.model_name}",
            result_type=IntentRoute,
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

        user_prompt = render_template(
            "chat/email_question_prompt.j2",
            context_text=context_text,
            question=question
        )

        message_history = []
        if conversation_history:
            message_history = conversation_history[-4:]

        result = await self.answer_agent.run(
            user_prompt,
            message_history=message_history,
            model_settings={
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )

        email_answer: EmailAnswer = result.data
        return email_answer.answer

    async def clarify_and_route(
        self,
        question: str,
        contexts: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
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
            Dict with routing decision containing:
            - intent_type: 'simple' or 'email_query'
            - needs_retrieval: bool
            - has_sufficient_context: Optional[bool]
            - route_to: 'output', 'retrieve', or 'generate'
            - reason: explanation
            - simple_response: Optional direct response for simple intents
        """
        intent_prompt = render_template(
            "chat/intent_routing_prompt.j2",
            question=question,
            contexts=contexts or []
        )

        result = await self.intent_router_agent.run(
            intent_prompt,
            model_settings={
                "temperature": 0.0,
                "max_tokens": 200,
            }
        )

        route: IntentRoute = result.data

        return {
            "intent_type": route.intent_type,
            "needs_retrieval": route.needs_retrieval,
            "has_sufficient_context": route.has_sufficient_context,
            "route_to": route.route_to,
            "reason": route.reason,
            "simple_response": route.simple_response,
        }
