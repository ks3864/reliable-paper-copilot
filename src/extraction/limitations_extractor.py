"""Structured extraction utilities for study limitations mentioned in a paper."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

LIMITATION_PATTERNS = [
    re.compile(
        r"\b(?:limitations?\s+(?:include|included|were|are)\s+|the main limitation\s+(?:was|is)\s+|"
        r"one limitation\s+(?:was|is)\s+|our study (?:is|was) limited by\s+|this study (?:is|was) limited by\s+)"
        r"([^.;]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:a limitation of this study\s+(?:is|was)\s+|a key limitation\s+(?:is|was)\s+|"
        r"important limitations?\s+(?:include|included)\s+)"
        r"([^.;]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:we caution that|we acknowledge that|we note that)\s+([^.;]+(?:limitation|limited|limits?)[^.;]*)",
        re.IGNORECASE,
    ),
]

SECTION_BONUS = {"abstract", "discussion", "limitations", "conclusion"}


def extract_limitations(
    parsed_data: Optional[Dict[str, Any]] = None,
    chunks: Optional[Iterable[Dict[str, Any]]] = None,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """Extract likely study limitations from parsed paper text or chunks."""
    candidates: Dict[str, Dict[str, Any]] = {}

    for section, text in _iter_sections(parsed_data=parsed_data, chunks=chunks):
        for limitation, evidence in _match_limitations(text):
            normalized = _normalize_limitation(limitation)
            if not normalized:
                continue

            key = normalized.lower()
            candidate = {
                "text": normalized,
                "section": section,
                "confidence": _score_candidate(section, evidence, normalized),
                "evidence": evidence,
            }
            existing = candidates.get(key)
            if existing is None or candidate["confidence"] > existing["confidence"]:
                candidates[key] = candidate

    ranked = sorted(candidates.values(), key=lambda item: (-item["confidence"], len(item["text"])))
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


def _match_limitations(text: str) -> List[tuple[str, str]]:
    matches: List[tuple[str, str]] = []
    for pattern in LIMITATION_PATTERNS:
        for match in pattern.finditer(text):
            snippet = match.group(1).strip()
            evidence = _build_evidence(text, match.start(), match.end())
            matches.append((snippet, evidence))
    return matches


def _normalize_limitation(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" .,:;()[]{}")
    value = re.sub(r"^that\s+", "", value, flags=re.IGNORECASE)
    value = value[0].upper() + value[1:] if value else value
    return value


def _score_candidate(section: str, evidence: str, limitation: str) -> float:
    score = 0.55
    if section.lower() in SECTION_BONUS:
        score += 0.15
    if re.search(r"\b(?:important limitations?|key limitation|main limitation)\b", evidence, re.IGNORECASE):
        score += 0.1
    if re.search(r"\b(?:limitation|limited|caution|acknowledge|future work|bias|single-center|small sample)\b", evidence, re.IGNORECASE):
        score += 0.15
    if len(limitation.split()) >= 5:
        score += 0.05
    if re.search(r"\b(?:may|might|could)\b", limitation, re.IGNORECASE):
        score += 0.05
    return min(score, 0.99)


def _build_evidence(text: str, start: int, end: int, window: int = 100) -> str:
    snippet_start = max(0, start - window)
    snippet_end = min(len(text), end + window)
    return text[snippet_start:snippet_end].strip()
