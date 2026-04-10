from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from app.config.schema import DatasetConfig, FeatureConfig, SplitConfig, WalkForwardConfig
from app.datasets.splitting import chronological_split_indices, walk_forward_slices
from app.datasets.targets import build_target, infer_task_type, target_dimension
from app.features.engineering import build_features, feature_columns
from app.utils.io import load_json, load_pickle, save_json, save_pickle


@dataclass
class DatasetBundle:
    x_all: np.ndarray
    y_all: np.ndarray
    x_train: np.ndarray
    y_train: np.ndarray
    x_validation: np.ndarray
    y_validation: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    train_indices: np.ndarray
    validation_indices: np.ndarray
    test_indices: np.ndarray
    scaler: StandardScaler
    feature_names: list[str]
    sample_metadata: pd.DataFrame
    dataset_metadata: dict[str, Any]


def build_dataset_bundle(
    frame: pd.DataFrame,
    *,
    feature_config: FeatureConfig,
    dataset_config: DatasetConfig,
    split_config: SplitConfig,
    walk_forward_config: WalkForwardConfig,
) -> DatasetBundle:
    featured = build_features(frame, feature_config)
    feature_names = feature_columns(featured)
    featured = featured.dropna(subset=feature_names + ["timestamp", "open", "high", "low", "close", "volume"]).reset_index(drop=True)

    samples_x: list[np.ndarray] = []
    samples_y: list[np.ndarray] = []
    sample_records: list[dict[str, Any]] = []

    for (symbol, timeframe), group in featured.groupby(["symbol", "timeframe"], sort=True):
        group = group.sort_values("timestamp").reset_index(drop=True)
        max_start = len(group) - dataset_config.window - dataset_config.horizon
        if max_start < 0:
            continue

        feature_matrix = group[feature_names].to_numpy(dtype=np.float32)
        for start in range(0, max_start + 1, dataset_config.stride):
            window_end = start + dataset_config.window
            horizon_end = window_end + dataset_config.horizon

            window_features = feature_matrix[start:window_end]
            anchor_row = group.iloc[window_end - 1]
            future = group.iloc[window_end:horizon_end]
            target, aux = build_target(future, float(anchor_row["close"]), dataset_config)

            samples_x.append(window_features)
            samples_y.append(target.astype(np.float32))
            sample_records.append(
                {
                    "sample_index": len(samples_x) - 1,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "anchor_timestamp": anchor_row["timestamp"],
                    "anchor_close": float(anchor_row["close"]),
                    **aux,
                }
            )

    if not samples_x:
        raise ValueError(
            "No training windows could be generated. "
            "Check dataset size, window/horizon settings, and missing values."
        )

    sample_metadata = pd.DataFrame(sample_records).sort_values("anchor_timestamp").reset_index(drop=True)
    reorder = sample_metadata["sample_index"].to_numpy(dtype=np.int64)
    x = np.stack(samples_x, axis=0)[reorder]
    y = np.stack(samples_y, axis=0)[reorder]
    sample_metadata["sample_index"] = np.arange(len(sample_metadata), dtype=np.int64)

    splits = chronological_split_indices(len(x), split_config)
    x_train = x[splits["train"]]
    x_validation = x[splits["validation"]]
    x_test = x[splits["test"]]
    y_train = y[splits["train"]]
    y_validation = y[splits["validation"]]
    y_test = y[splits["test"]]

    scaler = StandardScaler()
    train_2d = x_train.reshape(-1, x_train.shape[-1])
    scaler.fit(train_2d)

    x_all_scaled = scaler.transform(x.reshape(-1, x.shape[-1])).reshape(x.shape).astype(np.float32)
    x_train_scaled = x_all_scaled[splits["train"]]
    x_validation_scaled = scaler.transform(x_validation.reshape(-1, x_validation.shape[-1])).reshape(x_validation.shape).astype(np.float32)
    x_test_scaled = scaler.transform(x_test.reshape(-1, x_test.shape[-1])).reshape(x_test.shape).astype(np.float32)

    wf_slices = walk_forward_slices(len(x), walk_forward_config)
    metadata = {
        "num_samples": int(len(x)),
        "window": dataset_config.window,
        "horizon": dataset_config.horizon,
        "stride": dataset_config.stride,
        "target_mode": dataset_config.target_mode,
        "task_type": infer_task_type(dataset_config.target_mode),
        "target_dimension": target_dimension(dataset_config.target_mode, dataset_config.horizon),
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "split_counts": {
            "train": int(len(splits["train"])),
            "validation": int(len(splits["validation"])),
            "test": int(len(splits["test"])),
        },
        "walk_forward_folds": len(wf_slices),
        "walk_forward_slices": wf_slices,
    }

    return DatasetBundle(
        x_all=x_all_scaled,
        y_all=y,
        x_train=x_train_scaled,
        y_train=y_train,
        x_validation=x_validation_scaled,
        y_validation=y_validation,
        x_test=x_test_scaled,
        y_test=y_test,
        train_indices=splits["train"],
        validation_indices=splits["validation"],
        test_indices=splits["test"],
        scaler=scaler,
        feature_names=feature_names,
        sample_metadata=sample_metadata,
        dataset_metadata=metadata,
    )


def save_dataset_bundle(bundle: DatasetBundle, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_dir / "dataset.npz",
        x_all=bundle.x_all,
        y_all=bundle.y_all,
        x_train=bundle.x_train,
        y_train=bundle.y_train,
        x_validation=bundle.x_validation,
        y_validation=bundle.y_validation,
        x_test=bundle.x_test,
        y_test=bundle.y_test,
        train_indices=bundle.train_indices,
        validation_indices=bundle.validation_indices,
        test_indices=bundle.test_indices,
    )
    bundle.sample_metadata.to_parquet(output_dir / "sample_metadata.parquet", index=False)
    save_json(bundle.dataset_metadata, output_dir / "metadata.json")
    save_pickle(bundle.scaler, output_dir / "scaler.pkl")


def load_saved_dataset_bundle(output_dir: Path) -> DatasetBundle:
    arrays = np.load(output_dir / "dataset.npz")
    sample_metadata = pd.read_parquet(output_dir / "sample_metadata.parquet")
    metadata = load_json(output_dir / "metadata.json")
    scaler: StandardScaler = load_pickle(output_dir / "scaler.pkl")

    return DatasetBundle(
        x_all=arrays["x_all"],
        y_all=arrays["y_all"],
        x_train=arrays["x_train"],
        y_train=arrays["y_train"],
        x_validation=arrays["x_validation"],
        y_validation=arrays["y_validation"],
        x_test=arrays["x_test"],
        y_test=arrays["y_test"],
        train_indices=arrays["train_indices"],
        validation_indices=arrays["validation_indices"],
        test_indices=arrays["test_indices"],
        scaler=scaler,
        feature_names=list(metadata["feature_names"]),
        sample_metadata=sample_metadata,
        dataset_metadata=metadata,
    )
