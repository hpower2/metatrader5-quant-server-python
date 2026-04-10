from __future__ import annotations

from typing import Any

import numpy as np

from app.config.schema import SplitConfig, WalkForwardConfig


def chronological_split_indices(total_samples: int, split: SplitConfig) -> dict[str, np.ndarray]:
    if total_samples < 3:
        raise ValueError("Need at least 3 samples for chronological split.")

    train_end = int(total_samples * split.train_ratio)
    validation_end = train_end + int(total_samples * split.validation_ratio)

    train_end = max(1, min(train_end, total_samples - 2))
    validation_end = max(train_end + 1, min(validation_end, total_samples - 1))

    gap = max(0, split.gap)
    train_idx = np.arange(0, train_end, dtype=np.int64)
    validation_idx = np.arange(train_end + gap, validation_end, dtype=np.int64)
    test_idx = np.arange(validation_end + gap, total_samples, dtype=np.int64)

    if len(validation_idx) == 0 or len(test_idx) == 0:
        validation_idx = np.arange(train_end, validation_end, dtype=np.int64)
        test_idx = np.arange(validation_end, total_samples, dtype=np.int64)

    if len(validation_idx) == 0 or len(test_idx) == 0:
        raise ValueError("Chronological split produced empty validation or test slice.")

    return {
        "train": train_idx,
        "validation": validation_idx,
        "test": test_idx,
    }


def walk_forward_slices(total_samples: int, config: WalkForwardConfig) -> list[dict[str, Any]]:
    if not config.enabled:
        return []

    slices: list[dict[str, Any]] = []
    start = 0
    fold = 0
    needed = config.train_windows + config.validation_windows + config.test_windows
    while start + needed <= total_samples and fold < config.max_folds:
        train_start = start
        train_end = train_start + config.train_windows
        validation_end = train_end + config.validation_windows
        test_end = validation_end + config.test_windows
        slices.append(
            {
                "fold": fold,
                "train_start": train_start,
                "train_end": train_end,
                "validation_start": train_end,
                "validation_end": validation_end,
                "test_start": validation_end,
                "test_end": test_end,
            }
        )
        start += config.step_windows
        fold += 1
    return slices
