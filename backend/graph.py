from __future__ import annotations

from typing import Dict, Any, List

from langgraph.graph import StateGraph
from openai import OpenAI

from .config import load_config
from .vectorstore import query_chunks
from .ingest import embed_texts


config = load_config()
_client = OpenAI(api_key=config.openai_api_key)


def classify_intent(state: Dict[str, Any]) -> Dict[str, Any]:
    q: str = state["question"]
    # Simple heuristic: retrieval for most questions
    state["intent"] = "retrieve" if len(q) > 0 else "direct"
    return state


def retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
    account_id: int = state["account_id"]
    question: str = state["question"]
    top_k: int = state.get("top_k", config.top_k)
    q_emb = embed_texts([question])[0]
    res = query_chunks(account_id, q_emb, top_k=top_k)
    docs = []
    for i in range(len(res.get("ids", [[]])[0])):
        docs.append(
            {
                "text": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i],
            }
        )
    state["contexts"] = docs
    return state


def generate(state: Dict[str, Any]) -> Dict[str, Any]:
    question: str = state["question"]
    contexts: List[Dict[str, Any]] = state.get("contexts", [])
    system = (
        "You are an email assistant. Answer strictly using the provided email excerpts. "
        "Cite sources by message_id. If unsure, say you don't know."
    )
    context_text = "\n\n".join(
        [
            f"[message_id={c['metadata'].get('message_id')}] {c['text']}"
            for c in contexts
        ]
    )
    prompt = f"Context:\n{context_text}\n\nQuestion: {question}\nAnswer:"

    resp = _client.chat.completions.create(
        model=config.model_name,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=500,
        stream=False,
    )
    answer = resp.choices[0].message.content
    state["answer"] = answer
    state["sources"] = [c["metadata"] for c in contexts]
    return state


def build_graph():
    sg = StateGraph(dict)
    sg.add_node("classify_intent", classify_intent)
    sg.add_node("retrieve", retrieve)
    sg.add_node("generate", generate)
    sg.set_entry_point("classify_intent")
    # classify → retrieve → generate
    sg.add_edge("classify_intent", "retrieve")
    sg.add_edge("retrieve", "generate")
    return sg.compile()
