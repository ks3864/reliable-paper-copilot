#!/usr/bin/env python3
"""Generate Markdown and HTML benchmark reports from a persisted experiment run."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation import (
    load_experiment_run,
    render_benchmark_report_html,
    render_benchmark_report_markdown,
    summarize_benchmark_run,
)


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark reports from an experiment results.json file.")
    parser.add_argument("results_path", help="Path to a persisted results.json file.")
    parser.add_argument(
        "--output-dir",
        help="Optional directory for benchmark_report.md/html. Defaults to the results file directory.",
    )
    args = parser.parse_args()

    results_path = Path(args.results_path)
    experiment_run = load_experiment_run(results_path)
    summary = summarize_benchmark_run(experiment_run)

    output_dir = Path(args.output_dir) if args.output_dir else results_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = output_dir / "benchmark_report.md"
    html_path = output_dir / "benchmark_report.html"
    markdown_path.write_text(render_benchmark_report_markdown(summary), encoding="utf-8")
    html_path.write_text(render_benchmark_report_html(summary), encoding="utf-8")

    print(f"Wrote {markdown_path}")
    print(f"Wrote {html_path}")


if __name__ == "__main__":
    main()
