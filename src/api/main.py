"""FastAPI Application for Reliable Scientific Paper Copilot."""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import tempfile
import os
import uuid
from pathlib import Path
import time

from ..parsing import parse_pdf, save_parsed, load_parsed
from ..chunking import chunk_by_sections, save_chunks, load_chunks
from ..retrieval import Retriever, create_retriever
from ..answering import AnswerGenerator, SimpleAnswerGenerator
from ..utils import RequestLogger
from .web import WEB_UI_HTML


app = FastAPI(
    title="Reliable Scientific Paper Copilot",
    description="AI assistant for reading and answering questions about scientific papers",
    version="0.1.0"
)

# In-memory storage for uploaded papers
# In production, use a proper database
PAPERS: Dict[str, Dict[str, Any]] = {}
REQUEST_LOGGER = RequestLogger()


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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


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
        
        # Save index
        index_dir = Path("data/indexes")
        index_dir.mkdir(parents=True, exist_ok=True)
        index_path = index_dir / f"{paper_id}_index.faiss"
        retriever.save(str(index_path), str(chunks_path))
        
        # Store in memory
        PAPERS[paper_id] = {
            "paper_id": paper_id,
            "title": parsed["metadata"].get("title", "Unknown"),
            "status": "ready",
            "parsed_path": str(parsed_path),
            "chunks_path": str(chunks_path),
            "index_path": str(index_path),
            "num_chunks": len(chunks),
            "retriever": retriever
        }
        
        return PaperStatus(
            paper_id=paper_id,
            title=parsed["metadata"].get("title"),
            status="ready",
            num_chunks=len(chunks)
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
        raise HTTPException(status_code=404, detail="Paper not found. Upload first.")
    
    if paper.get("status") != "ready":
        raise HTTPException(status_code=400, detail="Paper not ready for queries.")
    
    # Get or create retriever
    retriever = paper.get("retriever")
    if retriever is None:
        # Load from disk
        retriever = Retriever()
        retriever.load(paper["index_path"], paper["chunks_path"])
    
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
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return PaperStatus(
        paper_id=paper_id,
        title=paper.get("title"),
        status=paper.get("status", "unknown"),
        num_chunks=paper.get("num_chunks", 0)
    )


@app.get("/papers")
async def list_papers():
    """List all uploaded papers."""
    return {
        "papers": [
            {"paper_id": pid, "title": p.get("title"), "status": p.get("status")}
            for pid, p in PAPERS.items()
        ],
        "total": len(PAPERS)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
