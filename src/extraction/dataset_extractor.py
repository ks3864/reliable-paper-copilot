"""Structured extraction utilities for dataset names mentioned in a paper."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

DATASET_KEYWORDS = ("dataset", "datasets", "corpus", "corpora", "cohort", "cohorts", "benchmark", "benchmarks")
STOPWORDS = {
    "abstract",
    "introduction",
    "methods",
    "results",
    "discussion",
    "conclusion",
    "study",
    "paper",
    "model",
    "approach",
    "task",
    "tasks",
    "experiment",
    "experiments",
}

PATTERNS = [
    re.compile(
        r"\b(?:using|used|evaluate(?:d)? on|trained on|tested on|validated on|from)\s+(?:the\s+)?"
        r"([A-Z][A-Za-z0-9\-]*(?:\s+[A-Z0-9][A-Za-z0-9\-]*){0,4})\s+"
        r"(?:dataset|datasets|corpus|cohort|benchmark)s?\b"
    ),
    re.compile(
        r"\b(?:dataset|datasets|corpus|cohort|benchmark)s?\s*(?:called|named)?\s*(?:the\s+)?"
        r"([A-Z][A-Za-z0-9\-]*(?:\s+[A-Z0-9][A-Za-z0-9\-]*){0,4})\b"
    ),
    re.compile(
        r"\b([A-Z][A-Za-z0-9\-]*(?:\s+[A-Z0-9][A-Za-z0-9\-]*){0,4})\s+"
        r"(?:dataset|datasets|corpus|cohort|benchmark)s?\b"
    ),
]


def extract_dataset_names(
    parsed_data: Optional[Dict[str, Any]] = None,
    chunks: Optional[Iterable[Dict[str, Any]]] = None,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """Extract likely dataset names from parsed paper text or chunks."""
    candidates: Dict[str, Dict[str, Any]] = {}

    for section, text in _iter_sections(parsed_data=parsed_data, chunks=chunks):
        for match in _match_candidates(text):
            normalized = _normalize_name(match)
            if not normalized or normalized.lower() in STOPWORDS:
                continue

            score = _score_candidate(normalized, section, text)
            existing = candidates.get(normalized.lower())
            candidate = {
                "name": normalized,
                "section": section,
                "confidence": score,
                "evidence": _build_evidence(text, normalized),
            }

            if existing is None or candidate["confidence"] > existing["confidence"]:
                candidates[normalized.lower()] = candidate

    ranked = sorted(candidates.values(), key=lambda item: (-item["confidence"], item["name"]))
    return ranked[:max_results]


def _iter_sections(
    parsed_data: Optional[Dict[str, Any]],
    chunks: Optional[Iterable[Dict[str, Any]]],
) -> Iterable[tuple[str, str]]:
    if chunks is not None:
        for chunk in chunks:
            yield chunk.get("section", "unknown"), chunk.get("text", "")
        return

    if parsed_data is not None:
        for page in parsed_data.get("pages", []):
            yield f"page_{page.get('page_number', 'unknown')}", page.get("text", "")


def _match_candidates(text: str) -> List[str]:
    found: List[str] = []
    for pattern in PATTERNS:
        found.extend(match.group(1) for match in pattern.finditer(text))
    return found


def _normalize_name(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" .,:;()[]{}")
    value = re.sub(r"^(the|a|an)\s+", "", value, flags=re.IGNORECASE)
    return value.strip()


def _score_candidate(name: str, section: str, text: str) -> float:
    score = 0.55
    if any(char.isdigit() for char in name):
        score += 0.1
    if section.lower() in {"abstract", "methods", "experiments", "evaluation", "results"}:
        score += 0.15
    if name.isupper() or any(char.isupper() for char in name[1:]):
        score += 0.1
    if re.search(re.escape(name) + r"\s+(?:dataset|datasets|corpus|cohort|benchmark)", text):
        score += 0.1
    return min(score, 0.99)


def _build_evidence(text: str, name: str, window: int = 90) -> str:
    match = re.search(re.escape(name), text)
    if match is None:
        return text[: window * 2].strip()
    start = max(0, match.start() - window)
    end = min(len(text), match.end() + window)
    return text[start:end].strip()
