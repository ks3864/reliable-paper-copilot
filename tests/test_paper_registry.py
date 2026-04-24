import json
import os
import tempfile
import unittest
from contextlib import contextmanager
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


@contextmanager
def temporary_cwd(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


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

    def test_build_provenance_metadata_accepts_upload_time_overrides(self):
        provenance = build_provenance_metadata(
            original_filename="paper.pdf",
            file_hash="abc123",
            created_at="2026-04-21T22:16:00Z",
            source_label="Curated benchmark PDF",
            source_url=" https://example.com/paper ",
            citation_hint=" Camera-ready appendix ",
        )

        self.assertEqual(provenance["source_label"], "Curated benchmark PDF")
        self.assertEqual(provenance["source_url"], "https://example.com/paper")
        self.assertEqual(provenance["citation_hint"], "Camera-ready appendix")

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
            self.assertEqual(len(updated["operator_metadata_history"]), 1)
            self.assertEqual(updated["operator_metadata_history"][0]["source"], "web-ui")
            self.assertEqual(updated["operator_metadata_history"][0]["source_label"], "Nature PDF export")

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

    def test_paper_registry_can_delete_record_and_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_path = tmp_path / "paper.pdf"
            parsed_path = tmp_path / "paper_parsed.json"
            chunks_path = tmp_path / "paper_chunks.json"
            index_path = tmp_path / "paper_index.faiss"
            raw_path.write_bytes(b"%PDF-1.4")
            parsed_path.write_text("{}", encoding="utf-8")
            chunks_path.write_text('{"chunks": []}', encoding="utf-8")
            index_path.write_bytes(b"index")

            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            registry.upsert_paper(
                {
                    "paper_id": "paper-delete",
                    "title": "Delete Me",
                    "status": "ready",
                    "num_chunks": 0,
                    "raw_pdf_path": str(raw_path),
                    "parsed_path": str(parsed_path),
                    "chunks_path": str(chunks_path),
                    "index_path": str(index_path),
                    "created_at": "2026-04-22T20:16:00Z",
                }
            )

            deleted = registry.delete_paper("paper-delete")

            self.assertIsNotNone(deleted)
            self.assertEqual(deleted["paper_id"], "paper-delete")
            self.assertIsNone(registry.get_paper("paper-delete"))
            self.assertFalse(raw_path.exists())
            self.assertFalse(parsed_path.exists())
            self.assertFalse(chunks_path.exists())
            self.assertFalse(index_path.exists())


@unittest.skipIf(TestClient is None or api_main is None, "fastapi is not installed")
class PaperRegistryApiTests(unittest.TestCase):
    def test_upload_route_smoke_persists_artifacts_and_registry_metadata(self):
        class StubRetriever:
            def __init__(self):
                self.index = None
                self.use_lexical_fallback = True

        parsed = {
            "metadata": {
                "title": "Smoke Tested Paper",
                "authors": ["Ada Lovelace"],
                "abstract": "We evaluated the MIMIC-III cohort with 120 patients.",
                "page_count": 1,
            },
            "pages": [
                {
                    "page_number": 1,
                    "text": "Abstract\nWe evaluated the MIMIC-III cohort with 120 patients.",
                    "tables": [],
                    "word_count": 10,
                }
            ],
        }
        chunks = [
            {
                "chunk_id": 0,
                "section": "abstract",
                "text": "We evaluated the MIMIC-III cohort with 120 patients.",
                "metadata": {
                    "source": "Smoke Tested Paper",
                    "chunking_strategy": "section",
                    "page_numbers": [1],
                    "page_start": 1,
                    "page_end": 1,
                },
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            paper_cache = {}

            with temporary_cwd(tmp_path), patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(
                api_main, "PAPERS", paper_cache
            ), patch.object(api_main, "parse_pdf", return_value=parsed), patch.object(
                api_main, "chunk_by_sections", return_value=chunks
            ), patch.object(api_main, "create_retriever", return_value=StubRetriever()):
                client = TestClient(api_main.app)
                response = client.post(
                    "/upload",
                    files={"file": ("smoke-paper.pdf", b"%PDF-1.4\n%stub pdf bytes\n", "application/pdf")},
                    data={
                        "source_label": "arXiv curated upload",
                        "source_url": "https://arxiv.org/abs/1234.5678",
                        "citation_hint": "arXiv v3 PDF",
                    },
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["title"], "Smoke Tested Paper")
            self.assertEqual(payload["status"], "ready")
            self.assertEqual(payload["num_chunks"], 1)
            self.assertTrue(any("MIMIC-III" in note for note in payload["ingestion_notes"]))
            self.assertEqual(payload["summary_metadata"]["extracted_summary"]["sample_sizes"], [120])

            stored_record = registry.get_paper(payload["paper_id"])
            self.assertIsNotNone(stored_record)
            self.assertTrue(Path(stored_record["raw_pdf_path"]).exists())
            self.assertTrue(Path(stored_record["parsed_path"]).exists())
            self.assertTrue(Path(stored_record["chunks_path"]).exists())
            self.assertEqual(stored_record["original_filename"], "smoke-paper.pdf")
            self.assertEqual(stored_record["file_size_bytes"], len(b"%PDF-1.4\n%stub pdf bytes\n"))
            self.assertEqual(stored_record["summary_metadata"]["authors"], ["Ada Lovelace"])
            self.assertEqual(stored_record["provenance"]["source_label"], "arXiv curated upload")
            self.assertEqual(stored_record["provenance"]["source_url"], "https://arxiv.org/abs/1234.5678")
            self.assertEqual(stored_record["provenance"]["citation_hint"], "arXiv v3 PDF")
            self.assertEqual(payload["provenance"]["source_label"], "arXiv curated upload")
            self.assertFalse(Path(stored_record["index_path"]).exists())
            self.assertIn(payload["paper_id"], paper_cache)

    def test_upload_route_rejects_non_pdf_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = PaperRegistry(Path(tmpdir) / "papers" / "registry.json")
            with temporary_cwd(Path(tmpdir)), patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(
                api_main, "PAPERS", {}
            ):
                client = TestClient(api_main.app)
                response = client.post(
                    "/upload",
                    files={"file": ("notes.txt", b"not a pdf", "text/plain")},
                )

            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["detail"], "File must be a PDF")
            self.assertEqual(registry.list_papers(), [])

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

                brief_response = client.get("/papers/paper-2/brief")
                self.assertEqual(brief_response.status_code, 200)
                brief_payload = brief_response.json()
                self.assertEqual(brief_payload["paper_id"], "paper-2")
                self.assertEqual(brief_payload["overview"]["page_count"], 12)
                self.assertEqual(brief_payload["overview"]["num_chunks"], 7)
                self.assertEqual(brief_payload["study_signals"]["datasets"], ["MIMIC-III"])
                self.assertEqual(brief_payload["study_signals"]["sample_sizes"], [120])
                self.assertEqual(
                    brief_payload["ingestion"]["operator_ingestion_notes"],
                    ["Flag missing appendix links"],
                )
                self.assertEqual(
                    brief_payload["ingestion"]["provenance"]["source_label"],
                    "Persistent import",
                )

                brief_export_response = client.get("/papers/paper-2/brief/export")
                self.assertEqual(brief_export_response.status_code, 200)
                self.assertIn("text/markdown", brief_export_response.headers["content-type"])
                self.assertIn("# Persistent Paper", brief_export_response.text)
                self.assertIn("- Paper ID: paper-2", brief_export_response.text)
                self.assertIn("### Datasets", brief_export_response.text)
                self.assertIn("- MIMIC-III", brief_export_response.text)
                self.assertIn("### Operator notes", brief_export_response.text)
                self.assertIn("- Flag missing appendix links", brief_export_response.text)

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
                self.assertEqual(len(payload["operator_metadata_history"]), 1)
                self.assertEqual(payload["operator_metadata_history"][0]["source"], "api-test")
                self.assertEqual(api_main.PAPERS["paper-edit"]["operator_ingestion_notes"], ["Needs provenance confirmation"])
                self.assertEqual(len(api_main.PAPERS["paper-edit"]["operator_metadata_history"]), 1)

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

    def test_end_to_end_api_workflow_covers_upload_ask_and_status(self):
        class StubRetriever:
            def __init__(self, chunks):
                self.index = None
                self.use_lexical_fallback = True
                self.retrieval_mode = "dense"
                self._chunks = chunks

            def retrieve(self, query, top_k=5):
                selected = []
                for rank, chunk in enumerate(self._chunks[:top_k], start=1):
                    hydrated = dict(chunk)
                    hydrated["retrieval_score"] = 0.9 / rank
                    hydrated["rank"] = rank
                    selected.append(hydrated)
                return selected

        class StubGenerator:
            def __init__(self, retriever):
                self.retriever = retriever

            def answer(self, question, top_k=5):
                retrieved_chunks = self.retriever.retrieve(question, top_k=top_k)
                return {
                    "question": question,
                    "answer": "The study uses the MIMIC-III dataset and enrolled 120 patients.",
                    "sources": [chunk["section"] for chunk in retrieved_chunks],
                    "retrieved_chunks": retrieved_chunks,
                    "num_chunks_retrieved": len(retrieved_chunks),
                    "confidence": {"has_good_match": True},
                    "token_usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
                    "model_version": "stub-generator",
                }

        parsed = {
            "metadata": {
                "title": "End-to-End Workflow Paper",
                "authors": ["Ada Lovelace"],
                "abstract": "We evaluated the MIMIC-III dataset with 120 patients.",
                "page_count": 2,
            },
            "pages": [
                {
                    "page_number": 1,
                    "text": "Abstract\nWe evaluated the MIMIC-III dataset with 120 patients.",
                    "tables": [],
                    "word_count": 10,
                },
                {
                    "page_number": 2,
                    "text": "Results\nPerformance improved across cohorts.",
                    "tables": [],
                    "word_count": 8,
                },
            ],
        }
        chunks = [
            {
                "chunk_id": 0,
                "section": "abstract",
                "text": "We evaluated the MIMIC-III dataset with 120 patients.",
                "metadata": {
                    "source": "End-to-End Workflow Paper",
                    "chunking_strategy": "section",
                    "page_numbers": [1],
                    "page_start": 1,
                    "page_end": 1,
                },
            },
            {
                "chunk_id": 1,
                "section": "results",
                "text": "Performance improved across cohorts.",
                "metadata": {
                    "source": "End-to-End Workflow Paper",
                    "chunking_strategy": "section",
                    "page_numbers": [2],
                    "page_start": 2,
                    "page_end": 2,
                },
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            request_logger = api_main.RequestLogger(tmp_path / "logs" / "requests.jsonl")

            with temporary_cwd(tmp_path), patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(
                api_main, "PAPERS", {}
            ), patch.object(api_main, "REQUEST_LOGGER", request_logger), patch.object(
                api_main, "parse_pdf", return_value=parsed
            ), patch.object(api_main, "chunk_by_sections", return_value=chunks), patch.object(
                api_main, "create_retriever", side_effect=lambda prepared_chunks, **_: StubRetriever(prepared_chunks)
            ), patch.object(api_main, "SimpleAnswerGenerator", StubGenerator):
                client = TestClient(api_main.app)

                upload_response = client.post(
                    "/upload",
                    files={"file": ("workflow-paper.pdf", b"%PDF-1.4\n%workflow pdf bytes\n", "application/pdf")},
                )
                self.assertEqual(upload_response.status_code, 200)
                upload_payload = upload_response.json()
                paper_id = upload_payload["paper_id"]
                self.assertEqual(upload_payload["title"], "End-to-End Workflow Paper")
                self.assertEqual(upload_payload["status"], "ready")
                self.assertEqual(upload_payload["num_chunks"], 2)

                ask_response = client.post(
                    "/ask",
                    json={"paper_id": paper_id, "question": "What dataset was used?", "top_k": 2},
                )
                self.assertEqual(ask_response.status_code, 200)
                ask_payload = ask_response.json()
                self.assertIn("MIMIC-III", ask_payload["answer"])
                self.assertEqual(ask_payload["sources"], ["abstract", "results"])
                self.assertEqual(ask_payload["num_chunks_retrieved"], 2)
                self.assertEqual(ask_payload["retrieval_mode"], "dense")
                self.assertEqual(ask_payload["evidence"][0]["page_label"], "p. 1")
                self.assertEqual(ask_payload["answer_citations"][0]["chunk_id"], 0)

                status_response = client.get(f"/papers/{paper_id}/status")
                self.assertEqual(status_response.status_code, 200)
                status_payload = status_response.json()
                self.assertEqual(status_payload["paper_id"], paper_id)
                self.assertEqual(status_payload["status"], "ready")
                self.assertEqual(status_payload["summary_metadata"]["extracted_summary"]["datasets"], ["MIMIC-III"])

                papers_response = client.get("/papers")
                self.assertEqual(papers_response.status_code, 200)
                papers_payload = papers_response.json()
                self.assertEqual(papers_payload["total"], 1)
                self.assertEqual(papers_payload["papers"][0]["paper_id"], paper_id)

            log_lines = request_logger.log_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(log_lines), 1)
            logged_event = json.loads(log_lines[0])
            self.assertEqual(logged_event["endpoint"], "/ask")
            self.assertEqual(logged_event["paper_id"], paper_id)
            self.assertEqual(logged_event["extra"]["num_chunks_retrieved"], 2)

    def test_delete_route_removes_registry_record_cache_and_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_path = tmp_path / "paper.pdf"
            parsed_path = tmp_path / "paper_parsed.json"
            chunks_path = tmp_path / "paper_chunks.json"
            index_path = tmp_path / "paper_index.faiss"
            raw_path.write_bytes(b"%PDF-1.4")
            parsed_path.write_text("{}", encoding="utf-8")
            chunks_path.write_text('{"chunks": []}', encoding="utf-8")
            index_path.write_bytes(b"index")

            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            registry.upsert_paper(
                {
                    "paper_id": "paper-delete-api",
                    "title": "Delete API Paper",
                    "status": "ready",
                    "num_chunks": 0,
                    "raw_pdf_path": str(raw_path),
                    "parsed_path": str(parsed_path),
                    "chunks_path": str(chunks_path),
                    "index_path": str(index_path),
                    "created_at": "2026-04-22T20:16:00Z",
                }
            )

            cached_papers = {
                "paper-delete-api": {
                    "paper_id": "paper-delete-api",
                    "status": "ready",
                    "num_chunks": 0,
                }
            }

            with patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(api_main, "PAPERS", cached_papers):
                client = TestClient(api_main.app)
                response = client.delete("/papers/paper-delete-api")

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["paper_id"], "paper-delete-api")
            self.assertTrue(payload["deleted"])
            self.assertIn("raw_pdf_path", payload["deleted_artifacts"])
            self.assertIsNone(registry.get_paper("paper-delete-api"))
            self.assertNotIn("paper-delete-api", cached_papers)
            self.assertFalse(raw_path.exists())
            self.assertFalse(parsed_path.exists())
            self.assertFalse(chunks_path.exists())
            self.assertFalse(index_path.exists())

    def test_activity_route_returns_recent_question_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            request_logger = api_main.RequestLogger(log_dir=tmp_path / "logs")
            registry.upsert_paper(
                {
                    "paper_id": "paper-activity-api",
                    "title": "Activity API Paper",
                    "status": "ready",
                    "num_chunks": 2,
                    "created_at": "2026-04-22T20:16:00Z",
                }
            )

            request_logger.log(
                request_logger.create_event(
                    endpoint="/ask",
                    paper_id="paper-activity-api",
                    question="What dataset was used?",
                    latency_ms=14.5,
                    token_usage={"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
                    model_version="demo-model-v1",
                    extra={
                        "num_chunks_retrieved": 3,
                        "has_good_match": True,
                        "sources": ["methods"],
                        "answer_preview": "The paper uses the MIMIC-III cohort for experiments.",
                        "evidence_labels": ["methods (p. 4)", "appendix (p. 12)"],
                        "retrieval_mode": "hybrid",
                        "top_k": 5,
                        "dense_weight": 1.2,
                        "lexical_weight": 0.8,
                        "rrf_k": 50,
                    },
                )
            )

            with patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(
                api_main, "PAPERS", {}
            ), patch.object(api_main, "REQUEST_LOGGER", request_logger):
                client = TestClient(api_main.app)
                response = client.get("/papers/paper-activity-api/activity?limit=5")

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertIn("summary", payload)
            self.assertIn("items", payload)
            self.assertEqual(payload["summary"]["question_count"], 1)
            self.assertEqual(payload["summary"]["average_latency_ms"], 14.5)
            self.assertEqual(payload["summary"]["good_match_count"], 1)
            self.assertEqual(payload["summary"]["good_match_rate"], 1.0)
            self.assertEqual(payload["summary"]["good_match_rate_label"], "1/1 (100%)")
            self.assertEqual(payload["summary"]["retrieval_modes"], {"hybrid": 1})
            self.assertEqual(payload["summary"]["retrieval_modes_label"], "hybrid (1)")
            self.assertEqual(payload["summary"]["total_tokens"], 6)
            self.assertEqual(len(payload["items"]), 1)
            self.assertEqual(payload["items"][0]["question"], "What dataset was used?")
            self.assertEqual(payload["items"][0]["answer_preview"], "The paper uses the MIMIC-III cohort for experiments.")
            self.assertEqual(payload["items"][0]["evidence_labels"], ["methods (p. 4)", "appendix (p. 12)"])
            self.assertEqual(payload["items"][0]["num_chunks_retrieved"], 3)
            self.assertTrue(payload["items"][0]["has_good_match"])
            self.assertEqual(payload["items"][0]["sources"], ["methods"])
            self.assertEqual(payload["items"][0]["retrieval_mode"], "hybrid")
            self.assertEqual(payload["items"][0]["top_k"], 5)
            self.assertEqual(payload["items"][0]["dense_weight"], 1.2)
            self.assertEqual(payload["items"][0]["lexical_weight"], 0.8)
            self.assertEqual(payload["items"][0]["rrf_k"], 50)

    def test_papers_summary_route_returns_aggregate_library_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            registry.upsert_paper(
                {
                    "paper_id": "paper-summary-1",
                    "title": "Earlier Paper",
                    "status": "processing",
                    "num_chunks": 4,
                    "page_count": 6,
                    "file_size_bytes": 2048,
                    "created_at": "2026-04-22T20:16:00Z",
                    "operator_ingestion_notes": [],
                }
            )
            registry.upsert_paper(
                {
                    "paper_id": "paper-summary-2",
                    "title": "Latest Paper",
                    "status": "ready",
                    "num_chunks": 7,
                    "page_count": 9,
                    "file_size_bytes": 4096,
                    "created_at": "2026-04-23T20:16:00Z",
                    "operator_ingestion_notes": ["Use for the main demo"],
                }
            )

            with patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(api_main, "PAPERS", {}):
                client = TestClient(api_main.app)
                response = client.get("/papers/summary")

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["total_papers"], 2)
            self.assertEqual(payload["ready_papers"], 1)
            self.assertEqual(payload["papers_with_operator_notes"], 1)
            self.assertEqual(payload["total_pages"], 15)
            self.assertEqual(payload["total_chunks"], 11)
            self.assertEqual(payload["total_file_size_bytes"], 6144)
            self.assertEqual(payload["latest_paper_id"], "paper-summary-2")
            self.assertEqual(payload["latest_paper_title"], "Latest Paper")
            self.assertEqual(payload["latest_created_at"], "2026-04-23T20:16:00Z")

    def test_activity_export_route_returns_markdown_transcript(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            request_logger = api_main.RequestLogger(log_dir=tmp_path / "logs")
            registry.upsert_paper(
                {
                    "paper_id": "paper-activity-export",
                    "title": "Exportable Activity Paper",
                    "original_filename": "exportable.pdf",
                    "status": "ready",
                    "num_chunks": 2,
                    "created_at": "2026-04-22T20:16:00Z",
                    "provenance": {"source_label": "Demo upload"},
                }
            )

            request_logger.log(
                request_logger.create_event(
                    endpoint="/ask",
                    paper_id="paper-activity-export",
                    question="What limitation did the authors mention?",
                    latency_ms=18.25,
                    token_usage={"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17},
                    model_version="demo-model-v2",
                    extra={
                        "num_chunks_retrieved": 4,
                        "has_good_match": False,
                        "sources": ["discussion", "limitations"],
                        "answer_preview": "The authors note that the cohort is small and from a single site.",
                        "evidence_labels": ["discussion (p. 8)", "limitations (p. 9)"],
                        "retrieval_mode": "hybrid",
                        "top_k": 4,
                        "dense_weight": 1.0,
                        "lexical_weight": 1.3,
                        "rrf_k": 60,
                    },
                )
            )

            with patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(
                api_main, "PAPERS", {}
            ), patch.object(api_main, "REQUEST_LOGGER", request_logger):
                client = TestClient(api_main.app)
                response = client.get("/papers/paper-activity-export/activity/export?limit=5")

            self.assertEqual(response.status_code, 200)
            self.assertIn("text/markdown", response.headers["content-type"])
            self.assertIn("# Recent activity transcript for Exportable Activity Paper", response.text)
            self.assertIn("- Paper ID: paper-activity-export", response.text)
            self.assertIn("## Activity summary", response.text)
            self.assertIn("- Questions included: 1", response.text)
            self.assertIn("- Average latency: 18.25 ms", response.text)
            self.assertIn("- Good-match rate: 0/1 (0%)", response.text)
            self.assertIn("- Retrieval modes: hybrid (1)", response.text)
            self.assertIn("- Total tokens: 17", response.text)
            self.assertIn("### 1. What limitation did the authors mention?", response.text)
            self.assertIn("- Match status: Fallback or weak retrieval match", response.text)
            self.assertIn("- Retrieval config: mode=hybrid, top_k=4, dense_weight=1.00, lexical_weight=1.30, rrf_k=60", response.text)
            self.assertIn("- Token usage: prompt=12, completion=5, total=17", response.text)
            self.assertIn("- Sources: discussion, limitations", response.text)
            self.assertIn("- Answer preview: The authors note that the cohort is small and from a single site.", response.text)
            self.assertIn("- Evidence cues: discussion (p. 8), limitations (p. 9)", response.text)

    def test_delete_activity_route_clears_only_matching_ask_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            request_logger = api_main.RequestLogger(log_dir=tmp_path / "logs")
            registry.upsert_paper(
                {
                    "paper_id": "paper-activity-reset",
                    "title": "Resettable Activity Paper",
                    "status": "ready",
                    "num_chunks": 2,
                    "created_at": "2026-04-23T18:45:00Z",
                }
            )

            request_logger.log(
                request_logger.create_event(
                    endpoint="/ask",
                    paper_id="paper-activity-reset",
                    question="Delete this question",
                    latency_ms=14.5,
                    token_usage={"prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
                    model_version="demo-model-v3",
                )
            )
            request_logger.log(
                request_logger.create_event(
                    endpoint="/health",
                    paper_id="paper-activity-reset",
                    question=None,
                    latency_ms=1.0,
                    token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    model_version="demo-model-v3",
                )
            )
            request_logger.log(
                request_logger.create_event(
                    endpoint="/ask",
                    paper_id="paper-activity-other",
                    question="Keep this other paper question",
                    latency_ms=9.0,
                    token_usage={"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
                    model_version="demo-model-v3",
                )
            )

            with patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(
                api_main, "PAPERS", {}
            ), patch.object(api_main, "REQUEST_LOGGER", request_logger):
                client = TestClient(api_main.app)
                response = client.delete("/papers/paper-activity-reset/activity")

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["paper_id"], "paper-activity-reset")
            self.assertTrue(payload["deleted"])
            self.assertEqual(payload["deleted_events"], 1)
            self.assertEqual(payload["remaining_events"], 0)
            self.assertEqual(
                request_logger.read_events(paper_id="paper-activity-reset", endpoint="/ask", limit=5),
                [],
            )
            self.assertEqual(
                len(request_logger.read_events(paper_id="paper-activity-other", endpoint="/ask", limit=5)),
                1,
            )
            self.assertEqual(
                len(request_logger.read_events(paper_id="paper-activity-reset", endpoint="/health", limit=5)),
                1,
            )

    def test_metadata_history_export_route_returns_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            registry.upsert_paper(
                {
                    "paper_id": "paper-metadata-export",
                    "title": "Metadata Export Paper",
                    "original_filename": "metadata-export.pdf",
                    "status": "ready",
                    "num_chunks": 2,
                    "created_at": "2026-04-23T18:45:00Z",
                    "operator_ingestion_notes": ["Most recent operator note"],
                    "provenance": {
                        "source_label": "Curated metadata paper",
                        "source_url": "https://example.com/metadata-paper.pdf",
                        "citation_hint": "Workshop version",
                        "operator_update_count": 2,
                    },
                    "operator_metadata_history": [
                        {
                            "timestamp": "2026-04-23T18:40:00Z",
                            "source": "api",
                            "operator_update_count": 1,
                            "operator_ingestion_notes": ["Initial triage note"],
                            "source_label": "Initial upload label",
                            "source_url": None,
                            "citation_hint": None,
                        },
                        {
                            "timestamp": "2026-04-23T18:44:00Z",
                            "source": "web-ui",
                            "operator_update_count": 2,
                            "operator_ingestion_notes": ["Most recent operator note"],
                            "source_label": "Curated metadata paper",
                            "source_url": "https://example.com/metadata-paper.pdf",
                            "citation_hint": "Workshop version",
                        },
                    ],
                }
            )

            with patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(api_main, "PAPERS", {}):
                client = TestClient(api_main.app)
                response = client.get("/papers/paper-metadata-export/metadata/history/export?limit=1")

            self.assertEqual(response.status_code, 200)
            self.assertIn("text/markdown", response.headers["content-type"])
            self.assertIn("# Operator metadata history for Metadata Export Paper", response.text)
            self.assertIn("- Paper ID: paper-metadata-export", response.text)
            self.assertIn("- Current source label: Curated metadata paper", response.text)
            self.assertIn("- Operator update count: 2", response.text)
            self.assertIn("- Included history items: 1", response.text)
            self.assertIn("## Saved edits", response.text)
            self.assertIn("### 1. Update 2", response.text)
            self.assertIn("- Timestamp: 2026-04-23T18:44:00Z", response.text)
            self.assertIn("- Source: web-ui", response.text)
            self.assertIn("- Source label: Curated metadata paper", response.text)
            self.assertIn("- Source URL: https://example.com/metadata-paper.pdf", response.text)
            self.assertIn("- Citation hint: Workshop version", response.text)
            self.assertIn("- Operator notes: Most recent operator note", response.text)
            self.assertNotIn("Initial triage note", response.text)

    def test_demo_recap_export_route_combines_brief_and_activity_sections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry = PaperRegistry(tmp_path / "papers" / "registry.json")
            request_logger = api_main.RequestLogger(log_dir=tmp_path / "logs")
            registry.upsert_paper(
                {
                    "paper_id": "paper-demo-recap",
                    "title": "Demo Recap Paper",
                    "original_filename": "demo-recap.pdf",
                    "status": "ready",
                    "num_chunks": 6,
                    "page_count": 9,
                    "created_at": "2026-04-23T18:45:00Z",
                    "artifact_validation": {
                        "all_required_present": True,
                        "missing_required": [],
                    },
                    "operator_ingestion_notes": ["Use for stakeholder walkthroughs"],
                    "provenance": {
                        "source_label": "Curated demo paper",
                        "uploaded_via": "api_upload",
                        "source_url": "https://example.com/demo-recap.pdf",
                    },
                    "summary_metadata": {
                        "authors": ["Ada Lovelace", "Grace Hopper"],
                        "abstract_preview": "This paper evaluates a reproducible retrieval pipeline.",
                        "section_count": 4,
                        "section_names": ["abstract", "methods", "results", "discussion"],
                        "total_word_count": 1500,
                        "tables_count": 2,
                        "chunking_strategies": {"primary": "section-aware"},
                        "extracted_summary": {
                            "datasets": ["DemoSet"],
                            "sample_sizes": [64],
                            "limitations": ["Single-center cohort"],
                            "inclusion_criteria": ["Adults over 18"],
                            "exclusion_criteria": ["Missing baseline labs"],
                            "counts": {"datasets": 1, "limitations": 1},
                        },
                    },
                }
            )

            request_logger.log(
                request_logger.create_event(
                    endpoint="/ask",
                    paper_id="paper-demo-recap",
                    question="What dataset was used?",
                    latency_ms=14.5,
                    token_usage={"prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
                    model_version="demo-model-v3",
                    extra={
                        "num_chunks_retrieved": 3,
                        "has_good_match": True,
                        "sources": ["methods"],
                        "answer_preview": "The study used the DemoSet benchmark.",
                        "evidence_labels": ["methods (p. 3)"],
                        "retrieval_mode": "hybrid",
                        "top_k": 3,
                        "dense_weight": 1.0,
                        "lexical_weight": 1.2,
                        "rrf_k": 60,
                    },
                )
            )

            with patch.object(api_main, "PAPER_REGISTRY", registry), patch.object(
                api_main, "PAPERS", {}
            ), patch.object(api_main, "REQUEST_LOGGER", request_logger):
                client = TestClient(api_main.app)
                response = client.get("/papers/paper-demo-recap/demo-recap/export?activity_limit=5")

            self.assertEqual(response.status_code, 200)
            self.assertIn("text/markdown", response.headers["content-type"])
            self.assertIn("# Demo Recap Paper", response.text)
            self.assertIn("## Overview", response.text)
            self.assertIn("### Datasets", response.text)
            self.assertIn("- DemoSet", response.text)
            self.assertIn("## Demo recap", response.text)
            self.assertIn("## Recent activity transcript for Demo Recap Paper", response.text)
            self.assertIn("### Activity summary", response.text)
            self.assertIn("### Activity", response.text)
            self.assertIn("#### 1. What dataset was used?", response.text)
            self.assertIn("- Source label: Curated demo paper", response.text)
            self.assertIn("- Source URL: https://example.com/demo-recap.pdf", response.text)
            self.assertIn("- Answer preview: The study used the DemoSet benchmark.", response.text)


if __name__ == "__main__":
    unittest.main()
