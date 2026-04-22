"""Evaluation Metrics Module."""

from typing import List, Dict, Any
import re


REFUSAL_PATTERNS = (
    "couldn't find",
    "could not find",
    "cannot find",
    "can't find",
    "don't have enough information",
    "do not have enough information",
    "does not provide",
    "doesn't provide",
    "not enough information",
    "cannot answer confidently",
    "can't answer confidently",
    "unable to answer",
)


def exact_match_score(prediction: str, gold_answer: str) -> float:
    """
    Compute exact match score.
    
    Returns 1.0 if prediction matches gold_answer exactly (case-insensitive),
    0.0 otherwise.
    """
    return 1.0 if prediction.strip().lower() == gold_answer.strip().lower() else 0.0


def f1_score(prediction: str, gold_answer: str) -> float:
    """
    Compute token-level F1 score between prediction and gold answer.
    """
    pred_tokens = set(re.findall(r'\w+', prediction.lower()))
    gold_tokens = set(re.findall(r'\w+', gold_answer.lower()))
    
    if len(pred_tokens) == 0 or len(gold_tokens) == 0:
        return 0.0
    
    overlap = pred_tokens & gold_tokens
    precision = len(overlap) / len(pred_tokens)
    recall = len(overlap) / len(gold_tokens)
    
    if precision + recall == 0:
        return 0.0
    
    return 2 * (precision * recall) / (precision + recall)


def is_refusal_answer(prediction: str) -> float:
    """Return 1.0 when the answer looks like a refusal or abstention."""
    normalized = prediction.strip().lower()
    return 1.0 if any(pattern in normalized for pattern in REFUSAL_PATTERNS) else 0.0


def _is_relevant_retrieved_chunk(
    chunk: Dict[str, Any], relevant_sections: List[str], relevant_source: str | None = None
) -> bool:
    """Return True when a retrieved chunk matches the expected section and source."""
    if chunk.get("section", "") not in set(relevant_sections):
        return False

    if relevant_source is None:
        return True

    return chunk.get("metadata", {}).get("source") == relevant_source


def retrieval_hit_rate(
    retrieved_chunks: List[Dict[str, Any]],
    relevant_sections: List[str],
    relevant_source: str | None = None,
) -> float:
    """
    Compute retrieval hit rate.

    Returns 1.0 if at least one retrieved chunk comes from a relevant section,
    and optionally the expected source paper, 0.0 otherwise.
    """
    return 1.0 if any(
        _is_relevant_retrieved_chunk(chunk, relevant_sections, relevant_source)
        for chunk in retrieved_chunks
    ) else 0.0


def retrieval_mrr(
    retrieved_chunks: List[Dict[str, Any]],
    relevant_sections: List[str],
    relevant_source: str | None = None,
) -> float:
    """
    Compute Mean Reciprocal Rank of first relevant hit.
    """
    for i, chunk in enumerate(retrieved_chunks, 1):
        if _is_relevant_retrieved_chunk(chunk, relevant_sections, relevant_source):
            return 1.0 / i

    return 0.0


def evaluate_qa_pair(
    result: Dict[str, Any],
    qa_pair: Dict[str, Any],
    judge=None,
) -> Dict[str, float]:
    """
    Evaluate a single QA pair result.
    
    Args:
        result: Output from AnswerGenerator.answer()
        qa_pair: Gold QA pair with question, gold_answer, relevant_sections
        
    Returns:
        Dictionary of metric scores
    """
    is_answerable = qa_pair.get("is_answerable", True)
    refused = is_refusal_answer(result["answer"])

    metrics = {
        "exact_match": exact_match_score(result["answer"], qa_pair["gold_answer"]),
        "f1": f1_score(result["answer"], qa_pair["gold_answer"]),
        "retrieval_hit": retrieval_hit_rate(
            result["retrieved_chunks"],
            qa_pair["relevant_sections"],
            qa_pair.get("source"),
        ),
        "retrieval_mrr": retrieval_mrr(
            result["retrieved_chunks"],
            qa_pair["relevant_sections"],
            qa_pair.get("source"),
        ),
        "is_answerable": 1.0 if is_answerable else 0.0,
        "refused": refused,
        "refusal_match": 1.0 if refused == (0.0 if is_answerable else 1.0) else 0.0,
    }

    if judge is not None:
        metrics.update(judge.score(result, qa_pair))
    
    return metrics


def evaluate_all(results: List[Dict[str, Any]], 
                 qa_pairs: List[Dict[str, Any]],
                 judge=None) -> Dict[str, Any]:
    """
    Evaluate all QA pair results and compute aggregate metrics.
    """
    if len(results) != len(qa_pairs):
        raise ValueError(f"Number of results ({len(results)}) != number of QA pairs ({len(qa_pairs)})")
    
    individual_metrics = []
    for result, qa_pair in zip(results, qa_pairs):
        metrics = evaluate_qa_pair(result, qa_pair, judge=judge)
        metrics["question_id"] = qa_pair["id"]
        individual_metrics.append(metrics)
    
    # Aggregate metrics
    aggregate = {
        "exact_match": sum(m["exact_match"] for m in individual_metrics) / len(individual_metrics),
        "f1": sum(m["f1"] for m in individual_metrics) / len(individual_metrics),
        "retrieval_hit": sum(m["retrieval_hit"] for m in individual_metrics) / len(individual_metrics),
        "retrieval_mrr": sum(m["retrieval_mrr"] for m in individual_metrics) / len(individual_metrics),
        "refusal_rate": sum(m["refused"] for m in individual_metrics) / len(individual_metrics),
        "refusal_accuracy": sum(m["refusal_match"] for m in individual_metrics) / len(individual_metrics),
    }

    answerable_metrics = [m for m in individual_metrics if m["is_answerable"] == 1.0]
    unanswerable_metrics = [m for m in individual_metrics if m["is_answerable"] == 0.0]

    true_positives = sum(1 for m in individual_metrics if m["is_answerable"] == 0.0 and m["refused"] == 1.0)
    false_positives = sum(1 for m in individual_metrics if m["is_answerable"] == 1.0 and m["refused"] == 1.0)
    false_negatives = sum(1 for m in individual_metrics if m["is_answerable"] == 0.0 and m["refused"] == 0.0)
    true_negatives = sum(1 for m in individual_metrics if m["is_answerable"] == 1.0 and m["refused"] == 0.0)
    predicted_refusals = sum(m["refused"] for m in individual_metrics)
    actual_unanswerable = len(unanswerable_metrics)

    aggregate["answerable_count"] = len(answerable_metrics)
    aggregate["unanswerable_count"] = len(unanswerable_metrics)
    aggregate["refusal_true_positives"] = true_positives
    aggregate["refusal_false_positives"] = false_positives
    aggregate["refusal_false_negatives"] = false_negatives
    aggregate["refusal_true_negatives"] = true_negatives
    aggregate["false_refusal_rate"] = false_positives / len(answerable_metrics) if answerable_metrics else 0.0
    aggregate["missed_refusal_rate"] = false_negatives / len(unanswerable_metrics) if unanswerable_metrics else 0.0
    aggregate["refusal_precision"] = true_positives / predicted_refusals if predicted_refusals else 0.0
    aggregate["refusal_recall"] = true_positives / actual_unanswerable if actual_unanswerable else 0.0
    precision = aggregate["refusal_precision"]
    recall = aggregate["refusal_recall"]
    aggregate["refusal_f1"] = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)

    optional_metrics = ["groundedness", "correctness", "completeness", "answer_quality"]
    for metric_name in optional_metrics:
        if any(metric_name in m for m in individual_metrics):
            aggregate[metric_name] = (
                sum(m.get(metric_name, 0.0) for m in individual_metrics) / len(individual_metrics)
            )
    
    
    slice_metrics = {}
    for slice_name, slice_values in (("answerable", answerable_metrics), ("unanswerable", unanswerable_metrics)):
        if not slice_values:
            continue
        refusal_count = sum(m["refused"] for m in slice_values)
        slice_metrics[slice_name] = {
            "count": len(slice_values),
            "share": len(slice_values) / len(individual_metrics),
            "exact_match": sum(m["exact_match"] for m in slice_values) / len(slice_values),
            "f1": sum(m["f1"] for m in slice_values) / len(slice_values),
            "retrieval_hit": sum(m["retrieval_hit"] for m in slice_values) / len(slice_values),
            "retrieval_mrr": sum(m["retrieval_mrr"] for m in slice_values) / len(slice_values),
            "refusal_rate": refusal_count / len(slice_values),
            "refusal_accuracy": sum(m["refusal_match"] for m in slice_values) / len(slice_values),
            "refusal_count": refusal_count,
        }

    return {
        "aggregate": aggregate,
        "per_question": individual_metrics,
        "slices": slice_metrics,
    }


if __name__ == "__main__":
    # Quick test
    print("Testing evaluation metrics...")
    
    pred = "28.4 BLEU score on WMT English-German"
    gold = "28.4 BLEU score on the WMT English-German translation task"
    
    print(f"Exact match: {exact_match_score(pred, gold)}")
    print(f"F1 score: {f1_score(pred, gold):.3f}")
