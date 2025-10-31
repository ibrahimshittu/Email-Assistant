from __future__ import annotations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from time import perf_counter
import asyncio
from concurrent.futures import ThreadPoolExecutor

from deepeval import evaluate
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric,
    ContextualRecallMetric,
    HallucinationMetric,
)
from deepeval.test_case import LLMTestCase

from config import load_config


config = load_config()


@dataclass
class EnhancedEvalResult:
    """Enhanced evaluation result with comprehensive metrics"""
    question: str
    answer: str
    expected_output: Optional[str]
    retrieval_context: List[str]

    # Metrics (0.0 to 1.0)
    answer_relevancy: float
    faithfulness: float
    contextual_relevancy: float
    contextual_recall: float
    hallucination_score: float

    # Performance
    latency_ms: int

    # Status
    passed: bool
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


def create_metrics(model: str = None) -> List:
    """
    Create DeepEval metrics for RAG evaluation.

    Args:
        model: OpenAI model to use for evaluation (defaults to config.eval_model)

    Returns:
        List of configured DeepEval metrics
    """
    eval_model = model or config.eval_model

    return [
        AnswerRelevancyMetric(
            threshold=0.7,
            model=eval_model,
            include_reason=True
        ),
        FaithfulnessMetric(
            threshold=0.7,
            model=eval_model,
            include_reason=True
        ),
        ContextualRelevancyMetric(
            threshold=0.7,
            model=eval_model,
            include_reason=True
        ),
        ContextualRecallMetric(
            threshold=0.7,
            model=eval_model,
            include_reason=True
        ),
        HallucinationMetric(
            threshold=0.5,  # Lower is better for hallucination
            model=eval_model,
            include_reason=True
        ),
    ]


def _run_evaluate_sync(test_case, metrics):
    """
    Run DeepEval evaluation synchronously in a separate thread.
    This avoids event loop conflicts with uvloop.
    """
    return evaluate(
        test_cases=[test_case],
        metrics=metrics
    )


async def run_deepeval(
    samples: List[Dict[str, Any]],
    ask_fn,
    verbose: bool = False
) -> List[EnhancedEvalResult]:
    """
    Run comprehensive RAG evaluation using DeepEval.

    Args:
        samples: List of test samples with 'question', 'expected_output' (optional)
        ask_fn: Function that takes a question and returns (answer, sources)
        verbose: Print detailed evaluation progress

    Returns:
        List of EnhancedEvalResult with all metrics
    """
    results: List[EnhancedEvalResult] = []
    metrics = create_metrics()

    for sample in samples:
        question = sample["question"]
        expected_output = sample.get("expected_output") or sample.get("reference")

        # Execute the RAG pipeline
        t0 = perf_counter()
        answer, sources = await ask_fn(question)
        latency_ms = int((perf_counter() - t0) * 1000)

        # Extract context from sources
        retrieval_context = []
        if sources:
            for source in sources:
                if isinstance(source, dict):
                    text = source.get("text", "")
                    if text:
                        retrieval_context.append(text)

        # If no context retrieved, add placeholder
        if not retrieval_context:
            retrieval_context = ["No context retrieved"]

        # Create DeepEval test case
        test_case = LLMTestCase(
            input=question,
            actual_output=answer,
            expected_output=expected_output,
            retrieval_context=retrieval_context,
            context=retrieval_context  
        )

        # Evaluate with all metrics in a thread pool to avoid event loop conflicts
        try:
            # Run evaluation in a thread pool executor
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                eval_results = await loop.run_in_executor(
                    executor,
                    _run_evaluate_sync,
                    test_case,
                    metrics
                )

            # Extract metric scores
            metric_scores = {}
            for metric_result in eval_results.test_results[0].metrics_data:
                metric_name = metric_result.name.lower().replace(" ", "_")
                metric_scores[metric_name] = metric_result.score

            # Determine if test passed
            passed = all(
                metric_result.success
                for metric_result in eval_results.test_results[0].metrics_data
            )

            # Get failure reasons if any
            reasons = [
                metric_result.reason
                for metric_result in eval_results.test_results[0].metrics_data
                if not metric_result.success and metric_result.reason
            ]
            reason = "; ".join(reasons) if reasons else None

            result = EnhancedEvalResult(
                question=question,
                answer=answer,
                expected_output=expected_output,
                retrieval_context=retrieval_context,
                answer_relevancy=metric_scores.get("answer_relevancy", 0.0),
                faithfulness=metric_scores.get("faithfulness", 0.0),
                contextual_relevancy=metric_scores.get("contextual_relevancy", 0.0),
                contextual_recall=metric_scores.get("contextual_recall", 0.0),
                hallucination_score=metric_scores.get("hallucination", 0.0),
                latency_ms=latency_ms,
                passed=passed,
                reason=reason
            )

        except Exception as e:
            # Fallback result if evaluation fails
            result = EnhancedEvalResult(
                question=question,
                answer=answer,
                expected_output=expected_output,
                retrieval_context=retrieval_context,
                answer_relevancy=0.0,
                faithfulness=0.0,
                contextual_relevancy=0.0,
                contextual_recall=0.0,
                hallucination_score=1.0,  # High hallucination on error
                latency_ms=latency_ms,
                passed=False,
                reason=f"Evaluation error: {str(e)}"
            )

        results.append(result)

    return results


def calculate_aggregate_metrics(results: List[EnhancedEvalResult]) -> Dict[str, Any]:
    """
    Calculate aggregate statistics across all evaluation results.

    Returns:
        Dictionary with average scores, pass rate, and performance metrics
    """
    if not results:
        return {}

    total = len(results)
    passed = sum(1 for r in results if r.passed)

    return {
        "total_tests": total,
        "passed_tests": passed,
        "pass_rate": round(passed / total, 2),
        "avg_answer_relevancy": round(
            sum(r.answer_relevancy for r in results) / total, 2
        ),
        "avg_faithfulness": round(
            sum(r.faithfulness for r in results) / total, 2
        ),
        "avg_contextual_relevancy": round(
            sum(r.contextual_relevancy for r in results) / total, 2
        ),
        "avg_contextual_recall": round(
            sum(r.contextual_recall for r in results) / total, 2
        ),
        "avg_hallucination_score": round(
            sum(r.hallucination_score for r in results) / total, 2
        ),
        "avg_latency_ms": round(
            sum(r.latency_ms for r in results) / total
        ),
        "min_latency_ms": min(r.latency_ms for r in results),
        "max_latency_ms": max(r.latency_ms for r in results),
    }
