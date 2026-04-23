"""Request logging utilities for API observability."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class RequestLogger:
    """Persist per-request telemetry as JSON lines."""

    def __init__(self, log_dir: str | Path | None = None, log_filename: str = "requests.jsonl"):
        default_dir = Path(__file__).resolve().parent.parent.parent / "data" / "logs"
        base_dir = Path(log_dir) if log_dir is not None else default_dir
        base_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = base_dir / log_filename

    def create_event(
        self,
        *,
        endpoint: str,
        paper_id: str | None,
        question: str | None,
        latency_ms: float,
        token_usage: Dict[str, int],
        model_version: str,
        extra: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        event: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "endpoint": endpoint,
            "paper_id": paper_id,
            "question": question,
            "latency_ms": round(latency_ms, 2),
            "token_usage": token_usage,
            "model_version": model_version,
        }
        if extra:
            event["extra"] = extra
            event.update(extra)
        return event

    def log(self, event: Dict[str, Any]) -> None:
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def read_events(
        self,
        *,
        paper_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        if limit <= 0 or not self.log_path.exists():
            return []

        events: List[Dict[str, Any]] = []
        with self.log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if paper_id is not None and event.get("paper_id") != paper_id:
                    continue
                if endpoint is not None and event.get("endpoint") != endpoint:
                    continue
                events.append(event)

        return list(reversed(events[-limit:]))

    def delete_events(
        self,
        *,
        paper_id: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> int:
        if not self.log_path.exists():
            return 0

        kept_lines: List[str] = []
        deleted_count = 0

        with self.log_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    kept_lines.append(raw_line if raw_line.endswith("\n") else raw_line + "\n")
                    continue

                matches_paper = paper_id is None or event.get("paper_id") == paper_id
                matches_endpoint = endpoint is None or event.get("endpoint") == endpoint
                if matches_paper and matches_endpoint:
                    deleted_count += 1
                    continue

                kept_lines.append(raw_line if raw_line.endswith("\n") else raw_line + "\n")

        with self.log_path.open("w", encoding="utf-8") as handle:
            handle.writelines(kept_lines)

        return deleted_count
