PYTHON ?= python
API_HOST ?= 127.0.0.1
API_PORT ?= 8000
API_URL ?= http://$(API_HOST):$(API_PORT)
EVAL_CONFIG ?= configs/experiments/baseline.yaml
OUTPUT_DIR ?= artifacts/experiments
BASELINE ?=
CANDIDATE ?=
REPORT_RESULTS ?=
PAPER ?=
QUESTION_ID ?=
RETRIEVAL_MODE ?= hybrid
DEMO_ARTIFACTS_DIR ?= artifacts/demo

.PHONY: help install test run-api run-ui ingest-check ingest fetch-sample-package demo-sample-package eval compare-experiments benchmark-report

help:
	@printf "Reliable Scientific Paper Copilot workflows\n\n"
	@printf "  make install                              Install Python dependencies\n"
	@printf "  make test                                 Run the test suite\n"
	@printf "  make run-api                              Start the FastAPI app\n"
	@printf "  make run-ui                               Start the app for browser UI work\n"
	@printf "  make ingest PAPER=path/to/paper.pdf       Upload a PDF to the local API\n"
	@printf "  make fetch-sample-package                 Download the tracked sample real-paper PDF\n"
	@printf "  make demo-sample-package [QUESTION_ID=architecture RETRIEVAL_MODE=hybrid]\n"
	@printf "                                           Run the packaged sample-paper ingest + canned QA flow and persist artifacts/demo output\n"
	@printf "  make eval [EVAL_CONFIG=... OUTPUT_DIR=...] Run the evaluation pipeline\n"
	@printf "  make compare-experiments BASELINE=... CANDIDATE=...\n"
	@printf "                                           Compare two results.json files\n"
	@printf "  make benchmark-report REPORT_RESULTS=...  Render Markdown + HTML benchmark reports\n"

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest

run-api:
	$(PYTHON) -m src.api.main

run-ui: run-api

ingest-check:
	@if [ -z "$(PAPER)" ]; then \
		echo "Set PAPER=path/to/paper.pdf"; \
		exit 1; \
	fi
	@if [ ! -f "$(PAPER)" ]; then \
		echo "Paper not found: $(PAPER)"; \
		exit 1; \
	fi

ingest: ingest-check
	curl --fail --show-error -X POST \
		-F "file=@$(PAPER);type=application/pdf" \
		$(API_URL)/upload
	@printf "\n"

fetch-sample-package:
	$(PYTHON) scripts/fetch_sample_package.py

demo-sample-package:
	$(PYTHON) scripts/run_sample_demo.py $(if $(QUESTION_ID),--question-id $(QUESTION_ID),) --retrieval-mode $(RETRIEVAL_MODE) --artifacts-dir $(DEMO_ARTIFACTS_DIR)

eval:
	$(PYTHON) scripts/run_evaluation.py --config $(EVAL_CONFIG) --output-dir $(OUTPUT_DIR)

compare-experiments:
	@if [ -z "$(BASELINE)" ] || [ -z "$(CANDIDATE)" ]; then \
		echo "Set BASELINE=/path/to/results.json and CANDIDATE=/path/to/results.json"; \
		exit 1; \
	fi
	$(PYTHON) scripts/compare_experiments.py $(BASELINE) $(CANDIDATE)

benchmark-report:
	@if [ -z "$(REPORT_RESULTS)" ]; then \
		echo "Set REPORT_RESULTS=/path/to/results.json"; \
		exit 1; \
	fi
	$(PYTHON) scripts/generate_benchmark_report.py $(REPORT_RESULTS)
