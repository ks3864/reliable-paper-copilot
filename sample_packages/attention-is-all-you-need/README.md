# Sample package: Attention Is All You Need

This package pins one open-access paper plus a few demo questions so the project can use a consistent real-paper example.

## Contents

- `manifest.json`: package metadata and canonical URLs
- `questions.json`: example questions for ingestion and grounded QA demos

## Why this paper

- public and stable arXiv source
- recognizable ML paper for portfolio demos
- rich enough to exercise section-aware chunking, retrieval, and citations

## Notes

- The repository does not redistribute the PDF directly.
- Download the PDF from the `paper_url` in `manifest.json` before running a live demo.

## Reproducible demo flow

From the repository root:

1. Download the tracked PDF:
   ```bash
   make fetch-sample-package
   ```
2. Start the app:
   ```bash
   make run-api
   ```
3. Upload `data/raw/attention-is-all-you-need.pdf` through the web UI or with:
   ```bash
   curl --fail --show-error -X POST \
     -F "file=@data/raw/attention-is-all-you-need.pdf;type=application/pdf" \
     http://127.0.0.1:8000/upload
   ```
4. Ask the demo questions from `questions.json` against `/ask`.
5. Inspect `/papers` or `/papers/<paper_id>/status` to show persisted registry metadata.

See the top-level `README.md` for the full end-to-end walkthrough, including evaluation and benchmark-report steps.
