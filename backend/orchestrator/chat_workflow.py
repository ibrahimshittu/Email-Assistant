from __future__ import annotations

from typing import Literal
from time import perf_counter

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from config import load_config
from services.ingest import embed_texts
from services.vectorstore import query_chunks
from orchestrator.models.chat import ChatState
from agents.chat_agent import ChatAgent


config = load_config()
_chat_agent = ChatAgent()
_checkpointer = MemorySaver()  # In-memory checkpointing


async def clarify_intent(state: ChatState) -> ChatState:
    """
    LLM-based intent router called once at workflow entry.
    Routes simple questions to output, email queries to retrieve.
    """
    start_time = perf_counter()

    routing_decision = await _chat_agent.clarify_and_route(
        question=state.question,
        contexts=state.raw_contexts,
        max_tokens=state.max_tokens
    )

    if routing_decision.simple_response:
        state.answer = routing_decision.simple_response

    state.current_step = routing_decision.route_to

    clarify_time = (perf_counter() - start_time) * 1000
    state.metadata["clarify_intent_ms"] = round(clarify_time)

    return state


def retrieve(state: ChatState) -> ChatState:
    """Retrieve relevant email contexts using vector similarity"""
    start_time = perf_counter()

    query_text = state.question.lower()

    try:
        q_emb = embed_texts([query_text])[0]
        res = query_chunks(state.account_id, q_emb, top_k=state.top_k)

        contexts = []
        for i in range(len(res.get("ids", [[]])[0])):
            contexts.append({
                "text": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i],
            })

        state.raw_contexts = contexts
        retrieve_time = (perf_counter() - start_time) * 1000
        state.metadata["retrieve_ms"] = round(retrieve_time)

    except Exception as e:
        state.error = f"Retrieval failed: {e}"
        state.raw_contexts = []

    return state


def output(state: ChatState) -> ChatState:
    """Output final responses - ensures all paths have proper answer and sources"""
    if state.answer is None:
        state.answer = "I'm here to help you with your emails. What would you like to know?"

    return state


async def generate(state: ChatState) -> ChatState:
    """Generate answer using retrieved email contexts"""
    start_time = perf_counter()

    try:
        state.answer = await _chat_agent.generate_answer(
            question=state.question,
            contexts=state.raw_contexts,
            conversation_history=state.conversation_history,
            temperature=state.temperature,
            max_tokens=state.max_tokens
        )

        state.sources = []
        for ctx in state.raw_contexts:
            meta = ctx.get("metadata", {}).copy()
            meta["text"] = ctx.get("text", "")
            state.sources.append(meta)

        generation_time = (perf_counter() - start_time) * 1000
        state.metadata["generation_ms"] = round(generation_time)

    except Exception as e:
        state.error = f"Generation failed: {e}"
        state.answer = f"Sorry, I encountered an error while generating the answer: {e}"

    return state


def route_after_clarify_intent(state: ChatState) -> Literal["retrieve", "output"]:
    """Route based on LLM decision: simple -> output, email query -> retrieve"""
    return state.current_step




def build_chat_workflow() -> StateGraph:
    """
    Build the chat workflow with single LLM intent router at entry.

    Flow:
      clarify_intent → [output → END | retrieve → generate → output → END]

    Routes:
    - Simple questions → output → END
    - Email queries → retrieve → generate → output → END
    """
    graph = StateGraph(ChatState)

    graph.add_node("clarify_intent", clarify_intent)
    graph.add_node("output", output)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)

    graph.set_entry_point("clarify_intent")

    graph.add_conditional_edges(
        "clarify_intent",
        route_after_clarify_intent,
        {"retrieve": "retrieve", "output": "output"}
    )

    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "output")
    graph.add_edge("output", END)

    return graph.compile(checkpointer=_checkpointer)


# Export the checkpointer for external use
def get_checkpointer():
    """Get the workflow checkpointer for managing conversation state"""
    return _checkpointer
