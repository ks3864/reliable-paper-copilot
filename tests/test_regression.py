import json
import subprocess
import sys
from pathlib import Path

from src.evaluation.regression import compare_experiment_runs, format_regression_report


def _make_run(name, version, aggregate):
    return {
        "experiment": {"name": name, "pipeline_version": version},
        "metrics": {"aggregate": aggregate},
    }


def test_compare_experiment_runs_flags_regressions_and_improvements():
    baseline = _make_run(
        "baseline-eval",
        "chunking-v1",
        {"exact_match": 0.4, "f1": 0.5, "retrieval_hit": 0.8, "answer_quality": 0.55},
    )
    candidate = _make_run(
        "baseline-eval",
        "chunking-v2",
        {"exact_match": 0.45, "f1": 0.48, "retrieval_hit": 0.82, "answer_quality": 0.55},
    )

    comparison = compare_experiment_runs(baseline, candidate)

    statuses = {item["metric"]: item["status"] for item in comparison["metrics"]}
    assert statuses["exact_match"] == "improved"
    assert statuses["f1"] == "regressed"
    assert statuses["retrieval_hit"] == "improved"
    assert statuses["answer_quality"] == "unchanged"
    assert comparison["summary"]["has_regression"] is True
    assert comparison["summary"]["regressions"] == ["f1"]


def test_format_regression_report_renders_markdown_table():
    comparison = compare_experiment_runs(
        _make_run("baseline-eval", "chunking-v1", {"exact_match": 0.4, "f1": 0.5}),
        _make_run("baseline-eval", "chunking-v2", {"exact_match": 0.45, "f1": 0.48}),
    )

    report = format_regression_report(comparison)

    assert "# Regression Comparison Report" in report
    assert "| exact_match | 40.00% | 45.00% | +5.00% | improved |" in report
    assert "- Regressions: f1" in report


def test_compare_experiments_script_prints_report(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    baseline_path.write_text(
        json.dumps(_make_run("baseline-eval", "chunking-v1", {"exact_match": 0.4, "f1": 0.5})),
        encoding="utf-8",
    )
    candidate_path.write_text(
        json.dumps(_make_run("baseline-eval", "chunking-v2", {"exact_match": 0.45, "f1": 0.48})),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/compare_experiments.py",
            str(baseline_path),
            str(candidate_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Regression Comparison Report" in result.stdout
    assert "chunking-v2" in result.stdout
