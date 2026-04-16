"""Structured extraction utilities for inclusion and exclusion criteria mentioned in a paper."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

INCLUSION_PATTERNS = [
    re.compile(
        r"\b(?:inclusion criteria(?: were| included)?|eligible participants(?: were)?|participants were eligible if|"
        r"patients were eligible if|subjects were eligible if)\s*(?::|included|were)?\s*([^.;]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:we included only|we included participants who|we enrolled patients with)\s+([^.;]+)",
        re.IGNORECASE,
    ),
]

EXCLUSION_PATTERNS = [
    re.compile(
        r"\b(?:exclusion criteria(?: were| included)?|participants were excluded if|patients were excluded if|"
        r"subjects were excluded if)\s*(?::|included|were)?\s*([^.;]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:we excluded participants with|we excluded patients with|excluded were those with)\s+([^.;]+)",
        re.IGNORECASE,
    ),
]

SECTION_BONUS = {"abstract", "methods", "materials and methods", "study population", "participants"}


def extract_inclusion_exclusion_criteria(
    parsed_data: Optional[Dict[str, Any]] = None,
    chunks: Optional[Iterable[Dict[str, Any]]] = None,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """Extract likely inclusion and exclusion criteria from parsed paper text or chunks."""
    candidates: Dict[tuple[str, str], Dict[str, Any]] = {}

    for section, text in _iter_sections(parsed_data=parsed_data, chunks=chunks):
        for criterion_type, criterion, evidence in _match_criteria(text):
            normalized = _normalize_criterion(criterion)
            if not normalized:
                continue

            key = (criterion_type, normalized.lower())
            candidate = {
                "type": criterion_type,
                "text": normalized,
                "section": section,
                "confidence": _score_candidate(section, evidence, normalized, criterion_type),
                "evidence": evidence,
            }
            existing = candidates.get(key)
            if existing is None or candidate["confidence"] > existing["confidence"]:
                candidates[key] = candidate

    ranked = sorted(
        candidates.values(),
        key=lambda item: (-item["confidence"], 0 if item["type"] == "inclusion" else 1, len(item["text"])),
    )
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


def _match_criteria(text: str) -> List[tuple[str, str, str]]:
    matches: List[tuple[str, str, str]] = []
    for pattern in INCLUSION_PATTERNS:
        for match in pattern.finditer(text):
            matches.append(("inclusion", match.group(1).strip(), _build_evidence(text, match.start(), match.end())))
    for pattern in EXCLUSION_PATTERNS:
        for match in pattern.finditer(text):
            matches.append(("exclusion", match.group(1).strip(), _build_evidence(text, match.start(), match.end())))
    return matches


def _normalize_criterion(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" .,:;()[]{}")
    value = re.sub(r"^(that|who)\s+", "", value, flags=re.IGNORECASE)
    value = value[0].upper() + value[1:] if value else value
    return value


def _score_candidate(section: str, evidence: str, criterion: str, criterion_type: str) -> float:
    score = 0.55
    if section.lower() in SECTION_BONUS:
        score += 0.15
    if re.search(r"\b(?:criteria|eligible|excluded|enrolled|included)\b", evidence, re.IGNORECASE):
        score += 0.15
    if criterion_type == "exclusion" and re.search(r"\b(?:exclude|excluded|without|prior|history of)\b", criterion, re.IGNORECASE):
        score += 0.1
    if criterion_type == "inclusion" and re.search(r"\b(?:age|diagnosis|confirmed|adult|consent)\b", criterion, re.IGNORECASE):
        score += 0.1
    if len(criterion.split()) >= 4:
        score += 0.05
    return min(score, 0.99)


def _build_evidence(text: str, start: int, end: int, window: int = 100) -> str:
    snippet_start = max(0, start - window)
    snippet_end = min(len(text), end + window)
    return text[snippet_start:snippet_end].strip()
