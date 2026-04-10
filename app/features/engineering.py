from __future__ import annotations

import numpy as np
import pandas as pd

from app.config.schema import FeatureConfig


def build_features(frame: pd.DataFrame, config: FeatureConfig) -> pd.DataFrame:
    required = {"timestamp", "open", "high", "low", "close", "volume", "symbol", "timeframe"}
    missing = required.difference(frame.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Input frame is missing required columns: {missing_text}")

    df = frame.sort_values(["symbol", "timeframe", "timestamp"]).reset_index(drop=True).copy()

    def per_group(group: pd.DataFrame) -> pd.DataFrame:
        g = group.copy()
        g["log_return"] = np.log(g["close"]).diff()
        g["candle_body"] = g["close"] - g["open"]
        g["upper_wick"] = g["high"] - g[["open", "close"]].max(axis=1)
        g["lower_wick"] = g[["open", "close"]].min(axis=1) - g["low"]
        g["range"] = g["high"] - g["low"]
        g["rolling_volatility"] = g["log_return"].rolling(config.rolling_vol_window).std()

        prev_close = g["close"].shift(1)
        true_range = pd.concat(
            [
                g["high"] - g["low"],
                (g["high"] - prev_close).abs(),
                (g["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        g["atr_like"] = true_range.rolling(config.atr_window).mean()
        if config.include_ema_distance:
            ema = g["close"].ewm(span=config.ema_window, adjust=False).mean()
            g["ema_distance"] = (g["close"] / ema) - 1.0
        return g

    engineered = df.groupby(["symbol", "timeframe"], group_keys=False).apply(per_group).reset_index(drop=True)
    return engineered


def feature_columns(frame: pd.DataFrame) -> list[str]:
    ignore = {"timestamp", "symbol", "timeframe"}
    return [column for column in frame.columns if column not in ignore]
