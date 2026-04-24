import json
from pathlib import Path

from fastapi.testclient import TestClient

import src.api.main as api_main
from src.api.main import app


client = TestClient(app)


def test_latest_benchmark_snapshot_returns_unavailable_when_no_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "ARTIFACTS_EXPERIMENTS_DIR", tmp_path)

    response = client.get("/benchmark/latest")

    assert response.status_code == 200
    assert response.json() == {
        "available": False,
        "message": "No persisted benchmark runs found yet.",
        "experiment_name": None,
        "pipeline_version": None,
        "run_id": None,
        "generated_at": None,
        "qa_pairs": 0,
        "metrics": {},
        "retrieval": {},
        "artifact_paths": {},
    }


def test_latest_benchmark_snapshot_returns_latest_run_metadata(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    experiments_dir = repo_root / "artifacts" / "experiments"
    monkeypatch.setattr(api_main, "ARTIFACTS_EXPERIMENTS_DIR", experiments_dir)
    monkeypatch.setattr(api_main, "REPO_ROOT", repo_root)

    older_dir = experiments_dir / "baseline-eval" / "v1" / "20260101T000000Z"
    latest_dir = experiments_dir / "hybrid-eval" / "v2" / "20260102T010000Z"
    older_dir.mkdir(parents=True)
    latest_dir.mkdir(parents=True)

    older_payload = {
        "experiment": {"name": "baseline-eval", "pipeline_version": "v1"},
        "run_id": "20260101T000000Z",
        "generated_at": "2026-01-01T00:00:00Z",
        "config": {"retrieval": {"mode": "dense", "top_k": 5}, "chunking": {"profile": "default"}},
        "metrics": {"aggregate": {"exact_match": 0.2, "f1": 0.3, "retrieval_hit": 0.4, "refusal_accuracy": 0.5}},
        "results": [{"id": 1}],
    }
    latest_payload = {
        "experiment": {"name": "hybrid-eval", "pipeline_version": "v2"},
        "run_id": "20260102T010000Z",
        "generated_at": "2026-01-02T01:00:00Z",
        "config": {
            "retrieval": {
                "mode": "hybrid",
                "top_k": 7,
                "dense_weight": 1.2,
                "lexical_weight": 0.8,
                "rrf_k": 55,
                "embedding_model": "demo-embedding",
            },
            "chunking": {"profile": "token-overlap-v2"},
        },
        "metrics": {"aggregate": {"exact_match": 0.61, "f1": 0.72, "retrieval_hit": 0.83, "refusal_accuracy": 0.94}},
        "results": [{"id": 1}, {"id": 2}, {"id": 3}],
    }

    (older_dir / "results.json").write_text(json.dumps(older_payload), encoding="utf-8")
    (latest_dir / "results.json").write_text(json.dumps(latest_payload), encoding="utf-8")
    (latest_dir / "summary.md").write_text("# Summary", encoding="utf-8")
    (latest_dir / "benchmark_report.md").write_text("# Report", encoding="utf-8")
    (latest_dir / "benchmark_report.html").write_text("<html></html>", encoding="utf-8")
    (experiments_dir / "benchmark_run_index.md").write_text("# Benchmark Run Index", encoding="utf-8")

    response = client.get("/benchmark/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is True
    assert payload["experiment_name"] == "hybrid-eval"
    assert payload["pipeline_version"] == "v2"
    assert payload["run_id"] == "20260102T010000Z"
    assert payload["generated_at"] == "2026-01-02T01:00:00Z"
    assert payload["qa_pairs"] == 3
    assert payload["metrics"] == {
        "exact_match": 0.61,
        "f1": 0.72,
        "retrieval_hit": 0.83,
        "refusal_accuracy": 0.94,
    }
    assert payload["retrieval"] == {
        "mode": "hybrid",
        "top_k": 7,
        "dense_weight": 1.2,
        "lexical_weight": 0.8,
        "rrf_k": 55,
        "embedding_model": "demo-embedding",
        "chunk_profile": "token-overlap-v2",
    }
    assert payload["artifact_paths"] == {
        "run_dir": "artifacts/experiments/hybrid-eval/v2/20260102T010000Z",
        "results": "artifacts/experiments/hybrid-eval/v2/20260102T010000Z/results.json",
        "index": "artifacts/experiments/benchmark_run_index.md",
        "summary": "artifacts/experiments/hybrid-eval/v2/20260102T010000Z/summary.md",
        "report_markdown": "artifacts/experiments/hybrid-eval/v2/20260102T010000Z/benchmark_report.md",
        "report_html": "artifacts/experiments/hybrid-eval/v2/20260102T010000Z/benchmark_report.html",
    }
