"""FastAPI Application for Reliable Scientific Paper Copilot."""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import tempfile
import os
import json
import uuid
from pathlib import Path
import time

from ..parsing import parse_pdf, save_parsed
from ..chunking import chunk_by_sections, save_chunks
from ..retrieval import Retriever, create_retriever
from ..answering import SimpleAnswerGenerator
from ..storage import PaperRegistry
from ..utils import RequestLogger, compute_file_hash
from .web import WEB_UI_HTML


app = FastAPI(
    title="Reliable Scientific Paper Copilot",
    description="AI assistant for reading and answering questions about scientific papers",
    version="0.1.0"
)

# In-memory cache backed by a persistent registry.
PAPERS: Dict[str, Dict[str, Any]] = {}
REQUEST_LOGGER = RequestLogger()
PAPER_REGISTRY = PaperRegistry()


class QuestionRequest(BaseModel):
    paper_id: str
    question: str
    top_k: Optional[int] = 5


class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]
    num_chunks_retrieved: int


class PaperStatus(BaseModel):
    paper_id: str
    title: Optional[str]
    status: str
    num_chunks: int


@app.get("/", response_class=HTMLResponse)
async def web_ui():
    """Serve a lightweight browser UI for uploading papers and asking questions."""
    return HTMLResponse(WEB_UI_HTML)


def _hydrate_paper_cache(paper: Dict[str, Any]) -> Dict[str, Any]:
    cached = dict(paper)
    cached.setdefault("retriever", None)
    PAPERS[paper["paper_id"]] = cached
    return cached


for _paper in PAPER_REGISTRY.list_papers():
    _hydrate_paper_cache(_paper)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0", "papers": len(PAPERS)}


@app.post("/upload", response_model=PaperStatus)
async def upload_paper(file: UploadFile = File(...)):
    """
    Upload and process a PDF paper.
    
    Parses the PDF, chunks it by sections, and builds a retrieval index.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Generate paper ID
    paper_id = str(uuid.uuid4())

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        raw_dir = Path("data/raw")
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_pdf_path = raw_dir / f"{paper_id}.pdf"
        raw_pdf_path.write_bytes(content)

        # Parse PDF
        parsed = parse_pdf(tmp_path)
        parsed["paper_id"] = paper_id

        # Save parsed data
        data_dir = Path("data/parsed")
        data_dir.mkdir(parents=True, exist_ok=True)
        parsed_path = data_dir / f"{paper_id}_parsed.json"
        save_parsed(parsed, str(parsed_path))

        # Chunk by sections
        chunks = chunk_by_sections(parsed)

        # Save chunks
        chunks_dir = Path("data/chunks")
        chunks_dir.mkdir(parents=True, exist_ok=True)
        chunks_path = chunks_dir / f"{paper_id}_chunks.json"
        save_chunks(chunks, str(chunks_path))

        # Build retrieval index
        retriever = create_retriever(chunks)

        # Save index when available
        index_dir = Path("data/indexes")
        index_dir.mkdir(parents=True, exist_ok=True)
        index_path = index_dir / f"{paper_id}_index.faiss"
        if retriever.index is not None and not retriever.use_lexical_fallback:
            retriever.save(str(index_path), str(chunks_path))

        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        record = {
            "paper_id": paper_id,
            "title": parsed["metadata"].get("title", "Unknown"),
            "original_filename": file.filename,
            "status": "ready",
            "parsed_path": str(parsed_path),
            "chunks_path": str(chunks_path),
            "index_path": str(index_path),
            "raw_pdf_path": str(raw_pdf_path),
            "num_chunks": len(chunks),
            "page_count": parsed["metadata"].get("page_count", 0),
            "file_hash": compute_file_hash(str(raw_pdf_path)),
            "created_at": created_at,
        }
        PAPER_REGISTRY.upsert_paper(record)
        cached = _hydrate_paper_cache(record)
        cached["retriever"] = retriever

        return PaperStatus(
            paper_id=paper_id,
            title=record["title"],
            status=record["status"],
            num_chunks=record["num_chunks"],
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing paper: {str(e)}")
    finally:
        os.unlink(tmp_path)


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question about an uploaded paper.
    """
    paper = PAPERS.get(request.paper_id)
    if paper is None:
        registry_record = PAPER_REGISTRY.get_paper(request.paper_id)
        if registry_record is None:
            raise HTTPException(status_code=404, detail="Paper not found. Upload first.")
        paper = _hydrate_paper_cache(registry_record)
    
    if paper.get("status") != "ready":
        raise HTTPException(status_code=400, detail="Paper not ready for queries.")
    
    # Get or create retriever
    retriever = paper.get("retriever")
    if retriever is None:
        retriever = Retriever()
        if Path(paper["index_path"]).exists():
            retriever.load(paper["index_path"], paper["chunks_path"])
        else:
            chunks_payload = Path(paper["chunks_path"])
            if not chunks_payload.exists():
                raise HTTPException(status_code=500, detail="Paper artifacts are missing on disk.")
            with chunks_payload.open("r", encoding="utf-8") as handle:
                saved_chunks = json.load(handle).get("chunks", [])
            retriever.build_index(saved_chunks)
        paper["retriever"] = retriever
    
    # Create answer generator (using mock for now - replace with real LLM)
    generator = SimpleAnswerGenerator(retriever)
    
    started_at = time.perf_counter()

    # Generate answer
    result = generator.answer(request.question, top_k=request.top_k)
    latency_ms = (time.perf_counter() - started_at) * 1000

    REQUEST_LOGGER.log(
        REQUEST_LOGGER.create_event(
            endpoint="/ask",
            paper_id=request.paper_id,
            question=request.question,
            latency_ms=latency_ms,
            token_usage=result.get("token_usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
            model_version=result.get("model_version", "unknown"),
            extra={
                "num_chunks_retrieved": result.get("num_chunks_retrieved", 0),
                "sources": result.get("sources", []),
                "has_good_match": result.get("confidence", {}).get("has_good_match"),
            },
        )
    )

    return QuestionResponse(
        question=result["question"],
        answer=result["answer"],
        sources=result["sources"],
        num_chunks_retrieved=result["num_chunks_retrieved"]
    )


@app.get("/papers/{paper_id}/status", response_model=PaperStatus)
async def get_paper_status(paper_id: str):
    """Get status of an uploaded paper."""
    paper = PAPERS.get(paper_id)
    if paper is None:
        registry_record = PAPER_REGISTRY.get_paper(paper_id)
        if registry_record is None:
            raise HTTPException(status_code=404, detail="Paper not found")
        paper = _hydrate_paper_cache(registry_record)
    
    return PaperStatus(
        paper_id=paper_id,
        title=paper.get("title"),
        status=paper.get("status", "unknown"),
        num_chunks=paper.get("num_chunks", 0)
    )


@app.get("/papers")
async def list_papers():
    """List all uploaded papers."""
    papers = PAPER_REGISTRY.list_papers()
    for paper in papers:
        if paper["paper_id"] not in PAPERS:
            _hydrate_paper_cache(paper)

    return {
        "papers": [
            {
                "paper_id": paper["paper_id"],
                "title": paper.get("title"),
                "status": paper.get("status"),
                "num_chunks": paper.get("num_chunks", 0),
                "original_filename": paper.get("original_filename"),
                "page_count": paper.get("page_count", 0),
                "created_at": paper.get("created_at"),
            }
            for paper in papers
        ],
        "total": len(papers)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
