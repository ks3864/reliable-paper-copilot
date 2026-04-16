import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.storage import PaperRegistry

try:
    from fastapi.testclient import TestClient
    from src.api import main as api_main
except ModuleNotFoundError:  # pragma: no cover - optional dependency in local tests
    TestClient = None
    api_main = None


class PaperRegistryTests(unittest.TestCase):
    def test_paper_registry_persists_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "papers" / "registry.json"
            registry = PaperRegistry(registry_path)

            record = {
                "paper_id": "paper-1",
                "title": "Example Paper",
                "status": "ready",
                "num_chunks": 4,
                "created_at": "2026-04-16T21:31:00Z",
            }
            registry.upsert_paper(record)

            reloaded = PaperRegistry(registry_path)
            reloaded_record = reloaded.get_paper("paper-1")
            self.assertEqual(reloaded_record["paper_id"], record["paper_id"])
            self.assertFalse(reloaded_record["artifact_validation"]["all_required_present"])
            self.assertEqual(
                reloaded_record["artifact_validation"]["missing_required"],
                ["raw_pdf_path", "parsed_path", "chunks_path"],
            )
            self.assertEqual(reloaded.list_papers(), [reloaded_record])

    def test_paper_registry_reports_artifact_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_path = tmp_path / "paper.pdf"
            parsed_path = tmp_path / "paper_parsed.json"
            chunks_path = tmp_path / "paper_chunks.json"
            raw_path.write_bytes(b"%PDF-1.4")
            parsed_path.write_text("{}", encoding="utf-8")
            chunks_path.write_text('{"chunks": []}', encoding="utf-8")

            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            registry.upsert_paper(
                {
                    "paper_id": "paper-valid",
                    "title": "Validated Paper",
                    "status": "ready",
                    "num_chunks": 0,
                    "raw_pdf_path": str(raw_path),
                    "parsed_path": str(parsed_path),
                    "chunks_path": str(chunks_path),
                    "index_path": str(tmp_path / "missing.faiss"),
                    "created_at": "2026-04-16T21:31:00Z",
                }
            )

            validated = registry.get_paper("paper-valid")
            self.assertTrue(validated["artifact_validation"]["all_required_present"])
            self.assertEqual(validated["artifact_validation"]["missing_required"], [])
            self.assertFalse(validated["artifact_validation"]["artifacts"]["index_path"]["exists"])


@unittest.skipIf(TestClient is None or api_main is None, "fastapi is not installed")
class PaperRegistryApiTests(unittest.TestCase):
    def test_list_and_status_routes_read_from_persistent_registry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = PaperRegistry(Path(tmpdir) / "papers" / "registry.json")
            registry.upsert_paper(
                {
                    "paper_id": "paper-2",
                    "title": "Persistent Paper",
                    "original_filename": "persistent.pdf",
                    "status": "ready",
                    "num_chunks": 7,
                    "page_count": 12,
                    "file_size_bytes": 2048,
                    "created_at": "2026-04-16T21:31:00Z",
                }
            )

            with patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(api_main, "PAPERS", {}):
                client = TestClient(api_main.app)

                papers_response = client.get("/papers")
                self.assertEqual(papers_response.status_code, 200)
                payload = papers_response.json()
                self.assertEqual(payload["total"], 1)
                self.assertEqual(payload["papers"][0]["paper_id"], "paper-2")
                self.assertEqual(payload["papers"][0]["original_filename"], "persistent.pdf")
                self.assertEqual(payload["papers"][0]["page_count"], 12)
                self.assertEqual(payload["papers"][0]["file_size_bytes"], 2048)
                self.assertFalse(payload["papers"][0]["artifact_validation"]["all_required_present"])

                status_response = client.get("/papers/paper-2/status")
                self.assertEqual(status_response.status_code, 200)
                status_payload = status_response.json()
                self.assertEqual(status_payload["paper_id"], "paper-2")
                self.assertEqual(status_payload["title"], "Persistent Paper")
                self.assertEqual(status_payload["status"], "ready")
                self.assertEqual(status_payload["num_chunks"], 7)
                self.assertIn("artifact_validation", status_payload)
                self.assertIn("paper-2", api_main.PAPERS)

    def test_ask_route_can_rebuild_retriever_from_registry_metadata(self):
        class StubGenerator:
            def __init__(self, retriever):
                self.retriever = retriever

            def answer(self, question, top_k=5):
                retrieved_chunks = self.retriever.retrieve(question, top_k=top_k)
                return {
                    "question": question,
                    "answer": "The paper uses the MIMIC-III dataset.",
                    "retrieved_chunks": retrieved_chunks,
                    "sources": [chunk["section"] for chunk in retrieved_chunks],
                    "num_chunks_retrieved": len(retrieved_chunks),
                    "confidence": {"has_good_match": True},
                    "token_usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    "model_version": "stub-generator",
                }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            chunks_path = tmp_path / "paper_chunks.json"
            chunks_path.write_text(
                json.dumps(
                    {
                        "chunks": [
                            {
                                "chunk_id": 0,
                                "section": "methods",
                                "text": "We use the MIMIC-III dataset.",
                                "metadata": {"source": "Persistent Paper"},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            registry.upsert_paper(
                {
                    "paper_id": "paper-ask",
                    "title": "Persistent Paper",
                    "status": "ready",
                    "num_chunks": 1,
                    "chunks_path": str(chunks_path),
                    "index_path": str(tmp_path / "missing.faiss"),
                    "created_at": "2026-04-16T21:31:00Z",
                }
            )

            with patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(api_main, "PAPERS", {}), patch.object(
                api_main, "SimpleAnswerGenerator", StubGenerator
            ):
                client = TestClient(api_main.app)
                response = client.post(
                    "/ask",
                    json={"paper_id": "paper-ask", "question": "What dataset was used?", "top_k": 1},
                )

                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertIn("MIMIC-III", payload["answer"])
                self.assertEqual(payload["sources"], ["methods"])
                self.assertIsNotNone(api_main.PAPERS["paper-ask"]["retriever"])


if __name__ == "__main__":
    unittest.main()
