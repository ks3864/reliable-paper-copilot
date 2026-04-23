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

    def test_request_logger_reads_recent_filtered_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = RequestLogger(log_dir=tmpdir)
            logger.log(
                logger.create_event(
                    endpoint="/ask",
                    paper_id="paper-1",
                    question="First question?",
                    latency_ms=10,
                    token_usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    model_version="model-a",
                )
            )
            logger.log(
                logger.create_event(
                    endpoint="/health",
                    paper_id="paper-1",
                    question=None,
                    latency_ms=1,
                    token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    model_version="model-a",
                )
            )
            logger.log(
                logger.create_event(
                    endpoint="/ask",
                    paper_id="paper-1",
                    question="Second question?",
                    latency_ms=20,
                    token_usage={"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
                    model_version="model-b",
                )
            )

            events = logger.read_events(paper_id="paper-1", endpoint="/ask", limit=5)

            self.assertEqual([event["question"] for event in events], ["Second question?", "First question?"])
            self.assertTrue(all(event["endpoint"] == "/ask" for event in events))

    def test_request_logger_deletes_filtered_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = RequestLogger(log_dir=tmpdir)
            logger.log(
                logger.create_event(
                    endpoint="/ask",
                    paper_id="paper-1",
                    question="Delete me",
                    latency_ms=10,
                    token_usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    model_version="model-a",
                )
            )
            logger.log(
                logger.create_event(
                    endpoint="/health",
                    paper_id="paper-1",
                    question=None,
                    latency_ms=1,
                    token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    model_version="model-a",
                )
            )
            logger.log(
                logger.create_event(
                    endpoint="/ask",
                    paper_id="paper-2",
                    question="Keep me",
                    latency_ms=20,
                    token_usage={"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
                    model_version="model-b",
                )
            )

            deleted_count = logger.delete_events(paper_id="paper-1", endpoint="/ask")
            remaining_events = logger.read_events(limit=10)

            self.assertEqual(deleted_count, 1)
            self.assertEqual(len(remaining_events), 2)
            self.assertEqual([event["endpoint"] for event in remaining_events], ["/ask", "/health"])
            self.assertEqual([event["paper_id"] for event in remaining_events], ["paper-2", "paper-1"])


if __name__ == "__main__":
    unittest.main()
