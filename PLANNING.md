# Project Implementation Plan

## Phase 1 — MVP ✅
- [x] Repo scaffold
- [x] PDF parsing module
- [x] Section-aware chunking
- [x] Embedding + FAISS retrieval
- [x] Prompting + answer generation
- [x] FastAPI app
- [x] Basic evaluation metrics

## Phase 2 — Reliability
- [x] Chunking strategy v2: overlap + token-based fallback chunking
- [x] Reranking module (cross-encoder)
- [x] Structured extraction: dataset name extractor
- [x] Structured extraction: sample size extractor
- [x] Structured extraction: limitations extractor
- [x] Structured extraction: inclusion/exclusion criteria extractor
- [x] Confidence estimation: retrieval fallback when no good match
- [x] Logging module: per-request latency, token usage, model version
- [x] Eval set expansion (30-50 QA pairs)
  - [x] Sub-task 1: expand the synthetic sample-paper eval set from 6 to 18 QA pairs
  - [x] Sub-task 2: add additional papers / QA coverage to reach 30-50 total QA pairs
- [x] Answer quality scoring (LLM-as-judge)

## Phase 3 — Production Polish
- [x] Pipeline versioning: config-based experiment runner
  - [x] Sub-task 1: add a baseline experiment config and reusable config loader/runner
  - [x] Sub-task 2: persist experiment outputs and versioned summaries
- [x] Regression testing: compare chunking v1 vs v2 on eval set
  - [x] Sub-task 1: add a regression comparison utility and CLI for comparing two experiment result payloads
  - [x] Sub-task 2: add chunking-v1 and chunking-v2 experiment configs and generate comparable runs on the eval set
- [x] Docker setup
  - [x] Sub-task 1: add a minimal Dockerfile and .dockerignore for running the FastAPI app
  - [x] Sub-task 2: add a compose file and README instructions for running the FastAPI app with a persistent data volume
- [x] README with architecture diagram
- [ ] Web UI (optional lightweight frontend)

## Current priority order
1. Pipeline versioning: config-based experiment runner
2. Regression testing: compare chunking v1 vs v2 on eval set
3. Docker setup
4. README with architecture diagram
5. Web UI (optional lightweight frontend)

## Notes
- Work on one item per session
- Commit after each item with a descriptive message
- Announce progress to parent session
- Keep each item achievable in one ~15-30 min coding session
