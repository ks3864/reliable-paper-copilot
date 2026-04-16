"""Embedding-based retrieval with optional fallback lexical scoring."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

try:
    import faiss
except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
    faiss = None

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
    np = None

try:
    from sentence_transformers import SentenceTransformer
except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
    SentenceTransformer = None

from .reranker import BaseReranker


class Retriever:
    """FAISS-based retriever for paper chunks."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", reranker: Optional[BaseReranker] = None):
        """
        Initialize retriever with embedding model.

        Args:
            model_name: Name of sentence-transformers model
            reranker: Optional reranker applied after vector search
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name) if SentenceTransformer is not None else None
        self.reranker = reranker
        self.index: Optional[faiss.Index] = None
        self.chunks: List[Dict[str, Any]] = []
        self.chunk_embeddings: Optional[np.ndarray] = None
        self.use_lexical_fallback = self.model is None or faiss is None or np is None

    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Build FAISS index from chunks.

        Args:
            chunks: List of chunk dictionaries from chunking module
        """
        self.chunks = chunks

        if self.use_lexical_fallback:
            print("sentence-transformers/faiss unavailable, using lexical retrieval fallback.")
            self.index = None
            self.chunk_embeddings = None
            return

        texts = [chunk["text"] for chunk in chunks]

        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=True)

        faiss.normalize_L2(embeddings)
        self.chunk_embeddings = embeddings.astype("float32")

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.chunk_embeddings)

        print(f"Built index with {self.index.ntotal} vectors of dimension {dimension}")

    def retrieve(self, query: str, top_k: int = 5, rerank_top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant chunks for a query.

        Args:
            query: Query string
            top_k: Number of chunks to return after optional reranking
            rerank_top_k: Number of initial candidates to rerank. Defaults to top_k.

        Returns:
            List of chunk dictionaries with similarity scores and optional reranker scores.
        """
        if self.index is None:
            if self.use_lexical_fallback:
                return self._retrieve_lexically(query, top_k=top_k)
            raise ValueError("Index not built. Call build_index() first.")

        search_k = min(max(rerank_top_k or top_k, top_k), self.index.ntotal)

        query_embedding = self.model.encode([query]).astype("float32")
        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(query_embedding, search_k)

        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx >= 0:
                chunk = self.chunks[idx].copy()
                chunk["retrieval_score"] = float(score)
                chunk["rank"] = i + 1
                results.append(chunk)

        if self.reranker is not None and results:
            return self.reranker.rerank(query, results, top_k=top_k)

        return results[:top_k]

    def _retrieve_lexically(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_terms = set(re.findall(r"\w+", query.lower()))
        scored: List[Dict[str, Any]] = []

        for chunk in self.chunks:
            chunk_terms = set(re.findall(r"\w+", chunk["text"].lower()))
            overlap = query_terms & chunk_terms
            score = len(overlap) / max(len(query_terms), 1)
            updated = dict(chunk)
            updated["retrieval_score"] = float(score)
            scored.append(updated)

        scored.sort(key=lambda chunk: chunk["retrieval_score"], reverse=True)
        for rank, chunk in enumerate(scored, start=1):
            chunk["rank"] = rank

        results = scored[:top_k]
        if self.reranker is not None and results:
            return self.reranker.rerank(query, results, top_k=top_k)
        return results

    def save(self, index_path: str, chunks_path: str) -> None:
        """Save index and chunks to disk."""
        if self.index is None:
            if self.use_lexical_fallback:
                raise ValueError("Lexical fallback retrievers do not persist FAISS indexes.")
            raise ValueError("No index to save.")

        faiss.write_index(self.index, index_path)

        chunks_to_save = [{k: v for k, v in chunk.items() if k != "embedding"} for chunk in self.chunks]

        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump({"chunks": chunks_to_save, "total": len(chunks_to_save)}, f, indent=2)

        np.save(chunks_path.replace(".json", "_embeddings.npy"), self.chunk_embeddings)

        print(f"Saved index to {index_path}")
        print(f"Saved {len(chunks_to_save)} chunks to {chunks_path}")

    def load(self, index_path: str, chunks_path: str) -> None:
        """Load index and chunks from disk."""
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index file not found: {index_path}")
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Chunks file not found: {chunks_path}")

        self.index = faiss.read_index(index_path)

        with open(chunks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.chunks = data.get("chunks", [])

        emb_path = chunks_path.replace(".json", "_embeddings.npy")
        if os.path.exists(emb_path):
            self.chunk_embeddings = np.load(emb_path)

        print(f"Loaded index with {self.index.ntotal} vectors")
        print(f"Loaded {len(self.chunks)} chunks")


def create_retriever(
    chunks: List[Dict[str, Any]],
    model_name: str = "all-MiniLM-L6-v2",
    reranker: Optional[BaseReranker] = None,
) -> Retriever:
    """Create and build a retriever from chunks."""
    retriever = Retriever(model_name=model_name, reranker=reranker)
    retriever.build_index(chunks)
    return retriever


if __name__ == "__main__":
    test_chunks = [
        {"chunk_id": 0, "section": "abstract", "text": "This paper presents a new method for machine learning.", "metadata": {}},
        {"chunk_id": 1, "section": "methods", "text": "Our approach uses deep neural networks with attention mechanisms.", "metadata": {}},
        {"chunk_id": 2, "section": "results", "text": "We achieved 95% accuracy on the benchmark dataset.", "metadata": {}},
    ]

    retriever = create_retriever(test_chunks)
    results = retriever.retrieve("What accuracy did they achieve?", top_k=2)

    print("\nQuery: What accuracy did they achieve?")
    for r in results:
        print(f"  [{r['section']}] score={r['retrieval_score']:.3f}: {r['text'][:60]}...")
