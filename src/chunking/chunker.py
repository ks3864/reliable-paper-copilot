"""Section-aware chunking module with overlap and token-based fallback chunking."""

import json
import re
from typing import Any, Dict, List, Optional


# Common section headers in scientific papers
SECTION_PATTERNS = [
    (r"(?i)^abstract\s*$", "abstract"),
    (r"(?i)^introduction\s*$", "introduction"),
    (r"(?i)^related\s*work\s*$", "related_work"),
    (r"(?i)^background\s*$", "background"),
    (r"(?i)^preliminaries?\s*$", "preliminaries"),
    (r"(?i)^methodology?\s*$", "methodology"),
    (r"(?i)^methods?\s*$", "methods"),
    (r"(?i)^approach\s*$", "approach"),
    (r"(?i)^model\s*$", "model"),
    (r"(?i)^architecture\s*$", "architecture"),
    (r"(?i)^experiment(?:al)?s?\s*$", "experiments"),
    (r"(?i)^evaluation\s*$", "evaluation"),
    (r"(?i)^results?\s*$", "results"),
    (r"(?i)^discussion\s*$", "discussion"),
    (r"(?i)^analysis\s*$", "analysis"),
    (r"(?i)^conclusion(?:s)?\s*$", "conclusions"),
    (r"(?i)^future\s*work\s*$", "future_work"),
    (r"(?i)^acknowledgements?\s*$", "acknowledgements"),
    (r"(?i)^references?\s*$", "references"),
]

DEFAULT_MAX_CHARS = 500
DEFAULT_OVERLAP_CHARS = 100
DEFAULT_MAX_TOKENS = 120
DEFAULT_OVERLAP_TOKENS = 24


def detect_sections(text: str) -> List[Dict[str, Any]]:
    """
    Detect sections in paper text and return list of section boundaries.

    Returns list of dicts with: section_name, start_pos, end_pos
    """
    sections = []
    lines = text.split("\n")

    current_section = "preamble"
    current_start = 0
    line_positions = []

    pos = 0
    for line in lines:
        line_positions.append(pos)
        pos += len(line) + 1

    for i, line in enumerate(lines):
        matched_section = None
        for pattern, section_name in SECTION_PATTERNS:
            if re.match(pattern, line.strip()):
                matched_section = section_name
                break

        if matched_section:
            if current_section:
                sections.append(
                    {
                        "section_name": current_section,
                        "start_pos": line_positions[current_start],
                        "end_pos": line_positions[i]
                        if i > current_start
                        else line_positions[current_start],
                    }
                )
            current_section = matched_section
            current_start = i

    sections.append(
        {
            "section_name": current_section,
            "start_pos": line_positions[current_start],
            "end_pos": len(text),
        }
    )

    return sections


def chunk_by_sections(
    parsed_data: Dict[str, Any],
    max_chunk_size: int = DEFAULT_MAX_CHARS,
    overlap_size: int = DEFAULT_OVERLAP_CHARS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> List[Dict[str, Any]]:
    """
    Chunk paper text by sections with overlap and token-based fallback.

    Args:
        parsed_data: Output from pdf_parser.parse_pdf()
        max_chunk_size: Maximum characters per chunk before splitting.
        overlap_size: Character overlap between adjacent chunks.
        max_tokens: Token threshold for token-based fallback splitting.
        overlap_tokens: Token overlap for token-based fallback chunks.

    Returns:
        List of chunk dictionaries with: chunk_id, section, text, metadata
    """
    chunks: List[Dict[str, Any]] = []
    chunk_id = 0

    full_text = ""
    for page in parsed_data["pages"]:
        full_text += page["text"] + "\n\n"

    sections = detect_sections(full_text)
    source_title = parsed_data.get("metadata", {}).get("title", "unknown")

    for section in sections:
        section_text = full_text[section["start_pos"] : section["end_pos"]].strip()
        if not section_text:
            continue

        if len(section_text) <= max_chunk_size and estimate_token_count(section_text) <= max_tokens:
            chunks.append(
                _build_chunk(
                    chunk_id=chunk_id,
                    section=section["section_name"],
                    text=section_text,
                    source=source_title,
                    strategy="section",
                )
            )
            chunk_id += 1
            continue

        section_chunks = _split_large_section(
            text=section_text,
            section=section["section_name"],
            start_id=chunk_id,
            max_size=max_chunk_size,
            overlap_size=overlap_size,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            source=source_title,
        )
        chunks.extend(section_chunks)
        chunk_id += len(section_chunks)

    return chunks


def estimate_token_count(text: str) -> int:
    """Approximate token count using word/punctuation segments."""
    if not text.strip():
        return 0
    return len(re.findall(r"\w+|[^\w\s]", text))


def _build_chunk(
    chunk_id: int,
    section: str,
    text: str,
    source: str,
    strategy: str,
    metadata_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    clean_text = text.strip()
    metadata = {
        "source": source,
        "char_count": len(clean_text),
        "word_count": len(clean_text.split()),
        "token_count_estimate": estimate_token_count(clean_text),
        "chunking_strategy": strategy,
    }
    if metadata_overrides:
        metadata.update(metadata_overrides)

    return {
        "chunk_id": chunk_id,
        "section": section,
        "text": clean_text,
        "metadata": metadata,
    }


def _split_large_section(
    text: str,
    section: str,
    start_id: int,
    max_size: int,
    overlap_size: int,
    max_tokens: int,
    overlap_tokens: int,
    source: str,
) -> List[Dict[str, Any]]:
    """Split a large section into overlapping chunks, then fall back to token windows when needed."""
    chunks: List[Dict[str, Any]] = []
    paragraphs = [para.strip() for para in re.split(r"\n\s*\n", text) if para.strip()]
    current_parts: List[str] = []
    chunk_id = start_id

    for para in paragraphs:
        candidate_parts = current_parts + [para]
        candidate_text = "\n\n".join(candidate_parts)

        if candidate_text and len(candidate_text) <= max_size and estimate_token_count(candidate_text) <= max_tokens:
            current_parts = candidate_parts
            continue

        if current_parts:
            chunk_text = "\n\n".join(current_parts)
            emitted = _emit_chunk_with_fallback(
                text=chunk_text,
                section=section,
                start_id=chunk_id,
                max_size=max_size,
                overlap_size=overlap_size,
                max_tokens=max_tokens,
                overlap_tokens=overlap_tokens,
                source=source,
            )
            chunks.extend(emitted)
            chunk_id += len(emitted)
            current_parts = _tail_overlap_paragraphs(current_parts, overlap_size)

        if len(para) <= max_size and estimate_token_count(para) <= max_tokens:
            current_parts = (current_parts + [para]) if current_parts else [para]
        else:
            emitted = _emit_chunk_with_fallback(
                text=para,
                section=section,
                start_id=chunk_id,
                max_size=max_size,
                overlap_size=overlap_size,
                max_tokens=max_tokens,
                overlap_tokens=overlap_tokens,
                source=source,
            )
            chunks.extend(emitted)
            chunk_id += len(emitted)
            current_parts = []

    if current_parts:
        emitted = _emit_chunk_with_fallback(
            text="\n\n".join(current_parts),
            section=section,
            start_id=chunk_id,
            max_size=max_size,
            overlap_size=overlap_size,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            source=source,
        )
        chunks.extend(emitted)

    return chunks


def _emit_chunk_with_fallback(
    text: str,
    section: str,
    start_id: int,
    max_size: int,
    overlap_size: int,
    max_tokens: int,
    overlap_tokens: int,
    source: str,
) -> List[Dict[str, Any]]:
    clean_text = text.strip()
    if not clean_text:
        return []

    if len(clean_text) <= max_size and estimate_token_count(clean_text) <= max_tokens:
        return [
            _build_chunk(
                chunk_id=start_id,
                section=section,
                text=clean_text,
                source=source,
                strategy="section_overlap",
                metadata_overrides={
                    "overlap_chars": min(overlap_size, len(clean_text)),
                    "overlap_tokens": overlap_tokens,
                },
            )
        ]

    sentences = _split_into_sentences(clean_text)
    sentence_windows = _sentence_windows(
        sentences=sentences,
        max_size=max_size,
        overlap_size=overlap_size,
    )

    if sentence_windows and all(estimate_token_count(window) <= max_tokens for window in sentence_windows):
        return [
            _build_chunk(
                chunk_id=start_id + offset,
                section=section,
                text=window,
                source=source,
                strategy="section_overlap",
                metadata_overrides={
                    "overlap_chars": overlap_size,
                    "overlap_tokens": overlap_tokens,
                },
            )
            for offset, window in enumerate(sentence_windows)
        ]

    token_windows = _token_windows(clean_text, max_tokens=max_tokens, overlap_tokens=overlap_tokens)
    return [
        _build_chunk(
            chunk_id=start_id + offset,
            section=section,
            text=window,
            source=source,
            strategy="token_fallback",
            metadata_overrides={
                "overlap_chars": overlap_size,
                "overlap_tokens": overlap_tokens,
            },
        )
        for offset, window in enumerate(token_windows)
    ]


def _tail_overlap_paragraphs(paragraphs: List[str], overlap_size: int) -> List[str]:
    if overlap_size <= 0 or not paragraphs:
        return []

    kept: List[str] = []
    total = 0
    for para in reversed(paragraphs):
        kept.insert(0, para)
        total += len(para)
        if total >= overlap_size:
            break
    return kept


def _split_into_sentences(text: str) -> List[str]:
    sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]
    return sentences or [text.strip()]


def _sentence_windows(sentences: List[str], max_size: int, overlap_size: int) -> List[str]:
    if not sentences:
        return []

    windows: List[str] = []
    current: List[str] = []
    index = 0

    while index < len(sentences):
        sentence = sentences[index]
        candidate = " ".join(current + [sentence]).strip()

        if current and len(candidate) > max_size:
            window = " ".join(current).strip()
            if window:
                windows.append(window)
            overlap = _tail_overlap_sentences(current, overlap_size)
            current = overlap if overlap != current else []
            if not current:
                continue
            continue

        if len(sentence) > max_size:
            if current:
                windows.append(" ".join(current).strip())
                current = []
                continue
            return []

        current.append(sentence)
        index += 1

    if current:
        windows.append(" ".join(current).strip())

    return [window for window in windows if window]


def _tail_overlap_sentences(sentences: List[str], overlap_size: int) -> List[str]:
    if overlap_size <= 0:
        return []

    kept: List[str] = []
    total = 0
    for sentence in reversed(sentences):
        kept.insert(0, sentence)
        total += len(sentence)
        if total >= overlap_size:
            break
    return kept


def _token_windows(text: str, max_tokens: int, overlap_tokens: int) -> List[str]:
    tokens = text.split()
    if not tokens:
        return []

    step = max(max_tokens - overlap_tokens, 1)
    windows = []
    for start in range(0, len(tokens), step):
        end = start + max_tokens
        window_tokens = tokens[start:end]
        if not window_tokens:
            continue
        windows.append(" ".join(window_tokens))
        if end >= len(tokens):
            break
    return windows


def save_chunks(chunks: List[Dict[str, Any]], output_path: str) -> None:
    """Save chunks to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"chunks": chunks, "total": len(chunks)}, f, indent=2, ensure_ascii=False)


def load_chunks(input_path: str) -> List[Dict[str, Any]]:
    """Load chunks from JSON file."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("chunks", [])


if __name__ == "__main__":
    import sys
    from src.parsing import load_parsed

    if len(sys.argv) > 1:
        parsed_path = sys.argv[1]
        parsed = load_parsed(parsed_path)
        chunks = chunk_by_sections(parsed)
        print(f"Created {len(chunks)} chunks")
        for c in chunks[:3]:
            print(f"  [{c['section']}] {c['text'][:80]}...")
