"""Retrieval module with FAISS and sentence-transformers."""

from .retriever import Retriever, create_retriever

__all__ = ["Retriever", "create_retriever"]
