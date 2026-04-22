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
    parser.add_argument(
        "--output-dir",
        default="artifacts/experiments",
        help="Directory where versioned experiment outputs should be stored.",
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Skip writing experiment artifacts to disk.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Reliable Scientific Paper Copilot - Evaluation")
    print("=" * 60)

    experiment_run = run_experiment(
        args.config,
        persist_outputs=not args.no_persist,
        output_root=args.output_dir,
    )
    experiment = experiment_run["experiment"]
    results = experiment_run["results"]
    eval_results = experiment_run["metrics"]

    print(f"\nExperiment: {experiment['name']}")
    print(f"Pipeline version: {experiment['pipeline_version']}")
    print(f"Loading {len(results)} evaluated QA pairs...")
    if "output_dir" in experiment_run:
        print(f"Artifacts saved to: {experiment_run['output_dir']}")

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
    print(f"  Refusal Rate:    {agg.get('refusal_rate', 0.0):.2%}")
    print(f"  Refusal Acc.:    {agg.get('refusal_accuracy', 0.0):.2%}")
    print(f"  Refusal Prec.:   {agg.get('refusal_precision', 0.0):.2%}")
    print(f"  Refusal Recall:  {agg.get('refusal_recall', 0.0):.2%}")
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
        if "refused" in metric:
            line += f" Refused={metric['refused']:.0f}"
        print(line)

    if eval_results.get("slices"):
        print("\nSlice Breakdown:")
        for slice_name, slice_metrics in eval_results["slices"].items():
            print(
                f"  {slice_name}: count={slice_metrics['count']} "
                f"EM={slice_metrics['exact_match']:.2f} F1={slice_metrics['f1']:.2f} "
                f"RefusalRate={slice_metrics['refusal_rate']:.2f} "
                f"RefusalAcc={slice_metrics['refusal_accuracy']:.2f}"
            )

    return experiment_run


if __name__ == "__main__":
    main()
