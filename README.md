# Reliable Scientific Paper Copilot

A local-first AI assistant for reading, understanding, and answering questions about scientific papers.

## Features

- **PDF Parsing**: Extract structured text and metadata from scientific papers
- **Section-Aware Chunking**: Split papers into meaningful chunks with section metadata
- **Embedding-Based Retrieval**: Find relevant passages using FAISS vector search
- **Grounded Generation**: Answer questions with citations from the paper

## Quick Start

```bash
pip install -r requirements.txt
python -m src.api.main
```

## API Endpoints

- `POST /upload` - Upload and process a PDF
- `POST /ask` - Ask a question about a processed paper
- `GET /health` - Health check

## Project Structure

```
reliable-paper-copilot/
├── configs/         # Configuration files
├── data/            # Data storage
│   ├── raw/         # Raw uploaded PDFs
│   ├── parsed/      # Parsed paper JSON
│   ├── chunks/      # Chunked text with metadata
│   └── eval/        # Evaluation data
├── src/
│   ├── parsing/     # PDF parsing module
│   ├── chunking/    # Section-aware chunking
│   ├── retrieval/   # Embedding and FAISS retrieval
│   ├── prompting/   # Prompt templates
│   ├── answering/   # Answer generation
│   ├── evaluation/  # Evaluation metrics
│   ├── api/         # FastAPI application
│   └── utils/       # Utility functions
├── scripts/         # Helper scripts
├── notebooks/       # Jupyter notebooks
├── tests/           # Unit tests
└── docker/          # Docker configuration
```

## Phase 1 MVP

- PDF parsing with pdfplumber
- Section-aware chunking
- FAISS-based retrieval with sentence-transformers
- FastAPI REST API
- Basic evaluation metrics
