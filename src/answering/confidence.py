"""Confidence estimation helpers for retrieval-grounded answering."""

from typing import Any, Dict, List, Optional


class RetrievalConfidenceEstimator:
    """Estimate whether retrieved chunks are strong enough to answer from."""

    def __init__(
        self,
        min_top_score: float = 0.35,
        min_average_score: float = 0.25,
        average_over_top_n: int = 3,
    ):
        self.min_top_score = min_top_score
        self.min_average_score = min_average_score
        self.average_over_top_n = average_over_top_n

    def assess(self, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return confidence metadata for a retrieved result set."""
        if not retrieved_chunks:
            return {
                "has_good_match": False,
                "top_score": None,
                "average_score": None,
                "reason": "no_retrieved_chunks",
            }

        scores = [float(chunk.get("reranker_score", chunk.get("retrieval_score", 0.0))) for chunk in retrieved_chunks]
        top_score = scores[0]
        avg_window = scores[: self.average_over_top_n]
        average_score = sum(avg_window) / len(avg_window)

        if top_score < self.min_top_score:
            return {
                "has_good_match": False,
                "top_score": top_score,
                "average_score": average_score,
                "reason": "top_score_below_threshold",
            }

        if average_score < self.min_average_score:
            return {
                "has_good_match": False,
                "top_score": top_score,
                "average_score": average_score,
                "reason": "average_score_below_threshold",
            }

        return {
            "has_good_match": True,
            "top_score": top_score,
            "average_score": average_score,
            "reason": None,
        }
