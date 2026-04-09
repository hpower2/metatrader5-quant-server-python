from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import Field

from libs.common.types import PlatformModel


class FeatureConfig(PlatformModel):
    windows: list[int] = Field(default_factory=lambda: [5, 14, 20, 50])
    add_multi_timeframe: bool = False


def _compute_rsi(series: pd.Series, window: int) -> pd.Series:
    delta = series.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.rolling(window).mean()
    avg_loss = losses.rolling(window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_features(frame: pd.DataFrame, config: FeatureConfig | None = None) -> pd.DataFrame:
    config = config or FeatureConfig()
    if frame.empty:
        return frame.copy()

    df = frame.copy()
    required_columns = {"symbol", "timeframe", "timestamp", "open", "high", "low", "close", "spread"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"compute_features requires columns: {missing}")

    df = df.sort_values(["symbol", "timeframe", "timestamp"]).reset_index(drop=True)

    def per_group(group: pd.DataFrame) -> pd.DataFrame:
        # Pandas groupby.apply can omit grouping columns depending on version/config;
        # preserve symbol/timeframe deterministically so downstream joins stay stable.
        group_key = group.name if isinstance(group.name, tuple) else (group.name, None)
        symbol_key = group_key[0]
        timeframe_key = group_key[1]

        group = group.copy()
        group["simple_return"] = group["close"].pct_change()
        group["log_return"] = np.log(group["close"]).diff()
        group["candle_range"] = group["high"] - group["low"]
        group["candle_body_size"] = (group["close"] - group["open"]).abs()
        upper_wick = group["high"] - group[["open", "close"]].max(axis=1)
        lower_wick = group[["open", "close"]].min(axis=1) - group["low"]
        group["upper_wick_ratio"] = upper_wick / group["candle_range"].replace(0, np.nan)
        group["lower_wick_ratio"] = lower_wick / group["candle_range"].replace(0, np.nan)
        group["spread_to_close"] = group["spread"] / group["close"].replace(0, np.nan)

        prev_close = group["close"].shift(1)
        true_range = pd.concat(
            [
                group["high"] - group["low"],
                (group["high"] - prev_close).abs(),
                (group["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        group["true_range"] = true_range

        for window in config.windows:
            group[f"rolling_mean_close_w{window}"] = group["close"].rolling(window).mean()
            group[f"rolling_std_return_w{window}"] = group["simple_return"].rolling(window).std()
            group[f"atr_w{window}"] = true_range.rolling(window).mean()
            group[f"rsi_w{window}"] = _compute_rsi(group["close"], window)
            group[f"momentum_w{window}"] = group["close"] / group["close"].shift(window) - 1
            group[f"volatility_w{window}"] = group["simple_return"].rolling(window).std()

        group["symbol"] = group.get("symbol", pd.Series([symbol_key] * len(group), index=group.index))
        group["timeframe"] = group.get("timeframe", pd.Series([timeframe_key] * len(group), index=group.index))

        return group

    return df.groupby(["symbol", "timeframe"], group_keys=False).apply(per_group).reset_index(drop=True)


def join_multi_timeframe_features(base_frame: pd.DataFrame, higher_timeframe_frame: pd.DataFrame, suffix: str) -> pd.DataFrame:
    if base_frame.empty or higher_timeframe_frame.empty:
        return base_frame.copy()
    left = base_frame.sort_values(["symbol", "timestamp"])
    right = higher_timeframe_frame.sort_values(["symbol", "timestamp"]).copy()
    feature_columns = [column for column in right.columns if column not in {"symbol", "timeframe", "timestamp"}]
    renamed = right.rename(columns={column: f"{column}_{suffix}" for column in feature_columns})
    # Keep canonical `timeframe` from the base frame only to avoid timeframe_x/timeframe_y collisions.
    renamed = renamed.drop(columns=["timeframe"], errors="ignore")
    return pd.merge_asof(left, renamed, on="timestamp", by="symbol", direction="backward")
