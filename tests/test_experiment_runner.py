import json
from pathlib import Path

from data.eval.eval_set import get_eval_chunks
from src.evaluation.experiment_runner import load_experiment_config, persist_experiment_run, run_experiment


def test_load_experiment_config_applies_defaults(tmp_path):
    config_path = tmp_path / "experiment.yaml"
    config_path.write_text(
        "experiment:\n  name: custom\n  pipeline_version: v-test\nevaluation:\n  top_k: 3\n",
        encoding="utf-8",
    )

    config = load_experiment_config(config_path)

    assert config["experiment"]["name"] == "custom"
    assert config["experiment"]["pipeline_version"] == "v-test"
    assert config["evaluation"]["top_k"] == 3
    assert config["retrieval"]["embedding_model"] == "all-MiniLM-L6-v2"
    assert config["retrieval"]["chunk_profile"] == "chunking-v2"
    assert config["retrieval"]["mode"] == "dense"
    assert config["retrieval"]["lexical_weight"] == 1.0
    assert config["answering"]["generator"] == "simple"


def test_get_eval_chunks_returns_distinct_regression_profiles():
    v1_chunks = get_eval_chunks("chunking-v1")
    v2_chunks = get_eval_chunks("chunking-v2")

    assert len(v1_chunks) < len(v2_chunks)
    assert all(chunk["metadata"]["chunking_strategy"] == "section_v1" for chunk in v1_chunks)
    assert all(chunk["metadata"]["chunking_strategy"] == "section_v2" for chunk in v2_chunks)


class StubRetriever:
    def retrieve(self, query, top_k=5):
        return [
            {
                "chunk_id": 0,
                "section": "abstract",
                "text": "Stub context",
                "metadata": {"source": "sample_paper"},
                "retrieval_score": 0.95,
            }
        ]


class StubGenerator:
    def answer(self, question, top_k=5):
        return {
            "question": question,
            "answer": "stub answer",
            "retrieved_chunks": [
                {
                    "chunk_id": 0,
                    "section": "abstract",
                    "text": "Stub context",
                    "metadata": {"source": "sample_paper"},
                    "retrieval_score": 0.95,
                }
            ],
            "sources": ["abstract"],
            "num_chunks_retrieved": 1,
            "confidence": {
                "has_good_match": True,
                "top_score": 0.95,
                "average_score": 0.95,
                "reason": None,
            },
        }


def test_run_experiment_returns_versioned_metadata():
    config_path = Path("configs/experiments/baseline.yaml")

    result = run_experiment(
        config_path,
        retriever_factory=lambda chunks, model_name: StubRetriever(),
        generator_factory=lambda retriever, generator_name: StubGenerator(),
        judge_factory=lambda enabled: None,
    )

    assert result["experiment"]["name"] == "baseline-eval"
    assert result["experiment"]["pipeline_version"] == "phase3-pipeline-versioning-v1"
    assert len(result["results"]) > 0
    assert "aggregate" in result["metrics"]
    assert "run_id" in result
    assert "generated_at" in result


def test_run_experiment_uses_configured_chunk_profile():
    seen = {}

    def capture_retriever_factory(chunks, model_name):
        seen["chunks"] = chunks
        return StubRetriever()

    run_experiment(
        Path("configs/experiments/chunking-v1.yaml"),
        retriever_factory=capture_retriever_factory,
        generator_factory=lambda retriever, generator_name: StubGenerator(),
        judge_factory=lambda enabled: None,
    )

    assert len(seen["chunks"]) == len(get_eval_chunks("chunking-v1"))
    assert all(chunk["metadata"]["chunking_strategy"] == "section_v1" for chunk in seen["chunks"])


def test_run_experiment_persists_versioned_outputs(tmp_path):
    config_path = Path("configs/experiments/baseline.yaml")

    result = run_experiment(
        config_path,
        retriever_factory=lambda chunks, model_name: StubRetriever(),
        generator_factory=lambda retriever, generator_name: StubGenerator(),
        judge_factory=lambda enabled: None,
        persist_outputs=True,
        output_root=tmp_path,
    )

    output_dir = Path(result["output_dir"])
    assert output_dir.exists()
    assert output_dir.parts[-3] == "baseline-eval"
    assert output_dir.parts[-2] == "phase3-pipeline-versioning-v1"

    results_payload = json.loads((output_dir / "results.json").read_text(encoding="utf-8"))
    assert results_payload["experiment"]["name"] == "baseline-eval"
    assert results_payload["run_id"] == result["run_id"]
    expected_qa_pairs = len(results_payload["results"])
    aggregate = results_payload["metrics"]["aggregate"]

    summary_text = (output_dir / "summary.md").read_text(encoding="utf-8")
    assert "# Experiment Summary: baseline-eval" in summary_text
    assert "## Overall Metrics" in summary_text
    assert "Pipeline version: phase3-pipeline-versioning-v1" in summary_text
    assert "Retrieval mode: dense" in summary_text
    assert "## Answerability Slice Breakdown" in summary_text
    assert "| Slice | Count | Share | Exact Match | F1 | Retrieval Hit | Retrieval MRR | Refusal Rate | Refusal Accuracy |" in summary_text
    assert "## Refusal Confusion Summary" in summary_text

    index_text = (tmp_path / "benchmark_run_index.md").read_text(encoding="utf-8")
    assert "# Benchmark Run Index" in index_text
    assert "## Quick Summary" in index_text
    assert "- Experiments indexed: 1" in index_text
    assert f"- Newest generated run: baseline-eval / phase3-pipeline-versioning-v1 at {result['generated_at']} (`{result['run_id']}`)" in index_text
    assert f"- Best latest F1: baseline-eval / phase3-pipeline-versioning-v1 with {aggregate['f1']:.2%} (`{result['run_id']}`)" in index_text
    assert "| Experiment | Pipeline Version | Latest Run ID | Generated At | QA Pairs | Exact Match | F1 | Retrieval Hit | Refusal Accuracy | Artifacts |" in index_text
    assert "baseline-eval" in index_text
    assert "phase3-pipeline-versioning-v1" in index_text
    assert result["generated_at"] in index_text
    assert f"| {expected_qa_pairs} |" in index_text
    assert f"{aggregate['exact_match']:.2%}" in index_text
    assert f"{aggregate['f1']:.2%}" in index_text
    assert f"{aggregate['retrieval_hit']:.2%}" in index_text
    assert f"{aggregate['refusal_accuracy']:.2%}" in index_text
    assert "[run-dir](baseline-eval/phase3-pipeline-versioning-v1/" in index_text
    assert "[report-md](baseline-eval/phase3-pipeline-versioning-v1/" in index_text
    assert "[report-html](baseline-eval/phase3-pipeline-versioning-v1/" in index_text


def test_benchmark_run_index_keeps_latest_run_per_experiment(tmp_path):
    config_path = Path("configs/experiments/baseline.yaml")
    result = run_experiment(
        config_path,
        retriever_factory=lambda chunks, model_name: StubRetriever(),
        generator_factory=lambda retriever, generator_name: StubGenerator(),
        judge_factory=lambda enabled: None,
    )
    first = {**result, "run_id": "20260101T000000Z"}
    second = {**result, "run_id": "20260101T000100Z"}

    persist_experiment_run(first, output_root=tmp_path)
    persist_experiment_run(second, output_root=tmp_path)

    index_text = (tmp_path / "benchmark_run_index.md").read_text(encoding="utf-8")

    assert first["run_id"] not in index_text
    assert second["run_id"] in index_text
    assert index_text.count("| baseline-eval |") == 1


def test_run_experiment_uses_hybrid_retrieval_settings_from_config(tmp_path):
    config_path = tmp_path / "hybrid.yaml"
    config_path.write_text(
        """
experiment:
  name: hybrid-test
  pipeline_version: phase4-hybrid
retrieval:
  mode: hybrid
  dense_weight: 1.5
  lexical_weight: 0.7
  rrf_k: 42
evaluation:
  use_answer_quality_judge: false
""",
        encoding="utf-8",
    )

    result = run_experiment(config_path, judge_factory=lambda enabled: None)

    assert result["config"]["retrieval"]["mode"] == "hybrid"
    assert result["config"]["retrieval"]["dense_weight"] == 1.5
    assert result["config"]["retrieval"]["lexical_weight"] == 0.7
    assert result["config"]["retrieval"]["rrf_k"] == 42
