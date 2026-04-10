from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from app.config.io import save_run_config
from app.config.schema import RunConfig
from app.data.quality import dataset_quality_report
from app.data.sufficiency import data_sufficiency_report
from app.datasets.builder import build_dataset_bundle, save_dataset_bundle
from app.datasets.targets import infer_task_type, target_dimension
from app.models import build_model
from app.utils.io import save_json
from app.utils.paths import make_run_id, run_dir
from app.utils.seeding import set_deterministic_seed


class WindowDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray) -> None:
        self.x = torch.tensor(x, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.x)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.x[index], self.y[index]


@dataclass
class TrainResult:
    run_id: str
    run_path: Path
    best_epoch: int
    best_validation_loss: float
    history: list[dict[str, float]]


def _choose_device(name: str) -> torch.device:
    if name == "cpu":
        return torch.device("cpu")
    if name == "cuda":
        if not torch.cuda.is_available():
            raise ValueError("CUDA requested but not available.")
        return torch.device("cuda")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def train_from_config(config: RunConfig) -> TrainResult:
    set_deterministic_seed(config.training.seed)
    run_prefix = config.run_name or f"{config.model.name}_{config.dataset.target_mode}"
    run_id = make_run_id(run_prefix)
    run_path = run_dir(run_id)
    save_run_config(config, run_path / "config.yaml")

    from app.data.loading import load_ohlcv

    frame = load_ohlcv(config.data)
    quality_report = dataset_quality_report(frame)
    sufficiency_report = data_sufficiency_report(
        frame,
        window=config.dataset.window,
        horizon=config.dataset.horizon,
        stride=config.dataset.stride,
        train_ratio=config.split.train_ratio,
        validation_ratio=config.split.validation_ratio,
        gap=config.split.gap,
        wf_train_windows=config.walk_forward.train_windows,
        wf_validation_windows=config.walk_forward.validation_windows,
        wf_test_windows=config.walk_forward.test_windows,
        wf_step_windows=config.walk_forward.step_windows,
    )
    save_json(
        {"quality": quality_report, "sufficiency": sufficiency_report},
        run_path / "data_sufficiency_report.json",
    )
    if sufficiency_report["verdict"] == "insufficient":
        raise ValueError(
            "Dataset sufficiency verdict is 'insufficient'. "
            "Training aborted; inspect runs/<run_id>/data_sufficiency_report.json for details."
        )

    bundle = build_dataset_bundle(
        frame,
        feature_config=config.features,
        dataset_config=config.dataset,
        split_config=config.split,
        walk_forward_config=config.walk_forward,
    )
    save_dataset_bundle(bundle, run_path / "dataset")

    task_type = infer_task_type(config.dataset.target_mode)
    output_dim = target_dimension(config.dataset.target_mode, config.dataset.horizon)
    model = build_model(
        config.model,
        input_window=config.dataset.window,
        input_features=bundle.x_train.shape[-1],
        output_dim=output_dim,
    )
    device = _choose_device(config.training.device)
    model.to(device)

    train_loader = DataLoader(
        WindowDataset(bundle.x_train, bundle.y_train),
        batch_size=config.training.batch_size,
        shuffle=False,
        num_workers=config.training.num_workers,
    )
    validation_loader = DataLoader(
        WindowDataset(bundle.x_validation, bundle.y_validation),
        batch_size=config.training.batch_size,
        shuffle=False,
        num_workers=config.training.num_workers,
    )

    criterion: nn.Module
    if task_type == "binary_classification":
        criterion = nn.BCEWithLogitsLoss()
    else:
        criterion = nn.SmoothL1Loss()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.training.learning_rate,
        weight_decay=config.training.weight_decay,
    )

    best_validation_loss = float("inf")
    best_state: dict[str, Any] | None = None
    best_epoch = -1
    patience = 0
    history: list[dict[str, float]] = []

    for epoch in range(config.training.epochs):
        model.train()
        train_losses: list[float] = []
        for x_batch, y_batch in train_loader:
            x_batch = x_batch.to(device)
            y_batch = y_batch.to(device)
            optimizer.zero_grad()
            prediction = model(x_batch)
            loss = criterion(prediction, y_batch)
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.item()))

        model.eval()
        validation_losses: list[float] = []
        with torch.no_grad():
            for x_batch, y_batch in validation_loader:
                x_batch = x_batch.to(device)
                y_batch = y_batch.to(device)
                prediction = model(x_batch)
                loss = criterion(prediction, y_batch)
                validation_losses.append(float(loss.item()))

        epoch_train_loss = float(np.mean(train_losses)) if train_losses else float("nan")
        epoch_validation_loss = float(np.mean(validation_losses)) if validation_losses else float("nan")
        history.append(
            {
                "epoch": float(epoch),
                "train_loss": epoch_train_loss,
                "validation_loss": epoch_validation_loss,
            }
        )

        if epoch_validation_loss < best_validation_loss:
            best_validation_loss = epoch_validation_loss
            best_epoch = epoch
            patience = 0
            best_state = {
                "model_state_dict": model.state_dict(),
                "input_window": config.dataset.window,
                "input_features": int(bundle.x_train.shape[-1]),
                "output_dim": output_dim,
                "task_type": task_type,
                "target_mode": config.dataset.target_mode,
                "model_config": config.model.model_dump(mode="json"),
                "dataset_meta": bundle.dataset_metadata,
                "feature_names": bundle.feature_names,
            }
        else:
            patience += 1

        if patience >= config.training.early_stopping_patience:
            break

    if best_state is None:
        raise RuntimeError("Training failed to produce a valid checkpoint.")

    checkpoint_dir = run_path / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    torch.save(best_state, checkpoint_dir / "best.pt")

    training_summary = {
        "run_id": run_id,
        "run_path": str(run_path),
        "best_epoch": best_epoch,
        "best_validation_loss": best_validation_loss,
        "epochs_ran": len(history),
        "device": str(device),
        "task_type": task_type,
        "target_mode": config.dataset.target_mode,
    }
    save_json(training_summary, run_path / "training_summary.json")
    save_json({"history": history}, run_path / "training_history.json")

    run_manifest = {
        "run_id": run_id,
        "run_name": config.run_name,
        "target_mode": config.dataset.target_mode,
        "model": config.model.name,
        "task_type": task_type,
        "input_path": str(config.data.input_path),
        "window": config.dataset.window,
        "horizon": config.dataset.horizon,
        "created_at_utc": run_id.split("_")[-1],
    }
    save_json(run_manifest, run_path / "run_manifest.json")

    return TrainResult(
        run_id=run_id,
        run_path=run_path,
        best_epoch=best_epoch,
        best_validation_loss=best_validation_loss,
        history=history,
    )
