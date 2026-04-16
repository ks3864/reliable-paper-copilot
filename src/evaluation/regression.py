"""Regression comparison helpers for evaluation runs."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


DEFAULT_METRICS = (
    "exact_match",
    "f1",
    "retrieval_hit",
    "retrieval_mrr",
    "groundedness",
    "correctness",
    "completeness",
    "answer_quality",
)


def compare_experiment_runs(
    baseline_run: Dict[str, Any],
    candidate_run: Dict[str, Any],
    *,
    metric_names: Iterable[str] = DEFAULT_METRICS,
    tolerance: float = 1e-9,
) -> Dict[str, Any]:
    """Compare aggregate metrics from two experiment runs."""
    baseline_metrics = baseline_run["metrics"]["aggregate"]
    candidate_metrics = candidate_run["metrics"]["aggregate"]

    compared_metrics: List[Dict[str, Any]] = []
    regressions: List[str] = []
    improvements: List[str] = []

    for metric_name in metric_names:
        if metric_name not in baseline_metrics or metric_name not in candidate_metrics:
            continue

        baseline_value = float(baseline_metrics[metric_name])
        candidate_value = float(candidate_metrics[metric_name])
        delta = candidate_value - baseline_value
        status = "unchanged"

        if delta > tolerance:
            status = "improved"
            improvements.append(metric_name)
        elif delta < -tolerance:
            status = "regressed"
            regressions.append(metric_name)

        compared_metrics.append(
            {
                "metric": metric_name,
                "baseline": baseline_value,
                "candidate": candidate_value,
                "delta": delta,
                "status": status,
            }
        )

    return {
        "baseline_experiment": baseline_run.get("experiment", {}),
        "candidate_experiment": candidate_run.get("experiment", {}),
        "metrics": compared_metrics,
        "summary": {
            "regressions": regressions,
            "improvements": improvements,
            "has_regression": bool(regressions),
            "has_improvement": bool(improvements),
        },
    }


def format_regression_report(comparison: Dict[str, Any]) -> str:
    """Render a compact markdown regression report."""
    baseline = comparison.get("baseline_experiment", {})
    candidate = comparison.get("candidate_experiment", {})
    lines = [
        "# Regression Comparison Report",
        "",
        f"- Baseline: {baseline.get('name', 'unknown')} ({baseline.get('pipeline_version', 'unknown')})",
        f"- Candidate: {candidate.get('name', 'unknown')} ({candidate.get('pipeline_version', 'unknown')})",
        "",
        "## Aggregate metric deltas",
        "",
        "| Metric | Baseline | Candidate | Delta | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]

    for metric in comparison.get("metrics", []):
        lines.append(
            "| {metric} | {baseline:.2%} | {candidate:.2%} | {delta:+.2%} | {status} |".format(
                metric=metric["metric"],
                baseline=metric["baseline"],
                candidate=metric["candidate"],
                delta=metric["delta"],
                status=metric["status"],
            )
        )

    summary = comparison.get("summary", {})
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Regressions: {', '.join(summary.get('regressions', [])) or 'none'}",
            f"- Improvements: {', '.join(summary.get('improvements', [])) or 'none'}",
        ]
    )
    return "\n".join(lines) + "\n"
