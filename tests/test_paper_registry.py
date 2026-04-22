import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.storage import (
    PaperRegistry,
    build_ingestion_notes,
    build_provenance_metadata,
    build_summary_metadata,
)

try:
    from fastapi.testclient import TestClient
    from src.api import main as api_main
except ModuleNotFoundError:  # pragma: no cover - optional dependency in local tests
    TestClient = None
    api_main = None


class PaperRegistryTests(unittest.TestCase):
    def test_summary_metadata_includes_extracted_study_signals(self):
        parsed = {
            "metadata": {
                "authors": ["Ada Lovelace", "Grace Hopper"],
                "abstract": "We used the MIMIC-III dataset and enrolled 120 patients.",
            },
            "pages": [
                {
                    "page_number": 1,
                    "word_count": 180,
                    "tables": [{"id": "t1"}],
                }
            ],
        }
        chunks = [
            {
                "section": "methods",
                "text": "We used the MIMIC-III dataset and enrolled 120 patients.",
                "metadata": {"chunking_strategy": "section"},
            },
            {
                "section": "discussion",
                "text": "A key limitation was the single-center design.",
                "metadata": {"chunking_strategy": "section"},
            },
            {
                "section": "participants",
                "text": "Inclusion criteria included adults with confirmed sepsis. Exclusion criteria included prior transplant.",
                "metadata": {"chunking_strategy": "token_fallback"},
            },
        ]

        summary = build_summary_metadata(parsed, chunks)

        self.assertEqual(summary["authors"], ["Ada Lovelace", "Grace Hopper"])
        self.assertEqual(summary["tables_count"], 1)
        self.assertEqual(summary["total_word_count"], 180)
        self.assertEqual(summary["chunking_strategies"], {"section": 2, "token_fallback": 1})
        self.assertEqual(summary["extracted_summary"]["datasets"], ["MIMIC-III"])
        self.assertEqual(summary["extracted_summary"]["sample_sizes"], [120])
        self.assertIn("single-center design", summary["extracted_summary"]["limitations"][0].lower())
        self.assertEqual(summary["extracted_summary"]["inclusion_criteria"], ["Adults with confirmed sepsis"])
        self.assertEqual(summary["extracted_summary"]["exclusion_criteria"], ["Prior transplant"])

    def test_ingestion_notes_include_extracted_metadata_hints(self):
        parsed = {"metadata": {"title": "Example", "abstract": "abstract text"}, "pages": []}
        chunks = [
            {
                "section": "methods",
                "text": "We used the MIMIC-III dataset and enrolled 120 patients.",
                "metadata": {"chunking_strategy": "section"},
            },
            {
                "section": "discussion",
                "text": "A key limitation was the single-center design.",
                "metadata": {"chunking_strategy": "section"},
            },
        ]

        notes = build_ingestion_notes(parsed, chunks, index_persisted=True)

        self.assertTrue(any("MIMIC-III" in note for note in notes))
        self.assertTrue(any("120" in note for note in notes))
        self.assertTrue(any("limitation" in note.lower() for note in notes))

    def test_build_provenance_metadata_sets_operator_edit_defaults(self):
        provenance = build_provenance_metadata(
            original_filename="paper.pdf",
            file_hash="abc123",
            created_at="2026-04-21T22:16:00Z",
        )

        self.assertEqual(provenance["source_type"], "uploaded_pdf")
        self.assertEqual(provenance["source_label"], "paper.pdf")
        self.assertEqual(provenance["file_hash"], "abc123")
        self.assertEqual(provenance["operator_update_count"], 0)
        self.assertIsNone(provenance["last_operator_update_at"])

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
            self.assertEqual(reloaded_record["operator_ingestion_notes"], [])
            self.assertEqual(reloaded_record["provenance"], {})

    def test_paper_registry_updates_operator_notes_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = Path(tmpdir) / "papers" / "registry.json"
            registry = PaperRegistry(registry_path)
            registry.upsert_paper(
                {
                    "paper_id": "paper-editable",
                    "title": "Example Paper",
                    "status": "ready",
                    "num_chunks": 2,
                    "created_at": "2026-04-21T22:16:00Z",
                    "provenance": build_provenance_metadata(
                        original_filename="example.pdf",
                        file_hash="hash-1",
                        created_at="2026-04-21T22:16:00Z",
                    ),
                }
            )

            updated = registry.update_operator_metadata(
                "paper-editable",
                operator_ingestion_notes=["Needs manual title verification", "  "],
                provenance={
                    "source_label": "Nature PDF export",
                    "citation_hint": "Nature 2024 supplementary appendix",
                    "source_url": "https://example.com/paper",
                    "last_operator_update_at": "2026-04-21T23:00:00Z",
                    "last_operator_update_source": "web-ui",
                    "operator_update_count": 1,
                    "uploaded_via": "should-not-change",
                },
            )

            self.assertEqual(updated["operator_ingestion_notes"], ["Needs manual title verification"])
            self.assertEqual(updated["provenance"]["source_label"], "Nature PDF export")
            self.assertEqual(updated["provenance"]["citation_hint"], "Nature 2024 supplementary appendix")
            self.assertEqual(updated["provenance"]["source_url"], "https://example.com/paper")
            self.assertEqual(updated["provenance"]["last_operator_update_source"], "web-ui")
            self.assertEqual(updated["provenance"]["operator_update_count"], 1)
            self.assertEqual(updated["provenance"]["uploaded_via"], "api_upload")

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
                    "operator_ingestion_notes": ["Flag missing appendix links"],
                    "provenance": {
                        "source_type": "uploaded_pdf",
                        "source_label": "Persistent import",
                        "uploaded_via": "api_upload",
                    },
                    "summary_metadata": {
                        "extracted_summary": {
                            "datasets": ["MIMIC-III"],
                            "sample_sizes": [120],
                        }
                    },
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
                self.assertEqual(payload["papers"][0]["summary_metadata"]["extracted_summary"]["datasets"], ["MIMIC-III"])
                self.assertEqual(payload["papers"][0]["operator_ingestion_notes"], ["Flag missing appendix links"])
                self.assertEqual(payload["papers"][0]["provenance"]["source_label"], "Persistent import")

                status_response = client.get("/papers/paper-2/status")
                self.assertEqual(status_response.status_code, 200)
                status_payload = status_response.json()
                self.assertEqual(status_payload["paper_id"], "paper-2")
                self.assertEqual(status_payload["title"], "Persistent Paper")
                self.assertEqual(status_payload["status"], "ready")
                self.assertEqual(status_payload["num_chunks"], 7)
                self.assertIn("artifact_validation", status_payload)
                self.assertEqual(status_payload["summary_metadata"]["extracted_summary"]["sample_sizes"], [120])
                self.assertEqual(status_payload["operator_ingestion_notes"], ["Flag missing appendix links"])
                self.assertEqual(status_payload["provenance"]["source_label"], "Persistent import")
                self.assertIn("paper-2", api_main.PAPERS)

    def test_metadata_patch_route_updates_operator_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = PaperRegistry(Path(tmpdir) / "papers" / "registry.json")
            registry.upsert_paper(
                {
                    "paper_id": "paper-edit",
                    "title": "Editable Paper",
                    "status": "ready",
                    "num_chunks": 3,
                    "created_at": "2026-04-16T21:31:00Z",
                    "provenance": {
                        "source_type": "uploaded_pdf",
                        "source_label": "Initial label",
                        "uploaded_via": "api_upload",
                        "operator_update_count": 0,
                    },
                }
            )

            with patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(
                api_main,
                "PAPERS",
                {"paper-edit": {"paper_id": "paper-edit", "status": "ready", "num_chunks": 3}},
            ):
                client = TestClient(api_main.app)
                response = client.patch(
                    "/papers/paper-edit/metadata",
                    json={
                        "operator_ingestion_notes": ["Needs provenance confirmation"],
                        "provenance": {
                            "source_label": "Curated arXiv export",
                            "source_url": "https://arxiv.org/abs/1234.5678",
                            "last_operator_update_at": "2026-04-21T23:15:00Z",
                            "last_operator_update_source": "api-test",
                            "operator_update_count": 1,
                        },
                    },
                )

                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual(payload["operator_ingestion_notes"], ["Needs provenance confirmation"])
                self.assertEqual(payload["provenance"]["source_label"], "Curated arXiv export")
                self.assertEqual(payload["provenance"]["source_url"], "https://arxiv.org/abs/1234.5678")
                self.assertEqual(payload["provenance"]["last_operator_update_source"], "api-test")
                self.assertEqual(api_main.PAPERS["paper-edit"]["operator_ingestion_notes"], ["Needs provenance confirmation"])

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
                self.assertEqual(payload["retrieval_mode"], "dense")
                self.assertEqual(payload["retrieval_scores"][0]["section"], "methods")
                self.assertIn("retrieval_score", payload["retrieval_scores"][0])
                self.assertEqual(payload["evidence"][0]["section"], "methods")
                self.assertIsNotNone(api_main.PAPERS["paper-ask"]["retriever"])

    def test_ask_returns_page_aware_evidence(self):
        class StubGenerator:
            def __init__(self, retriever):
                self.retriever = retriever

            def answer(self, question, top_k=5):
                chunks = self.retriever.retrieve(question, top_k=top_k)
                return {
                    "question": question,
                    "answer": "The evidence is on pages 3 and 4.",
                    "sources": [chunk["section"] for chunk in chunks],
                    "retrieved_chunks": chunks,
                    "num_chunks_retrieved": len(chunks),
                    "confidence": {"has_good_match": True},
                    "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
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
                                "chunk_id": 7,
                                "section": "results",
                                "text": "The main finding appears in the paged evidence snippet.",
                                "metadata": {
                                    "source": "Persistent Paper",
                                    "page_numbers": [3, 4],
                                    "page_start": 3,
                                    "page_end": 4,
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            registry.upsert_paper(
                {
                    "paper_id": "paper-evidence",
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
                    json={"paper_id": "paper-evidence", "question": "Where is the main finding?", "top_k": 1},
                )

                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual(payload["evidence"][0]["chunk_id"], 7)
                self.assertEqual(payload["evidence"][0]["page_numbers"], [3, 4])
                self.assertEqual(payload["evidence"][0]["page_label"], "pp. 3-4")
                self.assertEqual(payload["evidence"][0]["text"], "The main finding appears in the paged evidence snippet.")
                self.assertEqual(len(payload["answer_citations"]), 1)
                self.assertEqual(payload["answer_citations"][0]["chunk_id"], 7)
                self.assertEqual(payload["answer_citations"][0]["section"], "results")
                self.assertEqual(payload["answer_citations"][0]["page_label"], "pp. 3-4")
                self.assertEqual(payload["answer_citations"][0]["label"], "[1]")

    def test_ask_supports_hybrid_retrieval_request_settings(self):
        class StubGenerator:
            def __init__(self, retriever):
                self.retriever = retriever

            def answer(self, question, top_k=5):
                chunks = self.retriever.retrieve(question, top_k=top_k)
                return {
                    "question": question,
                    "answer": "Hybrid answer",
                    "sources": [chunk["section"] for chunk in chunks],
                    "retrieved_chunks": chunks,
                    "num_chunks_retrieved": len(chunks),
                    "confidence": {"has_good_match": True},
                    "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
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
                                "text": "Dataset construction details for the medical cohort.",
                                "metadata": {"source": "Persistent Paper"},
                            },
                            {
                                "chunk_id": 1,
                                "section": "results",
                                "text": "Benchmark dataset performance is summarized here.",
                                "metadata": {"source": "Persistent Paper"},
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            registry.upsert_paper(
                {
                    "paper_id": "paper-hybrid",
                    "title": "Persistent Paper",
                    "status": "ready",
                    "num_chunks": 2,
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
                    json={
                        "paper_id": "paper-hybrid",
                        "question": "What dataset was used?",
                        "top_k": 2,
                        "retrieval_mode": "hybrid",
                        "lexical_weight": 1.2,
                        "dense_weight": 0.8,
                        "rrf_k": 30,
                    },
                )

                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual(payload["retrieval_mode"], "hybrid")
                self.assertIn("hybrid_score", payload["retrieval_scores"][0])
                self.assertIn("lexical_score", payload["retrieval_scores"][0])
                self.assertIsNone(api_main.PAPERS["paper-hybrid"].get("retriever"))


if __name__ == "__main__":
    unittest.main()
