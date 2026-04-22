# Project Implementation Plan

## Phase 1 — MVP ✅
- [x] Repo scaffold
- [x] PDF parsing module
- [x] Section-aware chunking
- [x] Embedding + FAISS retrieval
- [x] Prompting + answer generation
- [x] FastAPI app
- [x] Basic evaluation metrics

## Phase 2 — Reliability ✅
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

## Phase 3 — Production Polish ✅
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
- [x] Web UI (optional lightweight frontend)

## Phase 4 — Portfolio Hardening
- [x] Add support for multiple real scientific PDFs with persistent paper registry metadata
  - [x] Sub-task 1: add a persistent paper registry and registry-backed API paper loading/listing across restarts
  - [x] Sub-task 2: extend ingestion/registry metadata with artifact validation summaries and file size metadata
  - [x] Sub-task 3: add richer real-paper metadata fields, such as ingestion notes and extracted summary metadata
    - [x] Sub-task 3a: persist extractor-derived study summary fields and ingestion-note hints in registry metadata
    - [x] Sub-task 3b: add paper-level operator-editable ingestion notes and provenance fields
    - [x] Sub-task 3c: surface richer paper metadata more clearly in the web UI
- [x] Add hybrid retrieval (BM25 + dense retrieval fusion)
  - [x] Sub-task 1: add retriever-level hybrid rank fusion between dense and lexical candidates
  - [x] Sub-task 2: expose hybrid retrieval settings through API/eval configs and surface scores in artifacts
  - [x] Sub-task 3: upgrade lexical retrieval from token overlap to BM25 scoring for stronger hybrid fusion
  - [x] Sub-task 4: expose hybrid retrieval controls and score breakdowns in the web UI for demos/debugging
- [x] Add citation span highlighting and page-aware evidence formatting in API/UI responses
  - [x] Sub-task 1: add page-aware structured evidence objects to chunk metadata, /ask responses, and the web UI evidence panel
  - [x] Sub-task 2: add answer-level citation span anchors/highlighting tied to evidence chunks in the UI
- [x] Add answerable-vs-unanswerable evaluation slice and refusal metrics
  - [x] Sub-task 1: add unanswerable eval examples plus core refusal and slice metrics in the evaluation pipeline
  - [x] Sub-task 2: surface answerable vs unanswerable results more clearly in benchmark/report outputs and docs
- [x] Add benchmark report generation (Markdown/HTML) summarizing accuracy, retrieval, latency, and cost
- [ ] Add ingestion smoke tests and end-to-end API tests
- [ ] Add Makefile / task runner for common workflows (ingest, eval, run-api, run-ui, compare-experiments)
- [ ] Add one polished demo notebook showing ingestion -> retrieval -> answer -> evaluation
- [ ] Add sample real-paper package and reproducible demo instructions
- [ ] Add deployment notes for local + split-host browser-assisted workflows if needed

## Current priority order
1. Add ingestion smoke tests and end-to-end API tests
2. Add Makefile / task runner
3. Add polished demo notebook
4. Add sample real-paper package and reproducible demo instructions
5. Add deployment notes for local + split-host browser-assisted workflows if needed

## Notes
- Work on one item per session
- Commit after each item with a descriptive message
- Announce progress to parent session
- Keep each item achievable in one ~15-30 min coding session
- Prefer portfolio-visible improvements now: demo quality, evaluation clarity, reproducibility, and real-paper support
