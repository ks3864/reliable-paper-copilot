"""Evaluation module."""

from .experiment_runner import load_experiment_config, persist_experiment_run, run_experiment
from .benchmark_report import (
    load_experiment_run,
    render_benchmark_report_html,
    render_benchmark_report_markdown,
    summarize_benchmark_run,
)
from .judge import AnswerQualityJudge, create_mock_judge_callable, parse_judge_response
from .metrics import (
    exact_match_score,
    f1_score,
    retrieval_hit_rate,
    retrieval_mrr,
    evaluate_qa_pair,
    evaluate_all,
)
from .regression import compare_experiment_runs, format_regression_report

__all__ = [
    "AnswerQualityJudge",
    "create_mock_judge_callable",
    "parse_judge_response",
    "load_experiment_config",
    "load_experiment_run",
    "persist_experiment_run",
    "render_benchmark_report_html",
    "render_benchmark_report_markdown",
    "run_experiment",
    "compare_experiment_runs",
    "format_regression_report",
    "summarize_benchmark_run",
    "exact_match_score",
    "f1_score",
    "retrieval_hit_rate",
    "retrieval_mrr",
    "evaluate_qa_pair",
    "evaluate_all",
]
