from __future__ import annotations

from datetime import timedelta
from typing import Any

import numpy as np
import pandas as pd


def _infer_expected_interval(group: pd.DataFrame) -> timedelta | None:
    if len(group) < 3:
        return None
    diffs = group["timestamp"].diff().dropna()
    if diffs.empty:
        return None
    mode_values = diffs.mode()
    if mode_values.empty:
        return None
    return mode_values.iloc[0].to_pytimedelta()


def _missing_and_irregular_counts(group: pd.DataFrame, expected: timedelta | None) -> tuple[int, int]:
    if expected is None or len(group) < 2:
        return 0, 0
    diffs = group["timestamp"].diff().dropna()
    expected_seconds = expected.total_seconds()
    if expected_seconds <= 0:
        return 0, 0

    missing = 0
    irregular = 0
    for delta in diffs:
        delta_seconds = delta.total_seconds()
        if delta_seconds <= expected_seconds:
            continue
        steps = delta_seconds / expected_seconds
        rounded = int(round(steps))
        if rounded >= 2 and abs(steps - rounded) < 1e-6:
            missing += rounded - 1
        else:
            irregular += 1
    return missing, irregular


def dataset_quality_report(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {
            "total_rows": 0,
            "symbol_count": 0,
            "timeframe_count": 0,
            "date_range": {"start": None, "end": None},
            "duplicate_rows": 0,
            "nan_counts": {},
            "groups": [],
            "warnings": ["Dataset is empty."],
        }

    required_columns = {"timestamp", "open", "high", "low", "close", "volume", "symbol", "timeframe"}
    missing = required_columns.difference(frame.columns)
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise ValueError(f"Dataset missing required columns: {missing_columns}")

    df = frame.sort_values(["symbol", "timeframe", "timestamp"]).reset_index(drop=True)
    duplicate_rows = int(df.duplicated(subset=["symbol", "timeframe", "timestamp"]).sum())
    nan_counts = {column: int(df[column].isna().sum()) for column in ["timestamp", "open", "high", "low", "close", "volume"]}

    malformed_ohlc_mask = (
        (df["high"] < df[["open", "close"]].max(axis=1))
        | (df["low"] > df[["open", "close"]].min(axis=1))
        | (df["high"] < df["low"])
    )
    malformed_ohlc_rows = int(malformed_ohlc_mask.sum())

    groups: list[dict[str, Any]] = []
    warnings: list[str] = []
    for (symbol, timeframe), group in df.groupby(["symbol", "timeframe"], sort=True):
        group = group.sort_values("timestamp").reset_index(drop=True)
        expected_interval = _infer_expected_interval(group)
        missing_timestamps, irregular_intervals = _missing_and_irregular_counts(group, expected_interval)
        group_duplicates = int(group.duplicated(subset=["timestamp"]).sum())
        group_nan = int(group[["timestamp", "open", "high", "low", "close", "volume"]].isna().sum().sum())
        group_malformed = int(
            (
                (group["high"] < group[["open", "close"]].max(axis=1))
                | (group["low"] > group[["open", "close"]].min(axis=1))
                | (group["high"] < group["low"])
            ).sum()
        )

        groups.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "rows": int(len(group)),
                "start": group["timestamp"].iloc[0].isoformat() if len(group) else None,
                "end": group["timestamp"].iloc[-1].isoformat() if len(group) else None,
                "expected_interval_seconds": expected_interval.total_seconds() if expected_interval else None,
                "missing_timestamps": int(missing_timestamps),
                "duplicate_timestamps": int(group_duplicates),
                "group_nan_values": group_nan,
                "irregular_intervals": int(irregular_intervals),
                "malformed_ohlc_rows": group_malformed,
            }
        )

        if group_duplicates > 0:
            warnings.append(f"{symbol}/{timeframe}: duplicate timestamps detected ({group_duplicates}).")
        if missing_timestamps > 0:
            warnings.append(f"{symbol}/{timeframe}: missing timestamps detected ({missing_timestamps}).")
        if irregular_intervals > 0:
            warnings.append(f"{symbol}/{timeframe}: irregular intervals detected ({irregular_intervals}).")
        if group_nan > 0:
            warnings.append(f"{symbol}/{timeframe}: NaN values detected ({group_nan}).")
        if group_malformed > 0:
            warnings.append(f"{symbol}/{timeframe}: malformed OHLC rows detected ({group_malformed}).")

    quality = {
        "total_rows": int(len(df)),
        "symbol_count": int(df["symbol"].nunique()),
        "timeframe_count": int(df["timeframe"].nunique()),
        "date_range": {
            "start": df["timestamp"].min().isoformat(),
            "end": df["timestamp"].max().isoformat(),
        },
        "duplicate_rows": duplicate_rows,
        "malformed_ohlc_rows": malformed_ohlc_rows,
        "nan_counts": nan_counts,
        "groups": groups,
        "warnings": warnings,
    }
    return quality
