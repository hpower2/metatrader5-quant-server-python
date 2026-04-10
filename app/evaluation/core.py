from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
import torch

from app.config.io import load_run_config
from app.datasets.builder import load_saved_dataset_bundle
from app.datasets.targets import infer_task_type, target_dimension
from app.evaluation.metrics import classification_metrics, regression_metrics
from app.models import build_model
from app.utils.io import load_json, save_json
from app.utils.paths import resolve_run_path

SplitName = Literal["train", "validation", "test"]


def _load_model(run_path: Path) -> tuple[torch.nn.Module, dict]:
    config = load_run_config(run_path / "config.yaml")
    checkpoint = torch.load(run_path / "checkpoints" / "best.pt", map_location="cpu")
    model = build_model(
        config.model,
        input_window=config.dataset.window,
        input_features=int(checkpoint["input_features"]),
        output_dim=target_dimension(config.dataset.target_mode, config.dataset.horizon),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, checkpoint


def evaluate_run(run_id: str, split: SplitName = "test") -> dict:
    run_path = resolve_run_path(run_id)
    if not run_path.exists():
        raise FileNotFoundError(f"Run not found: {run_id}")

    bundle = load_saved_dataset_bundle(run_path / "dataset")
    model, checkpoint = _load_model(run_path)
    config = load_run_config(run_path / "config.yaml")
    task_type = infer_task_type(config.dataset.target_mode)

    x: np.ndarray
    y: np.ndarray
    indices: np.ndarray
    if split == "train":
        x, y, indices = bundle.x_train, bundle.y_train, bundle.train_indices
    elif split == "validation":
        x, y, indices = bundle.x_validation, bundle.y_validation, bundle.validation_indices
    else:
        x, y, indices = bundle.x_test, bundle.y_test, bundle.test_indices

    with torch.no_grad():
        prediction = model(torch.tensor(x, dtype=torch.float32)).cpu().numpy()

    if task_type == "binary_classification":
        metrics = classification_metrics(y, prediction)
        probabilities = 1.0 / (1.0 + np.exp(-prediction.reshape(-1)))
        prediction_frame = pd.DataFrame(
            {
                "sample_index": indices.astype(int),
                "y_true": y.reshape(-1),
                "logit": prediction.reshape(-1),
                "probability": probabilities,
                "predicted_label": (probabilities >= 0.5).astype(int),
            }
        )
    else:
        metrics = regression_metrics(y, prediction)
        prediction_frame = pd.DataFrame(
            {
                "sample_index": indices.astype(int),
                "y_true": y.reshape(len(y), -1).tolist(),
                "y_pred": prediction.reshape(len(prediction), -1).tolist(),
            }
        )

    meta = bundle.sample_metadata.iloc[indices].reset_index(drop=True)
    prediction_frame = pd.concat([meta, prediction_frame], axis=1)

    metrics_payload = {
        "run_id": run_id,
        "split": split,
        "target_mode": config.dataset.target_mode,
        "task_type": task_type,
        "sample_count": int(len(x)),
        "metrics": metrics,
    }

    eval_dir = run_path / "evaluation" / split
    eval_dir.mkdir(parents=True, exist_ok=True)
    prediction_frame.to_parquet(eval_dir / "predictions.parquet", index=False)
    prediction_frame.head(200).to_csv(eval_dir / "prediction_samples.csv", index=False)
    save_json(metrics_payload, eval_dir / "metrics.json")

    summary = load_json(run_path / "training_summary.json")
    summary["last_evaluated_split"] = split
    summary["last_evaluation_metrics"] = metrics
    save_json(summary, run_path / "training_summary.json")

    return metrics_payload


def evaluate_walk_forward(run_id: str) -> dict:
    run_path = resolve_run_path(run_id)
    if not run_path.exists():
        raise FileNotFoundError(f"Run not found: {run_id}")

    bundle = load_saved_dataset_bundle(run_path / "dataset")
    model, _ = _load_model(run_path)
    config = load_run_config(run_path / "config.yaml")
    task_type = infer_task_type(config.dataset.target_mode)

    slices = bundle.dataset_metadata.get("walk_forward_slices", [])
    fold_metrics: list[dict] = []

    for slice_info in slices:
        test_start = int(slice_info["test_start"])
        test_end = int(slice_info["test_end"])
        if test_end > len(bundle.x_all):
            continue

        x_fold = bundle.x_all[test_start:test_end]
        y_fold = bundle.y_all[test_start:test_end]
        if len(x_fold) == 0:
            continue

        with torch.no_grad():
            prediction = model(torch.tensor(x_fold, dtype=torch.float32)).cpu().numpy()

        if task_type == "binary_classification":
            metrics = classification_metrics(y_fold, prediction)
        else:
            metrics = regression_metrics(y_fold, prediction)

        fold_metrics.append(
            {
                "fold": int(slice_info["fold"]),
                "test_start": test_start,
                "test_end": test_end,
                "samples": int(len(x_fold)),
                "metrics": metrics,
            }
        )

    aggregate = _aggregate_fold_metrics(fold_metrics, task_type)
    payload = {
        "run_id": run_id,
        "target_mode": config.dataset.target_mode,
        "task_type": task_type,
        "fold_count": len(fold_metrics),
        "aggregate_metrics": aggregate,
        "fold_metrics": fold_metrics,
    }
    eval_dir = run_path / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    save_json(payload, eval_dir / "walk_forward_metrics.json")
    return payload


def _aggregate_fold_metrics(fold_metrics: list[dict], task_type: str) -> dict:
    if not fold_metrics:
        return {}

    if task_type == "binary_classification":
        keys = ["accuracy", "precision", "recall", "f1", "directional_accuracy"]
    else:
        keys = ["mae", "rmse", "directional_accuracy"]

    aggregate: dict[str, float] = {}
    for key in keys:
        values = [float(fold["metrics"][key]) for fold in fold_metrics if fold["metrics"].get(key) is not None]
        if values:
            aggregate[key] = float(np.mean(values))
    return aggregate
