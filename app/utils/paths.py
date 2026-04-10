from __future__ import annotations

from datetime import UTC, datetime
import os
from pathlib import Path


def runs_root() -> Path:
    raw = os.getenv("APP_RUNS_ROOT", "runs")
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path


def make_run_id(prefix: str | None = None) -> str:
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    if prefix:
        return f"{prefix}_{timestamp}"
    return timestamp


def run_dir(run_id: str) -> Path:
    path = runs_root() / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_run_path(run_id: str) -> Path:
    return runs_root() / run_id
