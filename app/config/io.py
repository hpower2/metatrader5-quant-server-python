from __future__ import annotations

from pathlib import Path

import yaml

from app.config.schema import RunConfig


def load_run_config(path: Path) -> RunConfig:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload is None:
        raise ValueError(f"Config file is empty: {path}")
    return RunConfig.model_validate(payload)


def save_run_config(config: RunConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False), encoding="utf-8")
