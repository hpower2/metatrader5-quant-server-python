from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.config.schema import DataConfig


def load_ohlcv(config: DataConfig) -> pd.DataFrame:
    path = config.input_path
    if not path.exists():
        raise FileNotFoundError(f"Input dataset not found: {path}")

    if path.suffix.lower() == ".csv":
        raw = pd.read_csv(path)
    elif path.suffix.lower() in {".parquet", ".pq"}:
        raw = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported input format: {path.suffix}. Use .csv or .parquet")

    return normalize_ohlcv_columns(raw, config)


def normalize_ohlcv_columns(frame: pd.DataFrame, config: DataConfig) -> pd.DataFrame:
    df = frame.copy()
    lower_map = {column.lower(): column for column in df.columns}

    def find_column(name: str) -> str | None:
        if name in df.columns:
            return name
        return lower_map.get(name.lower())

    timestamp_col = find_column(config.timestamp_col)
    open_col = find_column(config.open_col)
    high_col = find_column(config.high_col)
    low_col = find_column(config.low_col)
    close_col = find_column(config.close_col)
    volume_col = find_column(config.volume_col)

    if volume_col is None:
        volume_col = find_column("tick_volume") or find_column("real_volume")

    if None in {timestamp_col, open_col, high_col, low_col, close_col, volume_col}:
        raise ValueError(
            "Missing required OHLCV columns. Required: timestamp/open/high/low/close/volume "
            "(volume can also be tick_volume or real_volume)."
        )

    symbol_col = find_column(config.symbol_col)
    timeframe_col = find_column(config.timeframe_col)

    normalized = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(df[timestamp_col], utc=True, errors="coerce"),
            "open": pd.to_numeric(df[open_col], errors="coerce"),
            "high": pd.to_numeric(df[high_col], errors="coerce"),
            "low": pd.to_numeric(df[low_col], errors="coerce"),
            "close": pd.to_numeric(df[close_col], errors="coerce"),
            "volume": pd.to_numeric(df[volume_col], errors="coerce"),
        }
    )

    if symbol_col is not None:
        normalized["symbol"] = df[symbol_col].astype(str)
    else:
        normalized["symbol"] = config.default_symbol

    if timeframe_col is not None:
        normalized["timeframe"] = df[timeframe_col].astype(str)
    else:
        normalized["timeframe"] = config.default_timeframe

    normalized = normalized.sort_values(["symbol", "timeframe", "timestamp"]).reset_index(drop=True)
    return normalized
