"""Config-based experiment runner for evaluation pipelines."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

import yaml

from data.eval.eval_set import EVAL_QA_PAIRS, get_eval_chunks, save_eval_set

from .judge import AnswerQualityJudge, create_mock_judge_callable
from .metrics import evaluate_all


ExperimentConfig = Dict[str, Any]
RetrieverFactory = Callable[[List[Dict[str, Any]], str | None], Any]
GeneratorFactory = Callable[[Any, str | None], Any]
JudgeFactory = Callable[[bool], Any]


DEFAULT_OUTPUT_ROOT = Path("artifacts/experiments")


DEFAULT_CONFIG: ExperimentConfig = {
    "experiment": {
        "name": "baseline-eval",
        "pipeline_version": "v1",
        "description": "Default evaluation pipeline for the sample copilot stack.",
    },
    "retrieval": {
        "embedding_model": "all-MiniLM-L6-v2",
        "chunk_profile": "chunking-v2",
        "mode": "dense",
        "lexical_weight": 1.0,
        "dense_weight": 1.0,
        "rrf_k": 60,
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


def _slugify(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-") or "experiment"


def _build_summary_text(experiment_run: Dict[str, Any]) -> str:
    experiment = experiment_run["experiment"]
    aggregate = experiment_run["metrics"]["aggregate"]
    retrieval = experiment_run["config"]["retrieval"]
    lines = [
        f"# Experiment Summary: {experiment['name']}",
        "",
        f"- Pipeline version: {experiment['pipeline_version']}",
        f"- Run ID: {experiment_run['run_id']}",
        f"- Retrieval mode: {retrieval.get('mode', 'dense')}",
        f"- Retrieval weights: dense={retrieval.get('dense_weight', 1.0)}, lexical={retrieval.get('lexical_weight', 1.0)}, rrf_k={retrieval.get('rrf_k', 60)}",
        f"- QA pairs evaluated: {len(experiment_run['results'])}",
        f"- Exact match: {aggregate['exact_match']:.2%}",
        f"- F1: {aggregate['f1']:.2%}",
        f"- Retrieval hit: {aggregate['retrieval_hit']:.2%}",
        f"- Retrieval MRR: {aggregate['retrieval_mrr']:.2%}",
        f"- Refusal rate: {aggregate.get('refusal_rate', 0.0):.2%}",
        f"- Refusal accuracy: {aggregate.get('refusal_accuracy', 0.0):.2%}",
        f"- Refusal precision: {aggregate.get('refusal_precision', 0.0):.2%}",
        f"- Refusal recall: {aggregate.get('refusal_recall', 0.0):.2%}",
    ]

    for metric_name in ("groundedness", "correctness", "completeness", "answer_quality"):
        if metric_name in aggregate:
            lines.append(f"- {metric_name.replace('_', ' ').title()}: {aggregate[metric_name]:.2%}")

    for slice_name, slice_metrics in experiment_run["metrics"].get("slices", {}).items():
        lines.extend(
            [
                f"- {slice_name.title()} questions: {slice_metrics['count']}",
                f"  - {slice_name.title()} refusal rate: {slice_metrics['refusal_rate']:.2%}",
                f"  - {slice_name.title()} refusal accuracy: {slice_metrics['refusal_accuracy']:.2%}",
            ]
        )

    return "\n".join(lines) + "\n"


def persist_experiment_run(
    experiment_run: Dict[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
) -> Path:
    """Persist raw outputs plus a compact versioned summary for one experiment run."""
    experiment = experiment_run["experiment"]
    run_dir = (
        Path(output_root)
        / _slugify(experiment["name"])
        / _slugify(experiment["pipeline_version"])
        / experiment_run["run_id"]
    )
    run_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "run_id": experiment_run["run_id"],
        "generated_at": experiment_run["generated_at"],
        "experiment": experiment,
        "config": experiment_run["config"],
        "metrics": experiment_run["metrics"],
        "results": experiment_run["results"],
    }
    (run_dir / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (run_dir / "summary.md").write_text(_build_summary_text(experiment_run), encoding="utf-8")
    return run_dir


def run_experiment(
    config_path: str | Path,
    *,
    retriever_factory: RetrieverFactory | None = None,
    generator_factory: GeneratorFactory | None = None,
    judge_factory: JudgeFactory | None = None,
    persist_outputs: bool = False,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
) -> Dict[str, Any]:
    """Run the evaluation pipeline from a config file."""
    config = load_experiment_config(config_path)
    save_eval_set()
    retrieval_config = config["retrieval"]

    eval_chunks = get_eval_chunks(retrieval_config.get("chunk_profile", "chunking-v2"))
    if retriever_factory is None:
        from src.retrieval import create_retriever

        retriever = create_retriever(
            eval_chunks,
            model_name=retrieval_config.get("embedding_model") or DEFAULT_CONFIG["retrieval"]["embedding_model"],
            retrieval_mode=retrieval_config.get("mode", "dense"),
            lexical_weight=float(retrieval_config.get("lexical_weight", 1.0)),
            dense_weight=float(retrieval_config.get("dense_weight", 1.0)),
            rrf_k=int(retrieval_config.get("rrf_k", 60)),
        )
    else:
        retriever = retriever_factory(
            eval_chunks,
            retrieval_config.get("embedding_model"),
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
    generated_at = datetime.now(timezone.utc)
    experiment_run = {
        "run_id": generated_at.strftime("%Y%m%dT%H%M%SZ"),
        "generated_at": generated_at.isoformat(),
        "experiment": config["experiment"],
        "config": config,
        "results": results,
        "metrics": metrics,
    }

    if persist_outputs:
        experiment_run["output_dir"] = str(persist_experiment_run(experiment_run, output_root=output_root))

    return experiment_run
