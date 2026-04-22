"""Tests for retrieval reranking behavior."""

import math
import sys
import types
import unittest


class FakeArray:
    def __init__(self, rows):
        self.rows = [[float(value) for value in row] for row in rows]
        self.shape = (len(self.rows), len(self.rows[0]) if self.rows else 0)

    def astype(self, _dtype):
        return self

    def __len__(self):
        return len(self.rows)

    def __iter__(self):
        return iter(self.rows)

    def __getitem__(self, index):
        value = self.rows[index]
        if isinstance(value, list):
            return FakeArray(value) if value and isinstance(value[0], list) else value
        return value


class FakeNumpyModule(types.SimpleNamespace):
    ndarray = FakeArray

    def array(self, rows, dtype=None):
        return FakeArray(rows)

    def save(self, path, array):
        return None

    def load(self, path):
        raise NotImplementedError


class FakeIndexFlatIP:
    def __init__(self, dimension):
        self.dimension = dimension
        self.vectors = []

    @property
    def ntotal(self):
        return len(self.vectors)

    def add(self, embeddings):
        self.vectors.extend(embeddings.rows)

    def search(self, query_embedding, top_k):
        query = query_embedding.rows[0]
        scored = []
        for idx, vector in enumerate(self.vectors):
            score = sum(q * v for q, v in zip(query, vector))
            scored.append((score, idx))
        scored.sort(key=lambda item: item[0], reverse=True)
        top = scored[:top_k]
        return [[score for score, _ in top]], [[idx for _, idx in top]]


class FakeFaissModule(types.SimpleNamespace):
    Index = FakeIndexFlatIP

    def IndexFlatIP(self, dimension):
        return FakeIndexFlatIP(dimension)

    def normalize_L2(self, embeddings):
        for row in embeddings.rows:
            norm = math.sqrt(sum(value * value for value in row))
            if norm:
                for index, value in enumerate(row):
                    row[index] = value / norm

    def write_index(self, index, path):
        return None

    def read_index(self, path):
        raise NotImplementedError


class DummySentenceTransformer:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def encode(self, texts, show_progress_bar: bool = False):
        if len(texts) == 1:
            return FakeArray([[1.0, 0.0]])

        return FakeArray(
            [
                [0.90, 0.10],
                [0.80, 0.20],
                [0.70, 0.30],
            ]
        )


class DummyCrossEncoder:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def predict(self, pairs):
        return [0.0 for _ in pairs]


sys.modules.setdefault("numpy", FakeNumpyModule())
sys.modules.setdefault("faiss", FakeFaissModule())
sys.modules.setdefault(
    "sentence_transformers",
    types.SimpleNamespace(SentenceTransformer=DummySentenceTransformer, CrossEncoder=DummyCrossEncoder),
)

from src.retrieval.reranker import BaseReranker
from src.retrieval.retriever import Retriever


class KeywordReranker(BaseReranker):
    def score(self, query, chunks):
        scores = []
        for chunk in chunks:
            text = chunk["text"].lower()
            if "benchmark" in text:
                scores.append(0.99)
            elif "dataset" in text:
                scores.append(0.75)
            else:
                scores.append(0.10)
        return scores


class RetrievalRerankingTests(unittest.TestCase):
    def test_retrieve_reranks_initial_candidates(self):
        retriever = Retriever(reranker=KeywordReranker())
        retriever.build_index(
            [
                {"chunk_id": 0, "section": "abstract", "text": "General background about the paper.", "metadata": {}},
                {"chunk_id": 1, "section": "methods", "text": "We train on a medical dataset with several cohorts.", "metadata": {}},
                {"chunk_id": 2, "section": "results", "text": "The benchmark evaluation achieves the strongest performance.", "metadata": {}},
            ]
        )

        results = retriever.retrieve("What dataset was used?", top_k=2, rerank_top_k=3)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["chunk_id"], 2)
        self.assertEqual(results[0]["rank"], 1)
        self.assertEqual(results[0]["initial_rank"], 3)
        self.assertIn("reranker_score", results[0])
        self.assertEqual(results[1]["chunk_id"], 1)
        self.assertEqual(results[1]["rank"], 2)

    def test_retrieve_without_reranker_preserves_vector_order(self):
        retriever = Retriever()
        retriever.build_index(
            [
                {"chunk_id": 0, "section": "abstract", "text": "First candidate.", "metadata": {}},
                {"chunk_id": 1, "section": "methods", "text": "Second candidate.", "metadata": {}},
                {"chunk_id": 2, "section": "results", "text": "Third candidate.", "metadata": {}},
            ]
        )

        results = retriever.retrieve("test query", top_k=2)

        self.assertEqual([chunk["chunk_id"] for chunk in results], [0, 1])
        self.assertTrue(all("reranker_score" not in chunk for chunk in results))

    def test_hybrid_retrieval_fuses_dense_and_lexical_signals(self):
        retriever = Retriever(retrieval_mode="hybrid", lexical_weight=3.0, dense_weight=0.2)
        retriever.build_index(
            [
                {"chunk_id": 0, "section": "abstract", "text": "General discussion without the key phrase.", "metadata": {}},
                {"chunk_id": 1, "section": "methods", "text": "Dataset construction details for the medical cohort.", "metadata": {}},
                {"chunk_id": 2, "section": "results", "text": "Benchmark dataset performance is summarized here.", "metadata": {}},
            ]
        )

        results = retriever.retrieve("What dataset was used?", top_k=3)

        self.assertEqual(results[0]["chunk_id"], 2)
        self.assertEqual({chunk["chunk_id"] for chunk in results[:2]}, {1, 2})
        self.assertAlmostEqual(results[0]["dense_rank"], 3)
        self.assertAlmostEqual(results[0]["lexical_rank"], 1)
        self.assertIn("hybrid_score", results[0])
        self.assertIn("dense_score", results[0])
        self.assertIn("lexical_score", results[0])

    def test_hybrid_mode_uses_lexical_results_when_dense_backend_unavailable(self):
        retriever = Retriever(retrieval_mode="hybrid")
        retriever.use_lexical_fallback = True
        retriever.index = None
        retriever.chunks = [
            {"chunk_id": 0, "section": "abstract", "text": "General background text.", "metadata": {}},
            {"chunk_id": 1, "section": "methods", "text": "This chunk mentions the dataset explicitly.", "metadata": {}},
        ]

        results = retriever.retrieve("Which dataset is mentioned?", top_k=2)

        self.assertEqual(results[0]["chunk_id"], 1)
        self.assertIn("lexical_score", results[0])

    def test_lexical_retrieval_uses_bm25_length_normalization(self):
        retriever = Retriever(retrieval_mode="lexical")
        retriever.chunks = [
            {"chunk_id": 0, "section": "methods", "text": "dataset dataset dataset", "metadata": {}},
            {
                "chunk_id": 1,
                "section": "methods",
                "text": "dataset noise noise noise noise noise noise noise noise noise noise noise",
                "metadata": {},
            },
        ]

        results = retriever.retrieve("dataset", top_k=2)

        self.assertEqual([chunk["chunk_id"] for chunk in results], [0, 1])
        self.assertGreater(results[0]["lexical_score"], results[1]["lexical_score"])


if __name__ == "__main__":
    unittest.main()
