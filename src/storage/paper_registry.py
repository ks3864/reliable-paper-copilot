"""Persistent registry for uploaded paper metadata."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.extraction import (
    extract_dataset_names,
    extract_inclusion_exclusion_criteria,
    extract_limitations,
    extract_sample_sizes,
)
from src.utils import ensure_dir, load_json, save_json


def build_summary_metadata(parsed: Dict[str, Any], chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a compact metadata summary for real-paper registry records."""
    metadata = parsed.get("metadata", {})
    abstract = (metadata.get("abstract") or "").strip()
    section_names = [chunk.get("section", "unknown") for chunk in chunks if chunk.get("section")]
    unique_sections = list(dict.fromkeys(section_names))
    tables_count = sum(len(page.get("tables", [])) for page in parsed.get("pages", []))
    total_word_count = sum(page.get("word_count", 0) for page in parsed.get("pages", []))
    chunking_strategies: Dict[str, int] = {}
    for chunk in chunks:
        strategy = chunk.get("metadata", {}).get("chunking_strategy", "unknown")
        chunking_strategies[strategy] = chunking_strategies.get(strategy, 0) + 1

    extracted_datasets = extract_dataset_names(chunks=chunks, max_results=3)
    extracted_sample_sizes = extract_sample_sizes(chunks=chunks, max_results=3)
    extracted_limitations = extract_limitations(chunks=chunks, max_results=2)
    extracted_criteria = extract_inclusion_exclusion_criteria(chunks=chunks, max_results=4)
    inclusion_criteria = [item for item in extracted_criteria if item.get("type") == "inclusion"]
    exclusion_criteria = [item for item in extracted_criteria if item.get("type") == "exclusion"]

    return {
        "authors": metadata.get("authors"),
        "abstract_preview": abstract[:280] if abstract else None,
        "section_names": unique_sections,
        "section_count": len(unique_sections),
        "tables_count": tables_count,
        "total_word_count": total_word_count,
        "chunking_strategies": chunking_strategies,
        "extracted_summary": {
            "datasets": [item.get("name") for item in extracted_datasets],
            "sample_sizes": [item.get("value") for item in extracted_sample_sizes],
            "limitations": [item.get("text") for item in extracted_limitations],
            "inclusion_criteria": [item.get("text") for item in inclusion_criteria],
            "exclusion_criteria": [item.get("text") for item in exclusion_criteria],
            "counts": {
                "datasets": len(extracted_datasets),
                "sample_sizes": len(extracted_sample_sizes),
                "limitations": len(extracted_limitations),
                "inclusion_criteria": len(inclusion_criteria),
                "exclusion_criteria": len(exclusion_criteria),
            },
        },
    }


def build_ingestion_notes(
    parsed: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    *,
    index_persisted: bool,
) -> List[str]:
    """Create lightweight operator-facing notes about ingestion quality."""
    notes: List[str] = []
    metadata = parsed.get("metadata", {})

    if metadata.get("title"):
        notes.append("Title extracted from the PDF first page.")
    else:
        notes.append("Title could not be extracted automatically; using fallback metadata.")

    if metadata.get("abstract"):
        notes.append("Abstract metadata was extracted and stored in the paper summary.")
    else:
        notes.append("No abstract metadata was extracted; answers rely on page text and chunk retrieval.")

    extracted_datasets = extract_dataset_names(chunks=chunks, max_results=3)
    extracted_sample_sizes = extract_sample_sizes(chunks=chunks, max_results=3)
    extracted_limitations = extract_limitations(chunks=chunks, max_results=2)

    if extracted_datasets:
        notes.append(
            "Extracted structured study metadata including dataset mentions: "
            + ", ".join(item["name"] for item in extracted_datasets)
            + "."
        )
    if extracted_sample_sizes:
        notes.append(
            "Detected likely sample size mention(s): "
            + ", ".join(str(item["value"]) for item in extracted_sample_sizes)
            + "."
        )
    if extracted_limitations:
        notes.append("Captured likely limitation statements for operator review in the registry summary.")

    if index_persisted:
        notes.append("Dense retrieval index was persisted for reuse across restarts.")
    else:
        notes.append("Persistent dense index was unavailable; the paper will rebuild or use lexical fallback at query time.")

    unique_sections = list(dict.fromkeys(chunk.get("section") for chunk in chunks if chunk.get("section")))
    notes.append(f"Detected {len(unique_sections)} section label(s) across {len(chunks)} chunk(s).")
    return notes


def build_provenance_metadata(
    *,
    original_filename: Optional[str],
    file_hash: Optional[str],
    created_at: str,
) -> Dict[str, Any]:
    """Build operator-visible provenance metadata for a paper record."""
    return {
        "source_type": "uploaded_pdf",
        "source_label": original_filename,
        "source_url": None,
        "citation_hint": None,
        "uploaded_via": "api_upload",
        "uploaded_at": created_at,
        "original_filename": original_filename,
        "file_hash": file_hash,
        "last_operator_update_at": None,
        "last_operator_update_source": None,
        "operator_update_count": 0,
    }


class PaperRegistry:
    """Store paper metadata in a JSON registry on disk."""

    ARTIFACT_PATH_FIELDS = ("raw_pdf_path", "parsed_path", "chunks_path", "index_path")
    EDITABLE_PROVENANCE_FIELDS = (
        "source_label",
        "source_url",
        "citation_hint",
        "last_operator_update_at",
        "last_operator_update_source",
        "operator_update_count",
    )

    def __init__(self, registry_path: str | Path = "data/papers/registry.json"):
        self.registry_path = Path(registry_path)
        ensure_dir(str(self.registry_path.parent))
        if not self.registry_path.exists():
            self._write({"papers": {}})

    def list_papers(self) -> List[Dict[str, Any]]:
        payload = self._read()
        papers = payload.get("papers", {})
        validated = (self._with_artifact_validation(record) for record in papers.values())
        return sorted(validated, key=lambda item: item["created_at"], reverse=True)

    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        payload = self._read()
        paper = payload.get("papers", {}).get(paper_id)
        return self._with_artifact_validation(paper) if paper is not None else None

    def upsert_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        if "paper_id" not in paper:
            raise ValueError("Paper record must include paper_id")

        payload = self._read()
        normalized = deepcopy(paper)
        normalized.setdefault("operator_ingestion_notes", [])
        normalized.setdefault("provenance", {})
        payload.setdefault("papers", {})[paper["paper_id"]] = normalized
        self._write(payload)
        return deepcopy(normalized)

    def update_operator_metadata(
        self,
        paper_id: str,
        *,
        operator_ingestion_notes: Optional[List[str]] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        payload = self._read()
        paper = payload.get("papers", {}).get(paper_id)
        if paper is None:
            return None

        if operator_ingestion_notes is not None:
            paper["operator_ingestion_notes"] = [note.strip() for note in operator_ingestion_notes if note and note.strip()]

        if provenance is not None:
            current = deepcopy(paper.get("provenance", {}))
            for field in self.EDITABLE_PROVENANCE_FIELDS:
                if field in provenance:
                    current[field] = provenance[field]
            paper["provenance"] = current

        self._write(payload)
        return self._with_artifact_validation(paper)

    def _read(self) -> Dict[str, Any]:
        return load_json(str(self.registry_path))

    def _write(self, payload: Dict[str, Any]) -> None:
        save_json(payload, str(self.registry_path))

    def _with_artifact_validation(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        enriched = deepcopy(paper)
        artifacts: Dict[str, Dict[str, Any]] = {}
        missing_required: List[str] = []

        for field in self.ARTIFACT_PATH_FIELDS:
            path_value = enriched.get(field)
            required = field != "index_path"
            exists = bool(path_value) and Path(path_value).exists()
            artifacts[field] = {
                "path": path_value,
                "exists": exists,
                "required": required,
            }
            if required and not exists:
                missing_required.append(field)

        enriched["artifact_validation"] = {
            "artifacts": artifacts,
            "all_required_present": not missing_required,
            "missing_required": missing_required,
        }
        return enriched
