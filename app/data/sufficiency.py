from __future__ import annotations

from typing import Any

import pandas as pd


def _usable_windows(row_count: int, window: int, horizon: int, stride: int) -> int:
    raw = row_count - window - horizon + 1
    if raw <= 0:
        return 0
    return (raw - 1) // stride + 1


def _split_counts(total_windows: int, train_ratio: float, validation_ratio: float, gap: int) -> dict[str, int]:
    if total_windows <= 0:
        return {"train": 0, "validation": 0, "test": 0}

    train_end = int(total_windows * train_ratio)
    validation_end = train_end + int(total_windows * validation_ratio)
    train_end = max(1, min(train_end, total_windows - 2))
    validation_end = max(train_end + 1, min(validation_end, total_windows - 1))

    train_count = train_end
    validation_count = max(0, validation_end - (train_end + gap))
    test_count = max(0, total_windows - (validation_end + gap))

    if validation_count == 0 or test_count == 0:
        validation_count = max(0, validation_end - train_end)
        test_count = max(0, total_windows - validation_end)

    return {"train": int(train_count), "validation": int(validation_count), "test": int(test_count)}


def _walk_forward_possible(total_windows: int, train_windows: int, validation_windows: int, test_windows: int, step_windows: int) -> int:
    needed = train_windows + validation_windows + test_windows
    if total_windows < needed:
        return 0
    folds = 1 + (total_windows - needed) // step_windows
    return int(max(0, folds))


def _verdict_from_windows(total_windows: int) -> str:
    if total_windows < 1_000:
        return "insufficient"
    if total_windows < 8_000:
        return "marginal"
    return "sufficient"


def data_sufficiency_report(
    frame: pd.DataFrame,
    *,
    window: int,
    horizon: int,
    stride: int,
    train_ratio: float,
    validation_ratio: float,
    gap: int,
    wf_train_windows: int,
    wf_validation_windows: int,
    wf_test_windows: int,
    wf_step_windows: int,
) -> dict[str, Any]:
    if frame.empty:
        return {
            "dataset_present": False,
            "verdict": "insufficient",
            "reason": "No rows in dataset.",
            "groups": [],
            "warnings": [
                "Dataset is empty. Provide a CSV/parquet file before training.",
                "No sufficiency estimate can be produced for window=500 horizon=60 without data.",
            ],
        }

    groups: list[dict[str, Any]] = []
    warnings: list[str] = []
    verdict_rank = {"insufficient": 0, "marginal": 1, "sufficient": 2}
    global_verdict = "sufficient"

    for (symbol, timeframe), group in frame.groupby(["symbol", "timeframe"], sort=True):
        row_count = int(len(group))
        windows = _usable_windows(row_count, window, horizon, stride)
        split_counts = _split_counts(windows, train_ratio, validation_ratio, gap)
        walk_forward_folds = _walk_forward_possible(
            windows,
            wf_train_windows,
            wf_validation_windows,
            wf_test_windows,
            wf_step_windows,
        )
        verdict = _verdict_from_windows(windows)
        if verdict_rank[verdict] < verdict_rank[global_verdict]:
            global_verdict = verdict

        group_warnings: list[str] = []
        if windows <= 0:
            group_warnings.append("Not enough rows to build any training windows.")
        if windows < 20_000:
            group_warnings.append("Likely too small for deep sequence models to generalize reliably.")
        if row_count < (window + horizon) * 10:
            group_warnings.append("Horizon=60 may be too ambitious for available history.")
        if split_counts["validation"] == 0 or split_counts["test"] == 0:
            group_warnings.append("Chronological split leaves empty validation or test windows.")
        if walk_forward_folds < 2:
            group_warnings.append("Walk-forward validation has fewer than 2 usable folds.")

        warnings.extend([f"{symbol}/{timeframe}: {message}" for message in group_warnings])
        groups.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "rows": row_count,
                "usable_windows": windows,
                "split_windows": split_counts,
                "walk_forward_folds": walk_forward_folds,
                "verdict": verdict,
                "warnings": group_warnings,
            }
        )

    return {
        "dataset_present": True,
        "window": window,
        "horizon": horizon,
        "stride": stride,
        "groups": groups,
        "verdict": global_verdict,
        "warnings": warnings,
    }
