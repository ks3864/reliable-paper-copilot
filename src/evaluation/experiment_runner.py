"""Config-based experiment runner for evaluation pipelines."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, List

import yaml

from data.eval.eval_set import EVAL_QA_PAIRS, SAMPLE_PAPER_CHUNKS, save_eval_set

from .judge import AnswerQualityJudge, create_mock_judge_callable
from .metrics import evaluate_all


ExperimentConfig = Dict[str, Any]
RetrieverFactory = Callable[[List[Dict[str, Any]], str | None], Any]
GeneratorFactory = Callable[[Any, str | None], Any]
JudgeFactory = Callable[[bool], Any]


DEFAULT_CONFIG: ExperimentConfig = {
    "experiment": {
        "name": "baseline-eval",
        "pipeline_version": "v1",
        "description": "Default evaluation pipeline for the sample copilot stack.",
    },
    "retrieval": {
        "embedding_model": "all-MiniLM-L6-v2",
    },
    "answering": {
        "generator": "simple",
        "judge": "mock",
    },
    "evaluation": {
        "top_k": 5,
        "use_answer_quality_judge": True,
    },
}


def load_experiment_config(config_path: str | Path) -> ExperimentConfig:
    """Load an experiment config and fill in missing defaults."""
    path = Path(config_path)
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}

    config = deepcopy(DEFAULT_CONFIG)
    for section, values in loaded.items():
        if isinstance(values, dict) and isinstance(config.get(section), dict):
            config[section].update(values)
        else:
            config[section] = values

    return config


def _default_retriever_factory(chunks: List[Dict[str, Any]], model_name: str | None):
    from src.retrieval import create_retriever

    return create_retriever(chunks, model_name=model_name or DEFAULT_CONFIG["retrieval"]["embedding_model"])


def _default_generator_factory(retriever: Any, generator_name: str | None):
    from src.answering import SimpleAnswerGenerator

    if generator_name not in (None, "simple"):
        raise ValueError(f"Unsupported generator: {generator_name}")
    return SimpleAnswerGenerator(retriever)


def _default_judge_factory(enabled: bool):
    if not enabled:
        return None
    return AnswerQualityJudge(create_mock_judge_callable())


def run_experiment(
    config_path: str | Path,
    *,
    retriever_factory: RetrieverFactory | None = None,
    generator_factory: GeneratorFactory | None = None,
    judge_factory: JudgeFactory | None = None,
) -> Dict[str, Any]:
    """Run the evaluation pipeline from a config file."""
    config = load_experiment_config(config_path)
    save_eval_set()

    retriever = (retriever_factory or _default_retriever_factory)(
        SAMPLE_PAPER_CHUNKS,
        config["retrieval"].get("embedding_model"),
    )
    generator = (generator_factory or _default_generator_factory)(
        retriever,
        config["answering"].get("generator"),
    )
    judge = (judge_factory or _default_judge_factory)(
        bool(config["evaluation"].get("use_answer_quality_judge", True))
    )

    results = []
    top_k = int(config["evaluation"].get("top_k", 5))
    for qa in EVAL_QA_PAIRS:
        answer = generator.answer(qa["question"], top_k=top_k)
        results.append(answer)

    metrics = evaluate_all(results, EVAL_QA_PAIRS, judge=judge)
    return {
        "experiment": config["experiment"],
        "config": config,
        "results": results,
        "metrics": metrics,
    }
