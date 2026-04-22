"""Request logging utilities for API observability."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict



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
