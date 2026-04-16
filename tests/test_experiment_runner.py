import json
from pathlib import Path

from data.eval.eval_set import get_eval_chunks
from src.evaluation.experiment_runner import load_experiment_config, run_experiment


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

    summary_text = (output_dir / "summary.md").read_text(encoding="utf-8")
    assert "# Experiment Summary: baseline-eval" in summary_text
    assert "Pipeline version: phase3-pipeline-versioning-v1" in summary_text
