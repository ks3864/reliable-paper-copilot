"""Tests for request logging and answer telemetry."""

import json
import tempfile
import unittest
from pathlib import Path

from src.answering import AnswerGenerator
from src.utils import RequestLogger


class StubRetriever:
    def __init__(self, chunks):
        self.chunks = chunks

    def retrieve(self, query, top_k=5):
        return self.chunks[:top_k]


class StaticLLM:
    def __call__(self, prompt):
        return "The paper uses the MIMIC-III dataset."


class RequestLoggingTests(unittest.TestCase):
    def test_answer_generator_reports_token_usage_and_model_version(self):
        retriever = StubRetriever(
            [
                {"chunk_id": 0, "section": "methods", "text": "We use the MIMIC-III dataset.", "retrieval_score": 0.95},
            ]
        )
        generator = AnswerGenerator(retriever, StaticLLM(), model_version="test-model-v1")

        result = generator.answer("What dataset was used?")

        self.assertEqual(result["model_version"], "test-model-v1")
        self.assertGreater(result["token_usage"]["prompt_tokens"], 0)
        self.assertGreater(result["token_usage"]["completion_tokens"], 0)
        self.assertEqual(
            result["token_usage"]["total_tokens"],
            result["token_usage"]["prompt_tokens"] + result["token_usage"]["completion_tokens"],
        )

    def test_request_logger_writes_jsonl_event(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = RequestLogger(log_dir=tmpdir)
            event = logger.create_event(
                endpoint="/ask",
                paper_id="paper-123",
                question="What dataset was used?",
                latency_ms=12.345,
                token_usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                model_version="test-model-v1",
                extra={"num_chunks_retrieved": 2},
            )
            logger.log(event)

            log_path = Path(tmpdir) / "requests.jsonl"
            lines = log_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            payload = json.loads(lines[0])
            self.assertEqual(payload["endpoint"], "/ask")
            self.assertEqual(payload["paper_id"], "paper-123")
            self.assertEqual(payload["token_usage"]["total_tokens"], 15)
            self.assertEqual(payload["model_version"], "test-model-v1")
            self.assertEqual(payload["num_chunks_retrieved"], 2)


if __name__ == "__main__":
    unittest.main()
