"""Section-Aware Chunking Module - Split papers into chunks by section."""

import re
from typing import Dict, List, Any, Optional
from pathlib import Path


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


def detect_sections(text: str) -> List[Dict[str, Any]]:
    """
    Detect sections in paper text and return list of section boundaries.
    
    Returns list of dicts with: section_name, start_pos, end_pos
    """
    sections = []
    lines = text.split('\n')
    
    current_section = "preamble"  # Before first proper section
    current_start = 0
    line_positions = []
    
    # Track character positions
    pos = 0
    for line in lines:
        line_positions.append(pos)
        pos += len(line) + 1  # +1 for newline
    
    for i, line in enumerate(lines):
        matched_section = None
        for pattern, section_name in SECTION_PATTERNS:
            if re.match(pattern, line.strip()):
                matched_section = section_name
                break
        
        if matched_section:
            # Save previous section
            if current_section:
                sections.append({
                    "section_name": current_section,
                    "start_pos": line_positions[current_start],
                    "end_pos": line_positions[i] if i > current_start else line_positions[current_start]
                })
            current_section = matched_section
            current_start = i
    
    # Add final section
    sections.append({
        "section_name": current_section,
        "start_pos": line_positions[current_start],
        "end_pos": len(text)
    })
    
    return sections


def chunk_by_sections(parsed_data: Dict[str, Any], max_chunk_size: int = 500) -> List[Dict[str, Any]]:
    """
    Chunk paper text by sections with metadata.
    
    Args:
        parsed_data: Output from pdf_parser.parse_pdf()
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        List of chunk dictionaries with: chunk_id, section, text, metadata
    """
    chunks = []
    chunk_id = 0
    
    # Combine all page text, tracking page boundaries
    full_text = ""
    page_starts = []
    
    for page in parsed_data["pages"]:
        page_starts.append(len(full_text))
        full_text += page["text"] + "\n\n"
    
    # Detect sections
    sections = detect_sections(full_text)
    
    for section in sections:
        section_text = full_text[section["start_pos"]:section["end_pos"]].strip()
        
        if not section_text:
            continue
        
        # Further split large sections into smaller chunks
        if len(section_text) <= max_chunk_size:
            chunks.append({
                "chunk_id": chunk_id,
                "section": section["section_name"],
                "text": section_text,
                "metadata": {
                    "source": parsed_data["metadata"].get("title", "unknown"),
                    "char_count": len(section_text),
                    "word_count": len(section_text.split())
                }
            })
            chunk_id += 1
        else:
            # Split section into smaller chunks
            section_chunks = _split_large_section(section_text, section["section_name"], chunk_id, max_chunk_size)
            chunks.extend(section_chunks)
            chunk_id += len(section_chunks)
    
    return chunks


def _split_large_section(text: str, section: str, start_id: int, max_size: int) -> List[Dict[str, Any]]:
    """Split a large section into smaller chunks at paragraph/sentence boundaries."""
    chunks = []
    
    # Split by double newlines (paragraphs) first
    paragraphs = re.split(r'\n\s*\n', text)
    current_chunk = ""
    chunk_id = start_id
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        if len(current_chunk) + len(para) + 2 <= max_size:
            current_chunk += para + "\n\n"
        else:
            # Save current chunk if not empty
            if current_chunk.strip():
                chunks.append({
                    "chunk_id": chunk_id,
                    "section": section,
                    "text": current_chunk.strip(),
                    "metadata": {
                        "source": "paper",
                        "char_count": len(current_chunk.strip()),
                        "word_count": len(current_chunk.strip().split())
                    }
                })
                chunk_id += 1
            
            # If single paragraph is too large, split by sentences
            if len(para) > max_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = ""
                for sent in sentences:
                    if len(current_chunk) + len(sent) + 1 <= max_size:
                        current_chunk += sent + " "
                    else:
                        if current_chunk.strip():
                            chunks.append({
                                "chunk_id": chunk_id,
                                "section": section,
                                "text": current_chunk.strip(),
                                "metadata": {
                                    "source": "paper",
                                    "char_count": len(current_chunk.strip()),
                                    "word_count": len(current_chunk.strip().split())
                                }
                            })
                            chunk_id += 1
                        current_chunk = sent + " "
                if current_chunk.strip():
                    chunks.append({
                        "chunk_id": chunk_id,
                        "section": section,
                        "text": current_chunk.strip(),
                        "metadata": {
                            "source": "paper",
                            "char_count": len(current_chunk.strip()),
                            "word_count": len(current_chunk.strip().split())
                        }
                    })
                    chunk_id += 1
                current_chunk = ""
            else:
                current_chunk = para + "\n\n"
    
    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append({
            "chunk_id": chunk_id,
            "section": section,
            "text": current_chunk.strip(),
            "metadata": {
                "source": "paper",
                "char_count": len(current_chunk.strip()),
                "word_count": len(current_chunk.strip().split())
            }
        })
    
    return chunks


def save_chunks(chunks: List[Dict[str, Any]], output_path: str) -> None:
    """Save chunks to JSON file."""
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"chunks": chunks, "total": len(chunks)}, f, indent=2, ensure_ascii=False)


def load_chunks(input_path: str) -> List[Dict[str, Any]]:
    """Load chunks from JSON file."""
    import json
    with open(input_path, 'r', encoding='utf-8') as f:
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
