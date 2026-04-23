"""Run the packaged sample-paper demo end-to-end in-process."""

from __future__ import annotations

import argparse
import json
import os
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from fastapi.testclient import TestClient

from scripts.fetch_sample_package import fetch_sample_package, load_manifest
from src.api.main import app


@contextmanager
def temporary_cwd(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def load_demo_questions(package_dir: Path) -> list[dict]:
    questions_path = package_dir / "questions.json"
    return json.loads(questions_path.read_text(encoding="utf-8"))


def select_question(questions: list[dict], question_id: str | None) -> dict:
    if question_id is None:
        return questions[0]

    for item in questions:
        if item.get("id") == question_id:
            return item

    available = ", ".join(item.get("id", "<missing>") for item in questions)
    raise ValueError(f"Unknown question id: {question_id}. Available ids: {available}")


def persist_demo_artifact(payload: dict, artifacts_dir: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    package_id = payload["package_id"]
    question_id = payload.get("question_id") or "question"

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifacts_dir / f"{timestamp}-{package_id}-{question_id}.json"
    latest_path = artifacts_dir / "latest.json"

    artifact_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    latest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return artifact_path


def run_sample_demo(
    package_dir: Path,
    output_dir: Path,
    question_id: str | None = None,
    top_k: int = 5,
    retrieval_mode: str = "hybrid",
    artifacts_dir: Path | None = None,
) -> dict:
    manifest = load_manifest(package_dir)
    questions = load_demo_questions(package_dir)
    selected_question = select_question(questions, question_id)
    pdf_path = fetch_sample_package(package_dir, output_dir)

    with temporary_cwd(package_dir.parents[1]):
        client = TestClient(app)
        with pdf_path.open("rb") as handle:
            upload_response = client.post(
                "/upload",
                files={"file": (pdf_path.name, handle, "application/pdf")},
            )
        upload_response.raise_for_status()
        upload_payload = upload_response.json()

        ask_response = client.post(
            "/ask",
            json={
                "paper_id": upload_payload["paper_id"],
                "question": selected_question["question"],
                "top_k": top_k,
                "retrieval_mode": retrieval_mode,
            },
        )
        ask_response.raise_for_status()
        answer_payload = ask_response.json()

    payload = {
        "package_id": manifest["package_id"],
        "title": manifest.get("title"),
        "paper_path": str(pdf_path),
        "question_id": selected_question.get("id"),
        "question": selected_question["question"],
        "expected_focus": selected_question.get("expected_focus"),
        "upload": upload_payload,
        "answer": answer_payload,
    }

    if artifacts_dir is not None:
        artifact_path = persist_demo_artifact(payload, artifacts_dir)
        payload["artifact_path"] = str(artifact_path)

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package-dir",
        default="sample_packages/attention-is-all-you-need",
        help="Path to the sample package directory",
    )
    parser.add_argument(
        "--output-dir",
        default="data/raw",
        help="Directory where the sample PDF should be downloaded",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts/demo",
        help="Directory where the demo transcript JSON should be persisted",
    )
    parser.add_argument(
        "--question-id",
        default=None,
        help="Optional packaged question id to ask. Defaults to the first question.",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve")
    parser.add_argument(
        "--retrieval-mode",
        default="hybrid",
        choices=["dense", "lexical", "hybrid"],
        help="Retrieval mode to use for the canned question",
    )
    args = parser.parse_args()

    payload = run_sample_demo(
        package_dir=Path(args.package_dir),
        output_dir=Path(args.output_dir),
        question_id=args.question_id,
        top_k=args.top_k,
        retrieval_mode=args.retrieval_mode,
        artifacts_dir=Path(args.artifacts_dir),
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
