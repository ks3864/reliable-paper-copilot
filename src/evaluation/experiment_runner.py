"""Config-based experiment runner for evaluation pipelines."""

from __future__ import annotations

import json
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

import yaml

from data.eval.eval_set import EVAL_QA_PAIRS, get_eval_chunks, save_eval_set

from .judge import AnswerQualityJudge, create_mock_judge_callable
from .metrics import evaluate_all
from .benchmark_report import render_benchmark_report_html, render_benchmark_report_markdown, summarize_benchmark_run


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


def _collect_latest_run_dirs(output_root: Path) -> List[Path]:
    latest_by_experiment: Dict[str, Path] = {}
    for results_path in output_root.glob("*/*/*/results.json"):
        run_dir = results_path.parent
        experiment_key = "/".join(run_dir.parts[-3:-1])
        previous = latest_by_experiment.get(experiment_key)
        if previous is None or run_dir.name > previous.name:
            latest_by_experiment[experiment_key] = run_dir
    return sorted(latest_by_experiment.values(), key=lambda path: path.parts[-3:])


def _build_benchmark_run_index(output_root: Path) -> str:
    lines = [
        "# Benchmark Run Index",
        "",
        "Latest benchmark artifacts per experiment.",
        "",
    ]

    run_summaries: List[Dict[str, Any]] = []
    for run_dir in _collect_latest_run_dirs(output_root):
        experiment_name = run_dir.parts[-3]
        pipeline_version = run_dir.parts[-2]
        run_id = run_dir.parts[-1]
        results_payload = {}
        aggregate = {}
        results_path = run_dir / "results.json"
        if results_path.exists():
            results_payload = json.loads(results_path.read_text(encoding="utf-8"))
            aggregate = results_payload.get("metrics", {}).get("aggregate", {})
        qa_pairs = len(results_payload.get("results", []))
        generated_at = results_payload.get("generated_at", "-")
        links = [f"[run-dir]({run_dir.relative_to(output_root).as_posix()}/)"]
        for filename, label in (
            ("summary.md", "summary"),
            ("benchmark_report.md", "report-md"),
            ("benchmark_report.html", "report-html"),
            ("results.json", "results"),
        ):
            artifact_path = run_dir / filename
            if artifact_path.exists():
                relative_path = artifact_path.relative_to(output_root)
                links.append(f"[{label}]({relative_path.as_posix()})")
        run_summaries.append(
            {
                "experiment_name": experiment_name,
                "pipeline_version": pipeline_version,
                "run_id": run_id,
                "generated_at": generated_at,
                "qa_pairs": qa_pairs,
                "exact_match": float(aggregate.get("exact_match", 0.0)),
                "f1": float(aggregate.get("f1", 0.0)),
                "retrieval_hit": float(aggregate.get("retrieval_hit", 0.0)),
                "refusal_accuracy": float(aggregate.get("refusal_accuracy", 0.0)),
                "links": " / ".join(links) if links else "-",
            }
        )

    if run_summaries:
        newest_run = max(run_summaries, key=lambda item: (item["generated_at"], item["run_id"]))
        best_f1_run = max(run_summaries, key=lambda item: (item["f1"], item["generated_at"], item["run_id"]))
        lines.extend(
            [
                "## Quick Summary",
                "",
                f"- Experiments indexed: {len(run_summaries)}",
                f"- Newest generated run: {newest_run['experiment_name']} / {newest_run['pipeline_version']} at {newest_run['generated_at']} (`{newest_run['run_id']}`)",
                f"- Best latest F1: {best_f1_run['experiment_name']} / {best_f1_run['pipeline_version']} with {best_f1_run['f1']:.2%} (`{best_f1_run['run_id']}`)",
                "",
            ]
        )

    lines.extend(
        [
            "| Experiment | Pipeline Version | Latest Run ID | Generated At | QA Pairs | Exact Match | F1 | Retrieval Hit | Refusal Accuracy | Artifacts |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )

    for summary in run_summaries:
        lines.append(
            "| {experiment_name} | {pipeline_version} | `{run_id}` | {generated_at} | {qa_pairs} | {exact_match:.2%} | {f1:.2%} | {retrieval_hit:.2%} | {refusal_accuracy:.2%} | {links} |".format(
                **summary,
            )
        )

    if not run_summaries:
        lines.append("| - | - | - | - | - | - | - | - | - | No benchmark runs found yet. |")

    return "\n".join(lines) + "\n"


def _build_summary_text(experiment_run: Dict[str, Any]) -> str:
    experiment = experiment_run["experiment"]
    aggregate = experiment_run["metrics"]["aggregate"]
    retrieval = experiment_run["config"]["retrieval"]
    lines = [
        f"# Experiment Summary: {experiment['name']}",
        "",
        "## Overall Metrics",
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
        f"- False refusal rate on answerable questions: {aggregate.get('false_refusal_rate', 0.0):.2%}",
        f"- Missed refusal rate on unanswerable questions: {aggregate.get('missed_refusal_rate', 0.0):.2%}",
    ]

    for metric_name in ("groundedness", "correctness", "completeness", "answer_quality"):
        if metric_name in aggregate:
            lines.append(f"- {metric_name.replace('_', ' ').title()}: {aggregate[metric_name]:.2%}")

    slices = experiment_run["metrics"].get("slices", {})
    if slices:
        lines.extend(
            [
                "",
                "## Answerability Slice Breakdown",
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
                    count=slice_metrics["count"],
                    share=slice_metrics.get("share", 0.0),
                    em=slice_metrics["exact_match"],
                    f1=slice_metrics["f1"],
                    hit=slice_metrics["retrieval_hit"],
                    mrr=slice_metrics["retrieval_mrr"],
                    refusal_rate=slice_metrics["refusal_rate"],
                    refusal_accuracy=slice_metrics["refusal_accuracy"],
                )
            )

        lines.extend(
            [
                "",
                "## Refusal Confusion Summary",
                f"- True refusals on unanswerable questions: {aggregate.get('refusal_true_positives', 0)}",
                f"- False refusals on answerable questions: {aggregate.get('refusal_false_positives', 0)}",
                f"- Missed refusals on unanswerable questions: {aggregate.get('refusal_false_negatives', 0)}",
                f"- Correct non-refusals on answerable questions: {aggregate.get('refusal_true_negatives', 0)}",
            ]
        )

    return "\n".join(lines) + "\n"


def persist_experiment_run(
    experiment_run: Dict[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
) -> Path:
    """Persist raw outputs plus a compact versioned summary for one experiment run."""
    output_root = Path(output_root)
    experiment = experiment_run["experiment"]
    run_dir = (
        output_root
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
    benchmark_summary = summarize_benchmark_run(experiment_run)
    (run_dir / "benchmark_report.md").write_text(
        render_benchmark_report_markdown(benchmark_summary),
        encoding="utf-8",
    )
    (run_dir / "benchmark_report.html").write_text(
        render_benchmark_report_html(benchmark_summary),
        encoding="utf-8",
    )
    (output_root / "benchmark_run_index.md").write_text(
        _build_benchmark_run_index(output_root),
        encoding="utf-8",
    )
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
        started_at = time.perf_counter()
        answer = generator.answer(qa["question"], top_k=top_k)
        answer["latency_ms"] = round((time.perf_counter() - started_at) * 1000, 3)
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
