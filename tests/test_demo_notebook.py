import json
from pathlib import Path


def test_demo_notebook_exists_and_covers_core_flow():
    notebook_path = Path("notebooks/reliable_paper_copilot_demo.ipynb")
    assert notebook_path.exists(), "Demo notebook should exist"

    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4

    cells = notebook["cells"]
    joined_sources = "\n".join("".join(cell.get("source", [])) for cell in cells)

    assert "build_text_pdf" in joined_sources
    assert "parse_pdf" in joined_sources
    assert "chunk_by_sections" in joined_sources
    assert "create_retriever" in joined_sources
    assert "SimpleAnswerGenerator" in joined_sources
    assert "run_experiment" in joined_sources
    assert "lexical fallback" in joined_sources.lower()
