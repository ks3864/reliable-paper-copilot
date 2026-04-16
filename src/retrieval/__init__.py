"""Retrieval module with FAISS retrieval and reranking."""

from .reranker import BaseReranker

try:
    from .reranker import CrossEncoderReranker
except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
    CrossEncoderReranker = None
from .retriever import Retriever, create_retriever

__all__ = ["Retriever", "create_retriever", "BaseReranker", "CrossEncoderReranker"]
