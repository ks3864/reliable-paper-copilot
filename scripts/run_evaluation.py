#!/usr/bin/env python3
"""Evaluation script for Reliable Scientific Paper Copilot."""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation import run_experiment


def main():
    parser = argparse.ArgumentParser(description="Run a configured evaluation experiment.")
    parser.add_argument(
        "--config",
        default="configs/experiments/baseline.yaml",
        help="Path to experiment config YAML.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Reliable Scientific Paper Copilot - Evaluation")
    print("=" * 60)

    experiment_run = run_experiment(args.config)
    experiment = experiment_run["experiment"]
    results = experiment_run["results"]
    eval_results = experiment_run["metrics"]

    print(f"\nExperiment: {experiment['name']}")
    print(f"Pipeline version: {experiment['pipeline_version']}")
    print(f"Loading {len(results)} evaluated QA pairs...")

    print("\nPer-Question Outputs:")
    for result, metric in zip(results, eval_results["per_question"]):
        answer_preview = result["answer"][:100] + "..." if len(result["answer"]) > 100 else result["answer"]
        print(f"\n  [{metric['question_id']}] Q: {result['question']}")
        print(f"      A: {answer_preview}")
        print(f"      Sources: {result['sources']}")

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    agg = eval_results["aggregate"]
    print("\nAggregate Metrics:")
    print(f"  Exact Match:     {agg['exact_match']:.2%}")
    print(f"  F1 Score:        {agg['f1']:.2%}")
    print(f"  Retrieval Hit:   {agg['retrieval_hit']:.2%}")
    print(f"  Retrieval MRR:   {agg['retrieval_mrr']:.2%}")
    if 'groundedness' in agg:
        print(f"  Groundedness:    {agg['groundedness']:.2%}")
        print(f"  Correctness:     {agg['correctness']:.2%}")
        print(f"  Completeness:    {agg['completeness']:.2%}")
        print(f"  Answer Quality:  {agg['answer_quality']:.2%}")

    print("\nPer-Question Breakdown:")
    for metric in eval_results["per_question"]:
        line = (
            f"  [{metric['question_id']}] EM={metric['exact_match']:.2f} F1={metric['f1']:.2f} "
            f"Hit={metric['retrieval_hit']:.2f} MRR={metric['retrieval_mrr']:.2f}"
        )
        if "answer_quality" in metric:
            line += f" AQ={metric['answer_quality']:.2f}"
        print(line)

    return experiment_run


if __name__ == "__main__":
    main()
