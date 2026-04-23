"""Benchmark report generation for experiment runs."""

from __future__ import annotations

import html
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable


DEFAULT_TOKEN_PRICING = {
    "prompt_per_1k_tokens": 0.0005,
    "completion_per_1k_tokens": 0.0015,
    "currency": "USD",
    "label": "estimated mock-LLM pricing",
}


def load_experiment_run(results_path: str | Path) -> Dict[str, Any]:
    """Load a persisted experiment run payload from results.json."""
    return json.loads(Path(results_path).read_text(encoding="utf-8"))


def _percentile(values: Iterable[float], percentile: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def summarize_benchmark_run(
    experiment_run: Dict[str, Any],
    *,
    token_pricing: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a compact benchmark summary covering quality, latency, and token cost."""
    pricing = {**DEFAULT_TOKEN_PRICING, **(token_pricing or {})}
    aggregate = experiment_run["metrics"]["aggregate"]
    results = experiment_run.get("results", [])

    latencies = [float(result.get("latency_ms", 0.0)) for result in results]
    prompt_tokens = sum(int(result.get("token_usage", {}).get("prompt_tokens", 0)) for result in results)
    completion_tokens = sum(int(result.get("token_usage", {}).get("completion_tokens", 0)) for result in results)
    total_tokens = sum(int(result.get("token_usage", {}).get("total_tokens", 0)) for result in results)

    prompt_cost = prompt_tokens / 1000.0 * float(pricing["prompt_per_1k_tokens"])
    completion_cost = completion_tokens / 1000.0 * float(pricing["completion_per_1k_tokens"])

    return {
        "experiment": experiment_run.get("experiment", {}),
        "run_id": experiment_run.get("run_id"),
        "generated_at": experiment_run.get("generated_at"),
        "counts": {
            "qa_pairs": len(results),
            "answerable": int(aggregate.get("answerable_count", 0)),
            "unanswerable": int(aggregate.get("unanswerable_count", 0)),
        },
        "slices": experiment_run.get("metrics", {}).get("slices", {}),
        "accuracy": {
            "exact_match": float(aggregate.get("exact_match", 0.0)),
            "f1": float(aggregate.get("f1", 0.0)),
            "groundedness": float(aggregate.get("groundedness", 0.0)),
            "correctness": float(aggregate.get("correctness", 0.0)),
            "completeness": float(aggregate.get("completeness", 0.0)),
            "answer_quality": float(aggregate.get("answer_quality", 0.0)),
            "refusal_accuracy": float(aggregate.get("refusal_accuracy", 0.0)),
        },
        "retrieval": {
            "hit_rate": float(aggregate.get("retrieval_hit", 0.0)),
            "mrr": float(aggregate.get("retrieval_mrr", 0.0)),
            "false_refusal_rate": float(aggregate.get("false_refusal_rate", 0.0)),
            "missed_refusal_rate": float(aggregate.get("missed_refusal_rate", 0.0)),
            "refusal_true_positives": int(aggregate.get("refusal_true_positives", 0)),
            "refusal_false_positives": int(aggregate.get("refusal_false_positives", 0)),
            "refusal_false_negatives": int(aggregate.get("refusal_false_negatives", 0)),
            "refusal_true_negatives": int(aggregate.get("refusal_true_negatives", 0)),
        },
        "latency": {
            "avg_ms": mean(latencies) if latencies else 0.0,
            "p50_ms": _percentile(latencies, 0.50),
            "p95_ms": _percentile(latencies, 0.95),
            "max_ms": max(latencies) if latencies else 0.0,
        },
        "cost": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
            "total_cost": prompt_cost + completion_cost,
            "currency": pricing["currency"],
            "label": pricing["label"],
        },
    }


def render_benchmark_report_markdown(summary: Dict[str, Any]) -> str:
    """Render benchmark summary as a Markdown report."""
    experiment = summary["experiment"]
    accuracy = summary["accuracy"]
    retrieval = summary["retrieval"]
    latency = summary["latency"]
    cost = summary["cost"]
    counts = summary["counts"]
    slices = summary.get("slices", {})

    lines = [
        f"# Benchmark Report: {experiment.get('name', 'unknown')}",
        "",
        f"- Pipeline version: {experiment.get('pipeline_version', 'unknown')}",
        f"- Run ID: {summary.get('run_id', 'unknown')}",
        f"- Generated at: {summary.get('generated_at', 'unknown')}",
        f"- QA pairs: {counts['qa_pairs']} ({counts['answerable']} answerable, {counts['unanswerable']} unanswerable)",
        "",
        "## Accuracy",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Exact match | {accuracy['exact_match']:.2%} |",
        f"| F1 | {accuracy['f1']:.2%} |",
        f"| Groundedness | {accuracy['groundedness']:.2%} |",
        f"| Correctness | {accuracy['correctness']:.2%} |",
        f"| Completeness | {accuracy['completeness']:.2%} |",
        f"| Answer quality | {accuracy['answer_quality']:.2%} |",
        f"| Refusal accuracy | {accuracy['refusal_accuracy']:.2%} |",
        "",
        "## Retrieval",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Hit rate | {retrieval['hit_rate']:.2%} |",
        f"| Mean reciprocal rank | {retrieval['mrr']:.2%} |",
        f"| False refusal rate | {retrieval['false_refusal_rate']:.2%} |",
        f"| Missed refusal rate | {retrieval['missed_refusal_rate']:.2%} |",
        "",
    ]

    if slices:
        lines.extend(
            [
                "## Answerability slices",
                "",
                "| Slice | Count | Share | Exact Match | F1 | Retrieval Hit | Retrieval MRR | Refusal Rate | Refusal Accuracy |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for slice_name in ("answerable", "unanswerable"):
            slice_metrics = slices.get(slice_name)
            if not slice_metrics:
                continue
            lines.append(
                "| {name} | {count} | {share:.2%} | {em:.2%} | {f1:.2%} | {hit:.2%} | {mrr:.2%} | {refusal_rate:.2%} | {refusal_accuracy:.2%} |".format(
                    name=slice_name.title(),
                    count=int(slice_metrics.get("count", 0)),
                    share=float(slice_metrics.get("share", 0.0)),
                    em=float(slice_metrics.get("exact_match", 0.0)),
                    f1=float(slice_metrics.get("f1", 0.0)),
                    hit=float(slice_metrics.get("retrieval_hit", 0.0)),
                    mrr=float(slice_metrics.get("retrieval_mrr", 0.0)),
                    refusal_rate=float(slice_metrics.get("refusal_rate", 0.0)),
                    refusal_accuracy=float(slice_metrics.get("refusal_accuracy", 0.0)),
                )
            )
        lines.extend(
            [
                "",
                "## Refusal confusion summary",
                "",
                f"- True refusals on unanswerable questions: {retrieval['refusal_true_positives']}",
                f"- False refusals on answerable questions: {retrieval['refusal_false_positives']}",
                f"- Missed refusals on unanswerable questions: {retrieval['refusal_false_negatives']}",
                f"- Correct non-refusals on answerable questions: {retrieval['refusal_true_negatives']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Latency",
        "",
        "| Metric | Value (ms) |",
        "| --- | ---: |",
        f"| Average | {latency['avg_ms']:.2f} |",
        f"| P50 | {latency['p50_ms']:.2f} |",
        f"| P95 | {latency['p95_ms']:.2f} |",
        f"| Max | {latency['max_ms']:.2f} |",
        "",
        "## Cost",
        "",
        f"Estimated using {cost['label']}.",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Prompt tokens | {cost['prompt_tokens']} |",
        f"| Completion tokens | {cost['completion_tokens']} |",
        f"| Total tokens | {cost['total_tokens']} |",
        f"| Prompt cost | {cost['currency']} {cost['prompt_cost']:.4f} |",
        f"| Completion cost | {cost['currency']} {cost['completion_cost']:.4f} |",
        f"| Total cost | {cost['currency']} {cost['total_cost']:.4f} |",
        "",
        ]
    )
    return "\n".join(lines)


def render_benchmark_report_html(summary: Dict[str, Any]) -> str:
    """Render benchmark summary as a lightweight standalone HTML page."""
    markdown = render_benchmark_report_markdown(summary)
    body = "\n".join(f"<pre>{html.escape(markdown)}</pre>".splitlines())
    title = html.escape(f"Benchmark Report: {summary['experiment'].get('name', 'unknown')}")
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\" />\n"
        f"  <title>{title}</title>\n"
        "  <style>body{font-family:system-ui,sans-serif;margin:2rem;line-height:1.5;}"
        "pre{white-space:pre-wrap;background:#f6f8fa;padding:1rem;border-radius:8px;}"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )
