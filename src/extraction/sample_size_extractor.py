"""Structured extraction utilities for sample sizes mentioned in a paper."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

SAMPLE_PATTERNS = [
    re.compile(
        r"\b(?:we enrolled|we included|we analyzed|we analysed|we recruited|the study included|this study included|"
        r"participants included|a total of|included|enrolled|recruited|analyzed|analysed)\s+"
        r"(?:approximately\s+|about\s+|around\s+)?(\d{1,3}(?:,\d{3})*|\d+)\s+"
        r"(?:patients|participants|subjects|individuals|samples|cases|volunteers|records?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b[Nn]\s*=\s*(\d{1,3}(?:,\d{3})*|\d+)\b"
    ),
    re.compile(
        r"\bcohort of\s+(\d{1,3}(?:,\d{3})*|\d+)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwith\s+(\d{1,3}(?:,\d{3})*|\d+)\s+"
        r"(?:patients|participants|subjects|individuals|samples|cases|volunteers|records?)\b",
        re.IGNORECASE,
    ),
]

SECTION_BONUS = {"abstract", "methods", "materials and methods", "results", "patients", "study population"}


def extract_sample_sizes(
    parsed_data: Optional[Dict[str, Any]] = None,
    chunks: Optional[Iterable[Dict[str, Any]]] = None,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """Extract likely sample size mentions from parsed paper text or chunks."""
    candidates: List[Dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()

    for section, text in _iter_sections(parsed_data=parsed_data, chunks=chunks):
        for value, evidence in _match_sample_sizes(text):
            key = (value, evidence)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "value": value,
                    "section": section,
                    "confidence": _score_candidate(value, section, evidence),
                    "evidence": evidence,
                }
            )

    ranked = sorted(candidates, key=lambda item: (-item["confidence"], -item["value"]))
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


def _match_sample_sizes(text: str) -> List[tuple[int, str]]:
    matches: List[tuple[int, str]] = []
    for pattern in SAMPLE_PATTERNS:
        for match in pattern.finditer(text):
            value = int(match.group(1).replace(",", ""))
            evidence = _build_evidence(text, match.start(), match.end())
            matches.append((value, evidence))
    return matches


def _score_candidate(value: int, section: str, evidence: str) -> float:
    score = 0.55
    normalized_section = section.lower()
    if normalized_section in SECTION_BONUS:
        score += 0.15
    if re.search(r"\b(?:patients|participants|subjects|individuals|samples|cases|volunteers|records?)\b", evidence, re.IGNORECASE):
        score += 0.15
    if re.search(r"\b(?:n\s*=|a total of|included|enrolled|recruited|analyzed|analysed|cohort of)\b", evidence, re.IGNORECASE):
        score += 0.1
    if value >= 100:
        score += 0.05
    return min(score, 0.99)


def _build_evidence(text: str, start: int, end: int, window: int = 90) -> str:
    snippet_start = max(0, start - window)
    snippet_end = min(len(text), end + window)
    return text[snippet_start:snippet_end].strip()
