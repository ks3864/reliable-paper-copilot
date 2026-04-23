import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.run_sample_demo import persist_demo_artifact, run_sample_demo, select_question


class SampleDemoTests(unittest.TestCase):
    def test_select_question_defaults_to_first_item(self):
        questions = [
            {"id": "first", "question": "First?"},
            {"id": "second", "question": "Second?"},
        ]

        selected = select_question(questions, None)

        self.assertEqual(selected["id"], "first")

    def test_select_question_rejects_unknown_question_id(self):
        questions = [{"id": "first", "question": "First?"}]

        with self.assertRaises(ValueError) as context:
            select_question(questions, "missing")

        self.assertIn("Unknown question id: missing", str(context.exception))
        self.assertIn("first", str(context.exception))

    def test_persist_demo_artifact_writes_timestamped_and_latest_files(self):
        payload = {"package_id": "demo-package", "question_id": "motivation", "answer": {"answer": "test"}}

        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = Path(tmpdir) / "artifacts" / "demo"
            artifact_path = persist_demo_artifact(payload, artifacts_dir)

            self.assertTrue(artifact_path.exists())
            self.assertEqual(json.loads(artifact_path.read_text(encoding="utf-8")), payload)

            latest_path = artifacts_dir / "latest.json"
            self.assertTrue(latest_path.exists())
            self.assertEqual(json.loads(latest_path.read_text(encoding="utf-8")), payload)
            self.assertIn("demo-package-motivation", artifact_path.name)

    def test_run_sample_demo_fetches_uploads_queries_and_persists_artifact(self):
        package_dir = Path("sample_packages/attention-is-all-you-need")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"
            artifacts_dir = Path(tmpdir) / "artifacts" / "demo"

            def fake_fetch_sample_package(_package_dir, requested_output_dir):
                requested_output_dir.mkdir(parents=True, exist_ok=True)
                pdf_path = requested_output_dir / "attention-is-all-you-need.pdf"
                pdf_path.write_bytes(b"%PDF-1.4\n%fake\n")
                return pdf_path

            class FakeResponse:
                def __init__(self, payload):
                    self._payload = payload

                def raise_for_status(self):
                    return None

                def json(self):
                    return self._payload

            class FakeTestClient:
                last_instance = None

                def __init__(self, _app):
                    self.calls = []
                    FakeTestClient.last_instance = self

                def post(self, path, files=None, json=None):
                    self.calls.append({"path": path, "files": files, "json": json})
                    if path == "/upload":
                        return FakeResponse(
                            {
                                "paper_id": "paper-123",
                                "title": "Attention Is All You Need",
                                "status": "ready",
                                "num_chunks": 7,
                            }
                        )
                    if path == "/ask":
                        return FakeResponse(
                            {
                                "question": json["question"],
                                "answer": "The encoder and decoder both rely on self-attention and feed-forward layers.",
                                "sources": ["methods"],
                                "num_chunks_retrieved": 3,
                                "retrieval_mode": json["retrieval_mode"],
                                "retrieval_scores": [],
                                "evidence": [],
                                "answer_citations": [],
                            }
                        )
                    raise AssertionError(f"Unexpected path: {path}")

            with patch("scripts.run_sample_demo.fetch_sample_package", side_effect=fake_fetch_sample_package), patch(
                "scripts.run_sample_demo.TestClient", FakeTestClient
            ):
                payload = run_sample_demo(
                    package_dir=package_dir,
                    output_dir=output_dir,
                    artifacts_dir=artifacts_dir,
                    question_id="architecture",
                    retrieval_mode="hybrid",
                )

            self.assertEqual(payload["package_id"], "attention-is-all-you-need")
            self.assertEqual(payload["question_id"], "architecture")
            self.assertIn("Transformer encoder and decoder", payload["question"])
            self.assertEqual(payload["upload"]["paper_id"], "paper-123")
            self.assertEqual(payload["answer"]["retrieval_mode"], "hybrid")
            self.assertIn("artifact_path", payload)

            artifact_path = Path(payload["artifact_path"])
            self.assertTrue(artifact_path.exists())
            self.assertEqual(json.loads(artifact_path.read_text(encoding="utf-8"))["question_id"], "architecture")
            self.assertTrue((artifacts_dir / "latest.json").exists())

            calls = FakeTestClient.last_instance.calls
            self.assertEqual([call["path"] for call in calls], ["/upload", "/ask"])
            self.assertEqual(calls[1]["json"]["paper_id"], "paper-123")
            self.assertEqual(calls[1]["json"]["question"], payload["question"])
            self.assertTrue((output_dir / "attention-is-all-you-need.pdf").exists())


if __name__ == "__main__":
    unittest.main()
