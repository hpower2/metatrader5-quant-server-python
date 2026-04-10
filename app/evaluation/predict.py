from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from app.config.io import load_run_config
from app.data.loading import load_ohlcv
from app.datasets.targets import infer_task_type
from app.features.engineering import build_features
from app.models import build_model
from app.utils.io import load_pickle
from app.utils.paths import resolve_run_path


def predict_latest(run_id: str, input_path: Path | None = None) -> dict[str, Any]:
    run_path = resolve_run_path(run_id)
    if not run_path.exists():
        raise FileNotFoundError(f"Run not found: {run_id}")

    config = load_run_config(run_path / "config.yaml")
    if input_path is not None:
        config.data.input_path = input_path

    frame = load_ohlcv(config.data)
    featured = build_features(frame, config.features)
    feature_names = load_model_metadata_feature_names(run_path)
    featured = featured.dropna(subset=feature_names).reset_index(drop=True)
    if len(featured) < config.dataset.window:
        raise ValueError(
            f"Not enough rows for prediction window={config.dataset.window}. "
            f"Available after feature warmup: {len(featured)}"
        )

    latest = featured.tail(config.dataset.window)
    x = latest[feature_names].to_numpy(dtype=np.float32)
    scaler = load_pickle(run_path / "dataset" / "scaler.pkl")
    x_scaled = scaler.transform(x).reshape(1, config.dataset.window, len(feature_names)).astype(np.float32)

    checkpoint = torch.load(run_path / "checkpoints" / "best.pt", map_location="cpu")
    model = build_model(
        config.model,
        input_window=config.dataset.window,
        input_features=int(checkpoint["input_features"]),
        output_dim=int(checkpoint["output_dim"]),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    with torch.no_grad():
        output = model(torch.tensor(x_scaled, dtype=torch.float32)).cpu().numpy().reshape(-1)

    task = infer_task_type(config.dataset.target_mode)
    payload: dict[str, Any] = {
        "run_id": run_id,
        "target_mode": config.dataset.target_mode,
        "task_type": task,
        "anchor_timestamp": pd.Timestamp(latest["timestamp"].iloc[-1]).isoformat(),
    }
    if task == "binary_classification":
        probability = float(1.0 / (1.0 + np.exp(-output[0])))
        payload["logit"] = float(output[0])
        payload["probability"] = probability
        payload["predicted_label"] = int(probability >= 0.5)
    else:
        payload["prediction"] = output.astype(float).tolist()
    return payload


def load_model_metadata_feature_names(run_path: Path) -> list[str]:
    checkpoint = torch.load(run_path / "checkpoints" / "best.pt", map_location="cpu")
    return list(checkpoint["feature_names"])
