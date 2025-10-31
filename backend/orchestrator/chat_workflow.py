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
        contexts=None
    )

    # Store simple response if provided
    if routing_decision["simple_response"]:
        state.metadata["simple_response"] = routing_decision["simple_response"]

    # Set next step
    state.current_step = routing_decision["route_to"]

    # Track timing
    clarify_time = (perf_counter() - start_time) * 1000
    state.metadata["clarify_intent_ms"] = round(clarify_time)

    return state


def retrieve(state: ChatState) -> ChatState:
    """Retrieve relevant email contexts using vector similarity"""
    start_time = perf_counter()

    query_text = state.question

    try:
        # Embed query
        q_emb = embed_texts([query_text])[0]

        # Retrieve from vector store
        # Fetch more than top_k for potential reranking
        fetch_k = state.top_k * 2
        res = query_chunks(state.account_id, q_emb, top_k=fetch_k)

        # Parse results
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

    # Route based on result count
    state.current_step = "rerank" if len(state.raw_contexts) > state.top_k else "generate"

    return state


def rerank(state: ChatState) -> ChatState:
    """Lightweight reranking of retrieved contexts"""
    start_time = perf_counter()

    # Simple reranking: take top_k by distance (already sorted)
    state.reranked_contexts = state.raw_contexts[:state.top_k]

    rerank_time = (perf_counter() - start_time) * 1000
    state.metadata["rerank_ms"] = round(rerank_time)

    return state


def output(state: ChatState) -> ChatState:
    """
    Output simple responses without LLM generation.

    Used for:
    1. Simple greetings/help messages (from initial routing)
    2. Error messages when contexts are insufficient (set by clarify_intent)
    """
    start_time = perf_counter()

    # Priority order for answer:
    # 1. Answer already set by clarify_intent (for insufficient contexts)
    # 2. Simple response from metadata (for greetings/help)
    # 3. Default fallback message
    if state.answer is None:
        if "simple_response" in state.metadata:
            state.answer = state.metadata["simple_response"]
        else:
            state.answer = "I'm here to help you with your emails. What would you like to know?"

    state.sources = []

    output_time = (perf_counter() - start_time) * 1000
    state.metadata["output_ms"] = round(output_time)

    state.current_step = "finalize"
    return state


def generate(state: ChatState) -> ChatState:
    """
    Generate answer using the ChatAgent with retrieved email contexts.

    Only called for email queries with sufficient contexts.
    """
    start_time = perf_counter()

    try:
        # Use retrieved contexts (reranked if available)
        contexts = state.reranked_contexts if state.reranked_contexts else state.raw_contexts

        state.answer = _chat_agent.generate_answer(
            question=state.question,
            contexts=contexts,
            conversation_history=state.conversation_history,
            temperature=state.temperature,
            max_tokens=state.max_tokens
        )

        # Include the full text content in sources for user to see
        state.sources = []
        for ctx in contexts:
            meta = ctx.get("metadata", {}).copy()
            meta["text"] = ctx.get("text", "")
            state.sources.append(meta)

        generation_time = (perf_counter() - start_time) * 1000
        state.metadata["generation_ms"] = round(generation_time)

    except Exception as e:
        state.error = f"Generation failed: {e}"
        state.answer = f"Sorry, I encountered an error while generating the answer: {e}"

    state.current_step = "finalize"
    return state


def finalize(state: ChatState) -> ChatState:
    """Finalize the response and add metadata"""
    # Calculate total latency
    total_time = sum([
        state.metadata.get("clarify_intent_ms", 0),
        state.metadata.get("retrieve_ms", 0),
        state.metadata.get("rerank_ms", 0),
        state.metadata.get("output_ms", 0),
        state.metadata.get("generation_ms", 0)
    ])
    state.metadata["latency_ms"] = total_time
    state.metadata["top_k"] = state.top_k
    state.current_step = "done"
    return state


def route_after_clarify_intent(state: ChatState) -> Literal["retrieve", "output"]:
    """Route based on LLM decision: simple -> output, email query -> retrieve"""
    return state.current_step


def route_after_retrieve(state: ChatState) -> Literal["rerank", "generate"]:
    """Rerank if many results, otherwise generate directly"""
    return "rerank" if len(state.raw_contexts) > state.top_k else "generate"


def build_chat_workflow() -> StateGraph:
    """
    Build the chat workflow with single LLM intent router at entry.

    Flow:
      clarify_intent → [output | retrieve → [rerank] → generate] → finalize

    Routes:
    - Simple questions → output
    - Email queries → retrieve → generate (with optional reranking)
    """
    graph = StateGraph(ChatState)

    # Add nodes
    graph.add_node("clarify_intent", clarify_intent)
    graph.add_node("output", output)
    graph.add_node("retrieve", retrieve)
    graph.add_node("rerank", rerank)
    graph.add_node("generate", generate)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("clarify_intent")

    # Routing
    graph.add_conditional_edges(
        "clarify_intent",
        route_after_clarify_intent,
        {"retrieve": "retrieve", "output": "output"}
    )

    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {"rerank": "rerank", "generate": "generate"}
    )

    graph.add_edge("rerank", "generate")
    graph.add_edge("output", "finalize")
    graph.add_edge("generate", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=_checkpointer)


# Export the checkpointer for external use
def get_checkpointer():
    """Get the workflow checkpointer for managing conversation state"""
    return _checkpointer
