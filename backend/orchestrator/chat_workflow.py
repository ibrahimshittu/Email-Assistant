from __future__ import annotations

from typing import Dict, Any, Literal
from time import perf_counter

from langgraph.graph import StateGraph, END
from openai import OpenAI

from config import load_config
from services.ingest import embed_texts
from services.vectorstore import query_chunks
from orchestrator.models.chat import ChatState


config = load_config()
_client = OpenAI(api_key=config.openai_api_key)


def classify_intent(state: ChatState) -> ChatState:
    """Classify user intent to determine retrieval strategy"""
    question = state.question.lower()

    # Simple heuristic classification
    if len(question) < 5:
        state.intent = "clarify"
    elif any(word in question for word in ["who", "what", "when", "where", "find", "search", "show", "list"]):
        state.intent = "retrieve"
    else:
        state.intent = "retrieve"  # Default to retrieval for most questions

    state.current_step = "retrieve" if state.intent == "retrieve" else "generate"
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

    state.current_step = "rerank" if len(state.raw_contexts) > state.top_k else "generate"
    return state


def rerank(state: ChatState) -> ChatState:
    """Lightweight reranking of retrieved contexts"""
    if len(state.raw_contexts) <= state.top_k:
        state.reranked_contexts = state.raw_contexts
        state.current_step = "generate"
        return state

    start_time = perf_counter()

    # Simple reranking: just take top_k by distance (already sorted)
    # In a more advanced version, could use LLM-based reranking
    state.reranked_contexts = state.raw_contexts[:state.top_k]

    rerank_time = (perf_counter() - start_time) * 1000
    state.metadata["rerank_ms"] = round(rerank_time)
    state.current_step = "generate"
    return state


def generate(state: ChatState) -> ChatState:
    """Generate answer using retrieved contexts"""
    start_time = perf_counter()

    # Use reranked contexts if available, otherwise raw contexts
    contexts = state.reranked_contexts if state.reranked_contexts else state.raw_contexts

    # Build context text
    context_parts = []
    for ctx in contexts:
        meta = ctx.get("metadata", {})
        text = ctx.get("text", "")
        message_id = meta.get("message_id", "unknown")
        context_parts.append(f"[message_id={message_id}] {text}")

    context_text = "\n\n".join(context_parts)

    # System prompt
    system_prompt = """You are an email assistant. Answer user questions strictly based on the provided email excerpts.

Guidelines:
- Only use information from the provided email contexts
- Cite sources by referencing message_id when possible
- If the answer is not in the provided emails, say "I don't have enough information in the emails to answer this question"
- Be concise and helpful
- Maintain professional tone"""

    # User prompt
    user_prompt = f"""Email contexts:
{context_text}

Question: {state.question}

Please provide a helpful answer based on the email contexts above."""

    # Add conversation history if available
    messages = []
    if state.conversation_history:
        messages.extend([
            {"role": msg["role"], "content": msg["content"]}
            for msg in state.conversation_history[-4:]  # Last 4 messages
        ])

    messages.extend([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    try:
        response = _client.chat.completions.create(
            model=config.model_name,
            messages=messages,
            temperature=state.temperature,
            max_tokens=state.max_tokens,
            stream=False,
        )

        state.answer = response.choices[0].message.content

        # Include the full text content in sources for user to see
        state.sources = []
        for ctx in contexts:
            meta = ctx.get("metadata", {}).copy()
            meta["text"] = ctx.get("text", "")  # Add the actual text content
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
    # Calculate total latency if not set
    if "latency_ms" not in state.metadata:
        total_time = state.metadata.get("retrieve_ms", 0) + \
                     state.metadata.get("rerank_ms", 0) + \
                     state.metadata.get("generation_ms", 0)
        state.metadata["latency_ms"] = total_time

    state.metadata["top_k"] = state.top_k
    state.metadata["intent"] = state.intent

    state.current_step = "done"
    return state


def route_after_classify(state: ChatState) -> Literal["retrieve", "generate"]:
    """Route based on intent classification"""
    if state.intent == "retrieve":
        return "retrieve"
    else:
        return "generate"


def route_after_retrieve(state: ChatState) -> Literal["rerank", "generate"]:
    """Route to reranking or directly to generation"""
    if len(state.raw_contexts) > state.top_k:
        return "rerank"
    return "generate"


def build_chat_workflow() -> StateGraph:
    """Build and compile the chat workflow graph"""
    # Create graph
    graph = StateGraph(ChatState)

    # Add nodes
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("retrieve", retrieve)
    graph.add_node("rerank", rerank)
    graph.add_node("generate", generate)
    graph.add_node("finalize", finalize)

    # Set entry point
    graph.set_entry_point("classify_intent")

    # Add conditional edges
    graph.add_conditional_edges(
        "classify_intent",
        route_after_classify,
        {
            "retrieve": "retrieve",
            "generate": "generate",
        }
    )

    # Linear edges
    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {
            "rerank": "rerank",
            "generate": "generate",
        }
    )
    graph.add_edge("rerank", "generate")
    graph.add_edge("generate", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()
