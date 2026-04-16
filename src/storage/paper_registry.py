"""Persistent registry for uploaded paper metadata."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils import ensure_dir, load_json, save_json


class PaperRegistry:
    """Store paper metadata in a JSON registry on disk."""

    ARTIFACT_PATH_FIELDS = ("raw_pdf_path", "parsed_path", "chunks_path", "index_path")

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
        payload.setdefault("papers", {})[paper["paper_id"]] = deepcopy(paper)
        self._write(payload)
        return deepcopy(paper)

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
