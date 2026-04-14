"""PDF Parsing Module - Extract structured text and metadata from scientific papers."""

import pdfplumber
from pathlib import Path
from typing import Dict, List, Any, Optional
import json


def parse_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Parse a PDF file and extract structured text with metadata.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing:
        - metadata: title, authors, abstract, page_count
        - pages: list of page contents with text and position info
    """
    result = {
        "metadata": {
            "title": None,
            "authors": None,
            "abstract": None,
            "page_count": 0,
        },
        "pages": []
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        result["metadata"]["page_count"] = len(pdf.pages)
        
        for page_num, page in enumerate(pdf.pages):
            page_data = {
                "page_number": page_num + 1,
                "text": page.extract_text() or "",
                "tables": page.extract_tables() or [],
            }
            
            # Extract words with positions for more granular analysis
            words = page.extract_words()
            page_data["word_count"] = len(words)
            
            result["pages"].append(page_data)
            
            # Try to extract title from first page
            if page_num == 0 and result["metadata"]["title"] is None:
                result["metadata"]["title"] = _extract_title(page.extract_text())
    
    return result


def _extract_title(first_page_text: str) -> Optional[str]:
    """Extract title from first page - heuristic based on large text at top."""
    if not first_page_text:
        return None
    
    lines = first_page_text.strip().split('\n')
    # Title is typically the first non-empty line(s)
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) > 10:
            # Skip common header lines
            if any(skip in line.lower() for skip in ['abstract', 'introduction', 'doi', 'http']):
                continue
            return line
    return None


def save_parsed( parsed_data: Dict[str, Any], output_path: str) -> None:
    """Save parsed PDF data to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, indent=2, ensure_ascii=False)


def load_parsed(input_path: str) -> Dict[str, Any]:
    """Load parsed PDF data from JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Parsing: {pdf_path}")
        result = parse_pdf(pdf_path)
        print(f"Title: {result['metadata']['title']}")
        print(f"Pages: {result['metadata']['page_count']}")
        print(f"Total text length: {sum(len(p['text']) for p in result['pages'])}")
