from __future__ import annotations

from typing import List, Dict, Any
from dataclasses import dataclass
from time import perf_counter

from openai import OpenAI

from config import load_config


config = load_config()
_client = OpenAI(api_key=config.openai_api_key)


@dataclass
class EvalResult:
    question: str
    reference: str
    answer: str
    faithfulness: int
    relevance: int
    latency_ms: int


def judge_faithfulness(question: str, reference_context: str, answer: str) -> int:
    rubric = (
        "Score 0-1: Is the answer fully supported by the reference context? "
        "Return only a number 0 or 1."
    )
    prompt = f"Reference:\n{reference_context}\n\nAnswer:\n{answer}\n\nQuestion:\n{question}\n\n{rubric}"
    resp = _client.chat.completions.create(
        model=config.eval_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=2,
    )
    txt = resp.choices[0].message.content.strip()
    return 1 if txt.startswith("1") else 0


def judge_relevance(question: str, answer: str) -> int:
    rubric = "Score 0-1: Is the answer relevant to the question? Return only 0 or 1."
    prompt = f"Question:\n{question}\n\nAnswer:\n{answer}\n\n{rubric}"
    resp = _client.chat.completions.create(
        model=config.eval_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=2,
    )
    txt = resp.choices[0].message.content.strip()
    return 1 if txt.startswith("1") else 0


async def run_eval(samples: List[Dict[str, Any]], ask_fn) -> List[EvalResult]:
    results: List[EvalResult] = []
    for s in samples:
        t0 = perf_counter()
        answer, _sources = await ask_fn(
            s["question"]
        )  # answer function returns (answer, sources)
        dt = int((perf_counter() - t0) * 1000)
        faith = judge_faithfulness(s["question"], s.get("reference", ""), answer)
        rel = judge_relevance(s["question"], answer)
        results.append(
            EvalResult(
                question=s["question"],
                reference=s.get("reference", ""),
                answer=answer,
                faithfulness=faith,
                relevance=rel,
                latency_ms=dt,
            )
        )
    return results
