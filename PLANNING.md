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
- [ ] Confidence estimation: retrieval fallback when no good match
- [ ] Logging module: per-request latency, token usage, model version
- [ ] Eval set expansion (30-50 QA pairs)
- [ ] Answer quality scoring (LLM-as-judge)

## Phase 3 — Production Polish
- [ ] Pipeline versioning: config-based experiment runner
- [ ] Regression testing: compare chunking v1 vs v2 on eval set
- [ ] Docker setup
- [ ] README with architecture diagram
- [ ] Web UI (optional lightweight frontend)

## Current priority order (Phase 2 next steps)
1. Chunking strategy v2: overlap + token-based fallback chunking
2. Reranking module (cross-encoder)
3. Structured extraction: dataset name extractor
4. Structured extraction: sample size extractor
5. Structured extraction: limitations extractor
6. Confidence estimation module
7. Logging module
8. Eval set expansion
9. Answer quality scoring (LLM-as-judge)
10. Pipeline versioning + experiment runner

## Notes
- Work on one item per session
- Commit after each item with a descriptive message
- Announce progress to parent session
- Keep each item achievable in one ~15-30 min coding session
