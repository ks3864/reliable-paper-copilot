import json
from pathlib import Path

from src.evaluation import (
    load_experiment_run,
    render_benchmark_report_html,
    render_benchmark_report_markdown,
    summarize_benchmark_run,
)
from src.evaluation.experiment_runner import run_experiment


class StubRetriever:
    def retrieve(self, query, top_k=5):
        return [
            {
                "chunk_id": 0,
                "section": "results",
                "text": "Benchmark result chunk",
                "metadata": {"source": "sample_paper"},
                "retrieval_score": 0.97,
            }
        ]


class StubGenerator:
    def answer(self, question, top_k=5):
        return {
            "question": question,
            "answer": "stub benchmark answer",
            "retrieved_chunks": [
                {
                    "chunk_id": 0,
                    "section": "results",
                    "text": "Benchmark result chunk",
                    "metadata": {"source": "sample_paper"},
                    "retrieval_score": 0.97,
                }
            ],
            "sources": ["results"],
            "num_chunks_retrieved": 1,
            "confidence": {
                "has_good_match": True,
                "top_score": 0.97,
                "average_score": 0.97,
                "reason": None,
            },
            "token_usage": {"prompt_tokens": 12, "completion_tokens": 6, "total_tokens": 18},
        }


def test_benchmark_summary_and_renderers_include_quality_latency_and_cost(tmp_path):
    result = run_experiment(
        Path("configs/experiments/baseline.yaml"),
        retriever_factory=lambda chunks, model_name: StubRetriever(),
        generator_factory=lambda retriever, generator_name: StubGenerator(),
        judge_factory=lambda enabled: None,
        persist_outputs=True,
        output_root=tmp_path,
    )

    summary = summarize_benchmark_run(result)

    assert summary["counts"]["qa_pairs"] == len(result["results"])
    assert summary["latency"]["avg_ms"] >= 0.0
    assert summary["cost"]["total_tokens"] == len(result["results"]) * 18
    assert summary["cost"]["total_cost"] > 0.0

    markdown = render_benchmark_report_markdown(summary)
    assert "# Benchmark Report: baseline-eval" in markdown
    assert "## Accuracy" in markdown
    assert "## Retrieval" in markdown
    assert "## Latency" in markdown
    assert "## Cost" in markdown

    html = render_benchmark_report_html(summary)
    assert "<!DOCTYPE html>" in html
    assert "Benchmark Report: baseline-eval" in html

    output_dir = Path(result["output_dir"])
    assert (output_dir / "benchmark_report.md").exists()
    assert (output_dir / "benchmark_report.html").exists()


def test_load_experiment_run_reads_persisted_results(tmp_path):
    results_path = tmp_path / "results.json"
    payload = {"experiment": {"name": "demo"}, "metrics": {"aggregate": {}}, "results": []}
    results_path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_experiment_run(results_path)

    assert loaded["experiment"]["name"] == "demo"
