from pathlib import Path

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
    assert config["answering"]["generator"] == "simple"


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
