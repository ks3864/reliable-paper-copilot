"""Evaluation Metrics Module."""

from typing import List, Dict, Any
import re


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
        )
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
    }

    optional_metrics = ["groundedness", "correctness", "completeness", "answer_quality"]
    for metric_name in optional_metrics:
        if any(metric_name in m for m in individual_metrics):
            aggregate[metric_name] = (
                sum(m.get(metric_name, 0.0) for m in individual_metrics) / len(individual_metrics)
            )
    
    
    return {
        "aggregate": aggregate,
        "per_question": individual_metrics
    }


if __name__ == "__main__":
    # Quick test
    print("Testing evaluation metrics...")
    
    pred = "28.4 BLEU score on WMT English-German"
    gold = "28.4 BLEU score on the WMT English-German translation task"
    
    print(f"Exact match: {exact_match_score(pred, gold)}")
    print(f"F1 score: {f1_score(pred, gold):.3f}")
