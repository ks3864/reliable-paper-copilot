"""FastAPI Application for Reliable Scientific Paper Copilot."""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import tempfile
import os
import json
import uuid
from pathlib import Path
import time
import re

from ..parsing import parse_pdf, save_parsed
from ..chunking import chunk_by_sections, save_chunks
from ..retrieval import Retriever, create_retriever
from ..answering import SimpleAnswerGenerator
from ..storage import PaperRegistry, build_ingestion_notes, build_provenance_metadata, build_summary_metadata
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
    retrieval_mode: Optional[str] = None
    lexical_weight: Optional[float] = None
    dense_weight: Optional[float] = None
    rrf_k: Optional[int] = None


class RetrievedChunkScore(BaseModel):
    chunk_id: Optional[int] = None
    section: str
    retrieval_score: float
    dense_score: Optional[float] = None
    lexical_score: Optional[float] = None
    hybrid_score: Optional[float] = None
    rank: Optional[int] = None
    dense_rank: Optional[int] = None
    lexical_rank: Optional[int] = None


class EvidenceItem(BaseModel):
    chunk_id: Optional[int] = None
    section: str
    text: str
    page_numbers: List[int] = []
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    page_label: Optional[str] = None
    retrieval_score: float
    dense_score: Optional[float] = None
    lexical_score: Optional[float] = None
    hybrid_score: Optional[float] = None
    rank: Optional[int] = None


class AnswerCitation(BaseModel):
    citation_id: str
    label: str
    chunk_id: Optional[int] = None
    section: str
    page_label: Optional[str] = None
    sentence_index: int
    sentence_text: str


class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]
    num_chunks_retrieved: int
    retrieval_mode: str
    retrieval_scores: List[RetrievedChunkScore]
    evidence: List[EvidenceItem]
    answer_citations: List[AnswerCitation]


class PaperStatus(BaseModel):
    paper_id: str
    title: Optional[str]
    status: str
    num_chunks: int
    artifact_validation: Optional[Dict[str, Any]] = None
    ingestion_notes: List[str] = []
    operator_ingestion_notes: List[str] = []
    operator_metadata_history: List[Dict[str, Any]] = []
    provenance: Optional[Dict[str, Any]] = None
    summary_metadata: Optional[Dict[str, Any]] = None


class PaperMetadataUpdateRequest(BaseModel):
    operator_ingestion_notes: Optional[List[str]] = None
    provenance: Optional[Dict[str, Any]] = None


class PaperBrief(BaseModel):
    paper_id: str
    title: Optional[str]
    status: str
    original_filename: Optional[str] = None
    created_at: Optional[str] = None
    overview: Dict[str, Any]
    study_signals: Dict[str, Any]
    ingestion: Dict[str, Any]


class PaperDeleteResponse(BaseModel):
    paper_id: str
    deleted: bool
    deleted_artifacts: List[str] = []


class PaperActivityItem(BaseModel):
    timestamp: str
    question: Optional[str] = None
    answer_preview: Optional[str] = None
    evidence_labels: List[str] = []
    latency_ms: float
    num_chunks_retrieved: int = 0
    has_good_match: Optional[bool] = None
    model_version: str
    token_usage: Dict[str, int] = {}
    sources: List[str] = []
    retrieval_mode: Optional[str] = None
    top_k: Optional[int] = None
    dense_weight: Optional[float] = None
    lexical_weight: Optional[float] = None
    rrf_k: Optional[int] = None


def _get_paper_or_404(paper_id: str) -> Dict[str, Any]:
    paper = PAPERS.get(paper_id)
    if paper is None:
        registry_record = PAPER_REGISTRY.get_paper(paper_id)
        if registry_record is None:
            raise HTTPException(status_code=404, detail="Paper not found")
        paper = _hydrate_paper_cache(registry_record)
    return paper


@app.get("/", response_class=HTMLResponse)
async def web_ui():
    """Serve a lightweight browser UI for uploading papers and asking questions."""
    return HTMLResponse(WEB_UI_HTML)


def _hydrate_paper_cache(paper: Dict[str, Any]) -> Dict[str, Any]:
    cached = dict(paper)
    cached.setdefault("retriever", None)
    PAPERS[paper["paper_id"]] = cached
    return cached


def _load_saved_chunks(chunks_path: str) -> List[Dict[str, Any]]:
    with Path(chunks_path).open("r", encoding="utf-8") as handle:
        return json.load(handle).get("chunks", [])


def _build_paper_brief(paper: Dict[str, Any]) -> PaperBrief:
    summary_metadata = paper.get("summary_metadata") or {}
    extracted_summary = summary_metadata.get("extracted_summary") or {}
    provenance = paper.get("provenance") or {}
    artifact_validation = paper.get("artifact_validation") or {}

    return PaperBrief(
        paper_id=paper["paper_id"],
        title=paper.get("title"),
        status=paper.get("status", "unknown"),
        original_filename=paper.get("original_filename"),
        created_at=paper.get("created_at"),
        overview={
            "authors": summary_metadata.get("authors") or [],
            "abstract_preview": summary_metadata.get("abstract_preview"),
            "page_count": paper.get("page_count", 0),
            "num_chunks": paper.get("num_chunks", 0),
            "section_count": summary_metadata.get("section_count", 0),
            "section_names": summary_metadata.get("section_names") or [],
            "total_word_count": summary_metadata.get("total_word_count", 0),
            "tables_count": summary_metadata.get("tables_count", 0),
            "chunking_strategies": summary_metadata.get("chunking_strategies") or {},
        },
        study_signals={
            "datasets": extracted_summary.get("datasets") or [],
            "sample_sizes": extracted_summary.get("sample_sizes") or [],
            "limitations": extracted_summary.get("limitations") or [],
            "inclusion_criteria": extracted_summary.get("inclusion_criteria") or [],
            "exclusion_criteria": extracted_summary.get("exclusion_criteria") or [],
            "counts": extracted_summary.get("counts") or {},
        },
        ingestion={
            "artifact_validation": artifact_validation,
            "ingestion_notes": paper.get("ingestion_notes") or [],
            "operator_ingestion_notes": paper.get("operator_ingestion_notes") or [],
            "operator_metadata_history": paper.get("operator_metadata_history") or [],
            "provenance": provenance,
        },
    )


def _format_page_label(page_numbers: List[int]) -> Optional[str]:
    if not page_numbers:
        return None
    if len(page_numbers) == 1:
        return f"p. {page_numbers[0]}"
    return f"pp. {page_numbers[0]}-{page_numbers[-1]}"


def _build_evidence_item(chunk: Dict[str, Any]) -> EvidenceItem:
    metadata = chunk.get("metadata") or {}
    page_numbers = [int(page) for page in metadata.get("page_numbers", []) if page is not None]
    snippet = (chunk.get("text") or "").strip()

    return EvidenceItem(
        chunk_id=chunk.get("chunk_id"),
        section=chunk.get("section", "unknown"),
        text=snippet,
        page_numbers=page_numbers,
        page_start=metadata.get("page_start"),
        page_end=metadata.get("page_end"),
        page_label=_format_page_label(page_numbers),
        retrieval_score=float(chunk.get("retrieval_score", 0.0)),
        dense_score=chunk.get("dense_score"),
        lexical_score=chunk.get("lexical_score"),
        hybrid_score=chunk.get("hybrid_score"),
        rank=chunk.get("rank"),
    )


def _split_answer_sentences(answer: str) -> List[str]:
    cleaned_answer = (answer or "").strip()
    if not cleaned_answer:
        return []

    collapsed = re.sub(r"\s+", " ", cleaned_answer)
    segments = re.split(r"(?<=[.!?])\s+|\n+", collapsed)
    return [segment.strip() for segment in segments if segment.strip()]


def _build_answer_citations(answer: str, retrieved_chunks: List[Dict[str, Any]]) -> List[AnswerCitation]:
    sentences = _split_answer_sentences(answer)
    if not sentences or not retrieved_chunks:
        return []

    citations: List[AnswerCitation] = []
    usable_chunks = retrieved_chunks[: len(sentences)]
    for index, sentence in enumerate(sentences):
        chunk = usable_chunks[min(index, len(usable_chunks) - 1)]
        evidence = _build_evidence_item(chunk)
        citations.append(
            AnswerCitation(
                citation_id=f"citation-{index + 1}",
                label=f"[{index + 1}]",
                chunk_id=evidence.chunk_id,
                section=evidence.section,
                page_label=evidence.page_label,
                sentence_index=index,
                sentence_text=sentence,
            )
        )

    return citations


def _format_activity_match_label(has_good_match: Optional[bool]) -> str:
    if has_good_match is None:
        return "Match quality unknown"
    return "Good retrieval match" if has_good_match else "Fallback or weak retrieval match"


def _build_activity_answer_preview(answer: Optional[str], limit: int = 240) -> Optional[str]:
    cleaned = re.sub(r"\s+", " ", (answer or "").strip())
    if not cleaned:
        return None
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 1)].rstrip() + "…"


def _build_activity_evidence_labels(chunks: List[Dict[str, Any]], limit: int = 3) -> List[str]:
    labels: List[str] = []
    for chunk in chunks[:limit]:
        evidence = _build_evidence_item(chunk)
        location = f" ({evidence.page_label})" if evidence.page_label else ""
        labels.append(f"{evidence.section}{location}")
    return labels



def _format_activity_retrieval_config(event: Dict[str, Any]) -> str:
    retrieval_mode = event.get("retrieval_mode") or "dense"
    top_k = int(event.get("top_k", 0) or 0)
    dense_weight = event.get("dense_weight")
    lexical_weight = event.get("lexical_weight")
    rrf_k = event.get("rrf_k")

    parts = [f"mode={retrieval_mode}"]
    if top_k:
        parts.append(f"top_k={top_k}")
    if dense_weight is not None:
        parts.append(f"dense_weight={float(dense_weight):.2f}")
    if lexical_weight is not None:
        parts.append(f"lexical_weight={float(lexical_weight):.2f}")
    if rrf_k is not None:
        parts.append(f"rrf_k={int(rrf_k)}")
    return ", ".join(parts)



def _build_activity_markdown(paper: Dict[str, Any], events: List[Dict[str, Any]]) -> str:
    title = paper.get("title") or paper.get("paper_id") or "Unknown paper"
    provenance = paper.get("provenance") or {}
    lines = [
        f"# Recent activity transcript for {title}",
        "",
        f"- Paper ID: {paper.get('paper_id', 'unknown')}",
        f"- Status: {paper.get('status', 'unknown')}",
        f"- Original filename: {paper.get('original_filename') or 'Unknown'}",
        f"- Source label: {provenance.get('source_label') or 'Unknown'}",
        f"- Generated at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"- Included activity items: {len(events)}",
        "",
    ]

    if not events:
        lines.extend([
            "## Activity",
            "",
            "No recent question activity was recorded for this paper.",
        ])
        return "\n".join(lines)

    lines.extend(["## Activity", ""])
    for index, event in enumerate(events, start=1):
        token_usage = event.get("token_usage") or {}
        lines.extend(
            [
                f"### {index}. {event.get('question') or 'Unknown question'}",
                f"- Timestamp: {event.get('timestamp') or 'Unknown'}",
                f"- Latency: {float(event.get('latency_ms', 0.0)):.2f} ms",
                f"- Retrieved chunks: {int(event.get('num_chunks_retrieved', 0))}",
                f"- Match status: {_format_activity_match_label(event.get('has_good_match'))}",
                f"- Model version: {event.get('model_version') or 'unknown'}",
                f"- Retrieval config: {_format_activity_retrieval_config(event)}",
                f"- Token usage: prompt={int(token_usage.get('prompt_tokens', 0))}, completion={int(token_usage.get('completion_tokens', 0))}, total={int(token_usage.get('total_tokens', 0))}",
                f"- Sources: {', '.join(event.get('sources') or []) or 'None'}",
                f"- Answer preview: {event.get('answer_preview') or 'Not captured'}",
                f"- Evidence cues: {', '.join(event.get('evidence_labels') or []) or 'None'}",
                "",
            ]
        )

    return "\n".join(lines)



def _get_retriever_for_request(paper: Dict[str, Any], request: QuestionRequest) -> Retriever:
    retrieval_mode = request.retrieval_mode or "dense"
    lexical_weight = request.lexical_weight if request.lexical_weight is not None else 1.0
    dense_weight = request.dense_weight if request.dense_weight is not None else 1.0
    rrf_k = request.rrf_k if request.rrf_k is not None else 60

    is_default_dense = (
        retrieval_mode == "dense"
        and lexical_weight == 1.0
        and dense_weight == 1.0
        and rrf_k == 60
    )

    if is_default_dense:
        retriever = paper.get("retriever")
        if retriever is None:
            retriever = Retriever()
            if Path(paper["index_path"]).exists():
                retriever.load(paper["index_path"], paper["chunks_path"])
            else:
                saved_chunks = _load_saved_chunks(paper["chunks_path"])
                retriever.build_index(saved_chunks)
            paper["retriever"] = retriever
        return retriever

    saved_chunks = _load_saved_chunks(paper["chunks_path"])
    return create_retriever(
        saved_chunks,
        retrieval_mode=retrieval_mode,
        lexical_weight=float(lexical_weight),
        dense_weight=float(dense_weight),
        rrf_k=int(rrf_k),
    )


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
        index_persisted = False
        if retriever.index is not None and not retriever.use_lexical_fallback:
            retriever.save(str(index_path), str(chunks_path))
            index_persisted = True

        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        file_hash = compute_file_hash(str(raw_pdf_path))
        record = {
            "paper_id": paper_id,
            "title": parsed["metadata"].get("title", "Unknown"),
            "original_filename": file.filename,
            "status": "ready",
            "parsed_path": str(parsed_path.resolve()),
            "chunks_path": str(chunks_path.resolve()),
            "index_path": str(index_path.resolve()),
            "raw_pdf_path": str(raw_pdf_path.resolve()),
            "num_chunks": len(chunks),
            "page_count": parsed["metadata"].get("page_count", 0),
            "file_size_bytes": len(content),
            "file_hash": file_hash,
            "created_at": created_at,
            "ingestion_notes": build_ingestion_notes(parsed, chunks, index_persisted=index_persisted),
            "operator_ingestion_notes": [],
            "provenance": build_provenance_metadata(
                original_filename=file.filename,
                file_hash=file_hash,
                created_at=created_at,
            ),
            "summary_metadata": build_summary_metadata(parsed, chunks),
        }
        PAPER_REGISTRY.upsert_paper(record)
        persisted_record = PAPER_REGISTRY.get_paper(paper_id) or record
        cached = _hydrate_paper_cache(persisted_record)
        cached["retriever"] = retriever

        return PaperStatus(
            paper_id=paper_id,
            title=persisted_record["title"],
            status=persisted_record["status"],
            num_chunks=persisted_record["num_chunks"],
            artifact_validation=persisted_record.get("artifact_validation"),
            ingestion_notes=persisted_record.get("ingestion_notes", []),
            operator_ingestion_notes=persisted_record.get("operator_ingestion_notes", []),
            operator_metadata_history=persisted_record.get("operator_metadata_history", []),
            provenance=persisted_record.get("provenance"),
            summary_metadata=persisted_record.get("summary_metadata"),
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
    
    if not Path(paper["chunks_path"]).exists():
        raise HTTPException(status_code=500, detail="Paper artifacts are missing on disk.")

    retriever = _get_retriever_for_request(paper, request)
    retrieval_mode = request.retrieval_mode or "dense"
    lexical_weight = float(request.lexical_weight if request.lexical_weight is not None else 1.0)
    dense_weight = float(request.dense_weight if request.dense_weight is not None else 1.0)
    rrf_k = int(request.rrf_k if request.rrf_k is not None else 60)
    top_k = int(request.top_k if request.top_k is not None else 5)

    # Create answer generator (using mock for now - replace with real LLM)
    generator = SimpleAnswerGenerator(retriever)
    
    started_at = time.perf_counter()

    # Generate answer
    result = generator.answer(request.question, top_k=top_k)
    latency_ms = (time.perf_counter() - started_at) * 1000
    answer_preview = _build_activity_answer_preview(result.get("answer"))
    evidence_labels = _build_activity_evidence_labels(result.get("retrieved_chunks", []))

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
                "answer_preview": answer_preview,
                "evidence_labels": evidence_labels,
                "retrieval_mode": retrieval_mode,
                "top_k": top_k,
                "dense_weight": dense_weight,
                "lexical_weight": lexical_weight,
                "rrf_k": rrf_k,
            },
        )
    )

    return QuestionResponse(
        question=result["question"],
        answer=result["answer"],
        sources=result["sources"],
        num_chunks_retrieved=result["num_chunks_retrieved"],
        retrieval_mode=retriever.retrieval_mode,
        evidence=[_build_evidence_item(chunk) for chunk in result.get("retrieved_chunks", [])],
        answer_citations=_build_answer_citations(result["answer"], result.get("retrieved_chunks", [])),
        retrieval_scores=[
            RetrievedChunkScore(
                chunk_id=chunk.get("chunk_id"),
                section=chunk.get("section", "unknown"),
                retrieval_score=float(chunk.get("retrieval_score", 0.0)),
                dense_score=chunk.get("dense_score"),
                lexical_score=chunk.get("lexical_score"),
                hybrid_score=chunk.get("hybrid_score"),
                rank=chunk.get("rank"),
                dense_rank=chunk.get("dense_rank"),
                lexical_rank=chunk.get("lexical_rank"),
            )
            for chunk in result.get("retrieved_chunks", [])
        ],
    )


@app.get("/papers/{paper_id}/status", response_model=PaperStatus)
async def get_paper_status(paper_id: str):
    """Get status of an uploaded paper."""
    paper = _get_paper_or_404(paper_id)

    return PaperStatus(
        paper_id=paper_id,
        title=paper.get("title"),
        status=paper.get("status", "unknown"),
        num_chunks=paper.get("num_chunks", 0),
        artifact_validation=paper.get("artifact_validation"),
        ingestion_notes=paper.get("ingestion_notes", []),
        operator_ingestion_notes=paper.get("operator_ingestion_notes", []),
        operator_metadata_history=paper.get("operator_metadata_history", []),
        provenance=paper.get("provenance"),
        summary_metadata=paper.get("summary_metadata"),
    )


@app.get("/papers/{paper_id}/brief", response_model=PaperBrief)
async def get_paper_brief(paper_id: str):
    """Return a compact, demo-friendly summary of a paper and its ingestion metadata."""
    paper = _get_paper_or_404(paper_id)

    return _build_paper_brief(paper)


@app.get("/papers/{paper_id}/activity", response_model=List[PaperActivityItem])
async def get_paper_activity(paper_id: str, limit: int = 10):
    """Return recent ask activity for a paper to support demo review and debugging."""
    _get_paper_or_404(paper_id)

    safe_limit = max(1, min(limit, 50))
    events = REQUEST_LOGGER.read_events(paper_id=paper_id, endpoint="/ask", limit=safe_limit)
    return [
        PaperActivityItem(
            timestamp=event.get("timestamp", ""),
            question=event.get("question"),
            answer_preview=event.get("answer_preview"),
            evidence_labels=event.get("evidence_labels") or [],
            latency_ms=float(event.get("latency_ms", 0.0)),
            num_chunks_retrieved=int(event.get("num_chunks_retrieved", 0)),
            has_good_match=event.get("has_good_match"),
            model_version=event.get("model_version", "unknown"),
            token_usage=event.get("token_usage") or {},
            sources=event.get("sources") or [],
            retrieval_mode=event.get("retrieval_mode"),
            top_k=event.get("top_k"),
            dense_weight=event.get("dense_weight"),
            lexical_weight=event.get("lexical_weight"),
            rrf_k=event.get("rrf_k"),
        )
        for event in events
    ]


@app.get("/papers/{paper_id}/activity/export", response_class=PlainTextResponse)
async def export_paper_activity_markdown(paper_id: str, limit: int = 10):
    """Return recent ask activity for a paper as a shareable Markdown transcript."""
    paper = _get_paper_or_404(paper_id)
    safe_limit = max(1, min(limit, 50))
    events = REQUEST_LOGGER.read_events(paper_id=paper_id, endpoint="/ask", limit=safe_limit)
    return PlainTextResponse(
        _build_activity_markdown(paper, events),
        media_type="text/markdown; charset=utf-8",
    )


@app.patch("/papers/{paper_id}/metadata", response_model=PaperStatus)
async def update_paper_metadata(paper_id: str, request: PaperMetadataUpdateRequest):
    """Update operator-managed notes and provenance metadata for a paper."""
    updated = PAPER_REGISTRY.update_operator_metadata(
        paper_id,
        operator_ingestion_notes=request.operator_ingestion_notes,
        provenance=request.provenance,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    cached = PAPERS.get(paper_id)
    if cached is not None:
        cached.update(
            operator_ingestion_notes=updated.get("operator_ingestion_notes", []),
            operator_metadata_history=updated.get("operator_metadata_history", []),
            provenance=updated.get("provenance"),
            artifact_validation=updated.get("artifact_validation"),
        )

    return PaperStatus(
        paper_id=updated["paper_id"],
        title=updated.get("title"),
        status=updated.get("status", "unknown"),
        num_chunks=updated.get("num_chunks", 0),
        artifact_validation=updated.get("artifact_validation"),
        ingestion_notes=updated.get("ingestion_notes", []),
        operator_ingestion_notes=updated.get("operator_ingestion_notes", []),
        operator_metadata_history=updated.get("operator_metadata_history", []),
        provenance=updated.get("provenance"),
        summary_metadata=updated.get("summary_metadata"),
    )


@app.delete("/papers/{paper_id}", response_model=PaperDeleteResponse)
async def delete_paper(paper_id: str):
    """Delete a paper from the registry and remove persisted artifacts when present."""
    deleted = PAPER_REGISTRY.delete_paper(paper_id, delete_artifacts=True)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    PAPERS.pop(paper_id, None)

    deleted_artifacts = []
    artifact_validation = deleted.get("artifact_validation") or {}
    for field, metadata in (artifact_validation.get("artifacts") or {}).items():
        path_value = metadata.get("path")
        if path_value:
            deleted_artifacts.append(field)

    return PaperDeleteResponse(
        paper_id=paper_id,
        deleted=True,
        deleted_artifacts=deleted_artifacts,
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
                "file_size_bytes": paper.get("file_size_bytes", 0),
                "created_at": paper.get("created_at"),
                "artifact_validation": paper.get("artifact_validation"),
                "ingestion_notes": paper.get("ingestion_notes", []),
                "operator_ingestion_notes": paper.get("operator_ingestion_notes", []),
                "operator_metadata_history": paper.get("operator_metadata_history", []),
                "provenance": paper.get("provenance"),
                "summary_metadata": paper.get("summary_metadata"),
            }
            for paper in papers
        ],
        "total": len(papers)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
