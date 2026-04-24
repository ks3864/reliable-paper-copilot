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
- [x] Add ingestion smoke tests and end-to-end API tests
  - [x] Sub-task 1: add upload and ingestion smoke coverage for artifact persistence and registry metadata
  - [x] Sub-task 2: add broader end-to-end API workflow coverage for upload -> ask -> status flows
- [x] Add Makefile / task runner for common workflows (ingest, eval, run-api, run-ui, compare-experiments)
- [x] Add one polished demo notebook showing ingestion -> retrieval -> answer -> evaluation
- [x] Add sample real-paper package and reproducible demo instructions
  - [x] Sub-task 1: add a versioned sample real-paper package manifest, demo questions, and fetch helper script
  - [x] Sub-task 2: document reproducible end-to-end demo steps that use the sample package
- [x] Add deployment notes for local + split-host browser-assisted workflows if needed

## Phase 5 — Demo Ergonomics
- [x] Add a demo-ready paper brief export endpoint
  - [x] Sub-task 1: add a compact `/papers/{paper_id}/brief` API view for summary metadata, study signals, and ingestion context
  - [x] Sub-task 2: add a UI action to copy or download the paper brief for demos
- [x] Add paper deletion workflow for demo reset and artifact cleanup
  - [x] Sub-task 1: add a registry-backed API delete route that removes persisted paper artifacts and clears cached paper state
  - [x] Sub-task 2: add a web UI delete action with confirmation and refresh the paper list after deletion

## Phase 6 — Reproducibility and Dev Ergonomics
- [x] Make the pytest suite runnable from a fresh checkout without manual `PYTHONPATH` setup
- [x] Add a demo script or Make target that runs the sample-package ingest and asks a canned demo question end-to-end
- [x] Add a recent paper activity endpoint and UI panel for demo question history

## Current priority order
1. Add operator-editable paper metadata fields in the web UI so provenance and manual notes can be updated without API calls.
   - [x] Sub-task 1: add a paper details editor in the web UI with save flow for operator notes plus provenance fields via the existing metadata API
   - [x] Sub-task 2: surface saved operator metadata update history more clearly in the web UI, including last update source/time

## Phase 7 — Demo Credibility Follow-ups
- [x] Persist operator metadata edit history and show real saved edits in the web UI

## Phase 8 — Multi-Paper Demo Usability
- [x] Add client-side paper search and newest-first sorting in the web UI paper picker

## Current priority order
1. Add richer recent-activity recap details for demo follow-up.
   - [x] Sub-task 1: include answer previews and evidence cues in recent paper activity API responses, transcript exports, and the web UI history panel.
   - [x] Sub-task 2: include retrieval configuration recaps in recent paper activity API responses, transcript exports, and the web UI history panel.

## Phase 9 — Demo Export Polish
- [x] Add a server-backed paper brief Markdown export endpoint for scripted demos and notes

## Current priority order
1. [x] Add question preset loading in the web UI from the packaged demo question set for faster live demos.

## Phase 10 — Evaluation Report Polish
- [x] Add answerability slice and refusal confusion breakdowns to benchmark report artifacts
  - [x] Sub-task 1: include answerable vs unanswerable slice tables plus refusal confusion counts in generated benchmark Markdown/HTML reports
  - [x] Sub-task 2: document how to read the new benchmark report slices in the README demo/eval workflow

## Phase 11 — Demo Follow-up Flow
- [x] Add recent question reuse actions in the web UI for faster live follow-up demos

## Phase 12 — Activity Recap Polish
- [x] Add richer aggregate recap summaries for recent paper activity
  - [x] Sub-task 1: add recent activity summary metrics to transcript exports and the web UI activity panel
  - [x] Sub-task 2: expose a structured activity summary object from the recent activity API for scripted consumers

## Phase 13 — Demo Handoff Polish
- [x] Add a combined demo recap Markdown export for handoff notes
  - [x] Sub-task 1: add a server-backed `/papers/{paper_id}/demo-recap/export` endpoint that combines the paper brief and recent activity recap into one Markdown artifact

## Phase 14 — Demo Export UX Polish
- [x] Add combined demo recap copy/download actions in the web UI
  - [x] Sub-task 1: wire the existing `/papers/{paper_id}/demo-recap/export` endpoint into UI buttons and preview behavior for live demos

## Phase 15 — Upload Provenance UX
- [x] Add optional upload-time provenance fields in the web UI and API so source label, source URL, and citation hint can be captured during ingestion

## Phase 16 — Demo Shareability
- [x] Add URL-backed web UI state for selected paper and demo preset so live demo views can be refreshed or shared without losing context

## Phase 17 — Demo Reset Ergonomics
- [x] Add paper activity reset workflow for live demos
  - [x] Sub-task 1: add an API route to clear persisted per-paper ask history without deleting the paper
  - [x] Sub-task 2: add a web UI clear-history action with confirmation and refresh the activity panel afterward

## Phase 18 — Provenance Handoff Exports
- [x] Add operator metadata history Markdown export for provenance review and demo handoff
  - [x] Sub-task 1: add a server-backed `/papers/{paper_id}/metadata/history/export` endpoint that exports recent operator metadata edits as Markdown

## Phase 19 — Metadata Export UX
- [x] Add operator metadata history copy/download actions in the web UI
  - [x] Sub-task 1: wire the existing `/papers/{paper_id}/metadata/history/export` endpoint into UI buttons and preview behavior for live provenance handoff

## Phase 20 — Repo Hygiene
- [x] Ignore runtime-generated local data artifacts so demo runs do not leave noisy untracked files in git status

## Phase 21 — Demo Library Overview
- [x] Add aggregate paper-library summary stats in the API and web UI for faster demo setup checks

## Phase 22 — Demo Library Snapshot Export
- [x] Add shareable paper-library snapshot export workflow for demo setup and handoff
  - [x] Sub-task 1: add a server-backed `/papers/summary/export` Markdown endpoint for the aggregate library snapshot
  - [x] Sub-task 2: add web UI copy/download actions for the library snapshot export

## Current priority order
1. [x] Add a small export-status polish pass for library snapshot actions if preview or clipboard failures need clearer UI messaging.

## Phase 23 — URL-backed Retrieval Presets
- [x] Add URL-backed retrieval controls in the web UI so demo retrieval setup can survive refreshes and shared links
  - [x] Sub-task 1: sync the selected retrieval mode with the web UI URL state and restore it on load
  - [x] Sub-task 2: extend URL-backed state to include advanced retrieval knobs such as top-k and hybrid weights

## Phase 24 — Test Stability
- [x] Make retrieval reranking tests deterministic across environments with or without local ML dependencies
  - [x] Sub-task 1: patch retrieval test doubles directly into the reranking test module instead of relying on optional dependency import state

## Current priority order
1. [x] Add a small benchmark artifact UX polish pass so report exports are easier to inspect from the repo and demo flow.
   - [x] Sub-task 1: add a compact benchmark run index Markdown artifact that links the latest generated report outputs per experiment.

## Phase 25 — Benchmark Index Scanability
- [x] Add key summary metrics to the benchmark run index artifact so the latest experiment quality is scannable without opening each report
  - [x] Sub-task 1: include generated-at, QA-pair count, exact match, F1, retrieval hit, and refusal accuracy columns in `benchmark_run_index.md`

## Current priority order
1. [x] Add a small README polish pass so the benchmark run index workflow is easier to discover from the repo root.
   - [x] Sub-task 1: document where `benchmark_run_index.md` is generated and how to use it after evaluation runs.

## Phase 26 — Benchmark Artifact Navigation
- [x] Add direct latest-run folder links to the benchmark run index for faster artifact inspection from the repo root
  - [x] Sub-task 1: include a `run-dir` link alongside per-file artifact links in `benchmark_run_index.md`

## Phase 27 — Export Action UX Consistency
- [x] Add preview-aware clipboard and download fallback messaging for paper-scoped Markdown exports in the web UI

## Phase 28 — Benchmark Report Context Polish
- [x] Add retrieval configuration recap to benchmark report artifacts
  - [x] Sub-task 1: include retrieval mode, top-k, fusion weights, embedding model, and chunk profile in generated benchmark Markdown/HTML reports

## Phase 29 — Benchmark Index Summary Scanability
- [x] Add a compact quick-summary block to the benchmark run index so the newest run and best latest F1 are visible before opening individual artifacts
  - [x] Sub-task 1: surface indexed experiment count plus newest-run and best-latest-F1 summary lines at the top of `benchmark_run_index.md`

## Phase 30 — Benchmark Index Quick Summary Links
- [x] Add direct artifact links to the benchmark run index quick-summary recap lines
  - [x] Sub-task 1: link the newest-run and best-latest-F1 recap entries directly to the latest run directory and artifact set

## Phase 31 — Benchmark Snapshot API for Demo Credibility
- [x] Add a latest-benchmark snapshot API endpoint for demo credibility and artifact navigation
  - [x] Sub-task 1: add a server-backed `/benchmark/latest` endpoint that surfaces the newest persisted evaluation metrics, retrieval config, and artifact paths
  - [ ] Sub-task 2: surface the latest benchmark snapshot in the web UI for live demo credibility checks

## Current priority order
1. Surface the latest benchmark snapshot in the web UI for live demo credibility checks.

## Notes
- Work on one item per session
- Commit after each item with a descriptive message
- Announce progress to parent session
- Keep each item achievable in one ~15-30 min coding session
- Prefer portfolio-visible improvements now: demo quality, evaluation clarity, reproducibility, and real-paper support
