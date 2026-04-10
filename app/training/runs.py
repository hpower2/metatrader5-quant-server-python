from __future__ import annotations

from typing import Any

from app.utils.io import load_json
from app.utils.paths import resolve_run_path, runs_root


def list_runs() -> list[dict[str, Any]]:
    root = runs_root()
    if not root.exists():
        return []

    items: list[dict[str, Any]] = []
    for child in sorted(root.iterdir()):
        manifest_path = child / "run_manifest.json"
        if child.is_dir() and manifest_path.exists():
            manifest = load_json(manifest_path)
            items.append(manifest)
    return items


def show_run(run_id: str) -> dict[str, Any]:
    run_path = resolve_run_path(run_id)
    if not run_path.exists():
        raise FileNotFoundError(f"Run not found: {run_id}")

    payload: dict[str, Any] = {"run_id": run_id}
    for name in ["run_manifest.json", "training_summary.json", "training_history.json"]:
        path = run_path / name
        if path.exists():
            payload[name.replace(".json", "")] = load_json(path)
    return payload
