"""Reranking module for retrieval results."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Sequence

try:
    from sentence_transformers import CrossEncoder
except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
    CrossEncoder = None


class BaseReranker(ABC):
    """Interface for reranking retrieved chunks."""

    @abstractmethod
    def score(self, query: str, chunks: Sequence[Dict[str, Any]]) -> List[float]:
        """Return a relevance score per chunk for the provided query."""

    def rerank(self, query: str, chunks: Sequence[Dict[str, Any]], top_k: int | None = None) -> List[Dict[str, Any]]:
        """Return chunks sorted by reranker score in descending order."""
        if not chunks:
            return []

        scores = self.score(query, chunks)
        if len(scores) != len(chunks):
            raise ValueError("Reranker returned a mismatched number of scores.")

        reranked: List[Dict[str, Any]] = []
        for original_rank, (chunk, score) in enumerate(zip(chunks, scores), start=1):
            updated = dict(chunk)
            updated["initial_rank"] = chunk.get("rank", original_rank)
            updated["reranker_score"] = float(score)
            reranked.append(updated)

        reranked.sort(key=lambda chunk: chunk["reranker_score"], reverse=True)

        for rank, chunk in enumerate(reranked, start=1):
            chunk["rank"] = rank

        if top_k is None:
            return reranked
        return reranked[:top_k]


class CrossEncoderReranker(BaseReranker):
    """Cross-encoder reranker backed by sentence-transformers."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        if CrossEncoder is None:
            raise ModuleNotFoundError(
                "sentence_transformers is required for CrossEncoderReranker. "
                "Install optional retrieval dependencies to enable reranking."
            )
        self.model_name = model_name
        self.model = CrossEncoder(model_name)

    def score(self, query: str, chunks: Sequence[Dict[str, Any]]) -> List[float]:
        pairs = [(query, chunk["text"]) for chunk in chunks]
        scores = self.model.predict(pairs)
        return [float(score) for score in scores]
