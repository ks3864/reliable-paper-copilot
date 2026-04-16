#!/usr/bin/env python3
"""Compare two persisted experiment runs and print a regression report."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.regression import compare_experiment_runs, format_regression_report


def _load_results(path: str | Path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    parser = argparse.ArgumentParser(description="Compare two experiment result payloads.")
    parser.add_argument("baseline", help="Path to baseline results.json")
    parser.add_argument("candidate", help="Path to candidate results.json")
    parser.add_argument(
        "--output",
        help="Optional path to write the markdown report.",
    )
    args = parser.parse_args()

    comparison = compare_experiment_runs(_load_results(args.baseline), _load_results(args.candidate))
    report = format_regression_report(comparison)
    print(report)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
