"""Tests for retrieval confidence fallback behavior."""

import unittest

from src.answering import AnswerGenerator, RetrievalConfidenceEstimator


class StubRetriever:
    def __init__(self, chunks):
        self.chunks = chunks

    def retrieve(self, query, top_k=5):
        return self.chunks[:top_k]


class RecordingLLM:
    def __init__(self, response="grounded answer"):
        self.response = response
        self.calls = 0

    def __call__(self, prompt):
        self.calls += 1
        return self.response


class ConfidenceEstimationTests(unittest.TestCase):
    def test_falls_back_when_retrieval_scores_are_too_low(self):
        llm = RecordingLLM()
        retriever = StubRetriever(
            [
                {"chunk_id": 0, "section": "methods", "text": "Weakly related context.", "retrieval_score": 0.18},
                {"chunk_id": 1, "section": "results", "text": "Another weak context.", "retrieval_score": 0.12},
            ]
        )
        generator = AnswerGenerator(
            retriever,
            llm,
            confidence_estimator=RetrievalConfidenceEstimator(min_top_score=0.4, min_average_score=0.3),
        )

        result = generator.answer("What dataset was used?")

        self.assertEqual(llm.calls, 0)
        self.assertIn("strong enough match", result["answer"])
        self.assertEqual(result["confidence"]["reason"], "top_score_below_threshold")
        self.assertEqual(result["sources"], [])

    def test_generates_answer_when_retrieval_confidence_is_high(self):
        llm = RecordingLLM("The paper uses the MIMIC-III dataset.")
        retriever = StubRetriever(
            [
                {"chunk_id": 0, "section": "methods", "text": "We use the MIMIC-III dataset.", "retrieval_score": 0.82},
                {"chunk_id": 1, "section": "data", "text": "The cohort includes ICU stays.", "retrieval_score": 0.77},
            ]
        )
        generator = AnswerGenerator(
            retriever,
            llm,
            confidence_estimator=RetrievalConfidenceEstimator(min_top_score=0.4, min_average_score=0.3),
        )

        result = generator.answer("What dataset was used?")

        self.assertEqual(llm.calls, 1)
        self.assertIn("MIMIC-III", result["answer"])
        self.assertTrue(result["confidence"]["has_good_match"])
        self.assertEqual(result["sources"], ["methods", "data"])


if __name__ == "__main__":
    unittest.main()
