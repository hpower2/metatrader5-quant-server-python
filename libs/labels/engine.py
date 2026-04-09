from __future__ import annotations

import pandas as pd
from pydantic import Field

from libs.common.types import PlatformModel


class BarrierConfig(PlatformModel):
    enabled: bool = False
    take_profit_pct: float = 0.002
    stop_loss_pct: float = 0.001


class LabelConfig(PlatformModel):
    horizon_bars: int = 5
    return_threshold: float = 0.0005
    barrier: BarrierConfig = Field(default_factory=BarrierConfig)


def _compute_barrier_label(group: pd.DataFrame, config: LabelConfig) -> pd.Series:
    if not config.barrier.enabled:
        return pd.Series(index=group.index, dtype="float64")

    labels: list[int] = []
    for idx in range(len(group)):
        entry = group.iloc[idx]["close"]
        future = group.iloc[idx + 1 : idx + 1 + config.horizon_bars]
        outcome = 0
        upper = entry * (1 + config.barrier.take_profit_pct)
        lower = entry * (1 - config.barrier.stop_loss_pct)
        for _, row in future.iterrows():
            if row["high"] >= upper:
                outcome = 1
                break
            if row["low"] <= lower:
                outcome = -1
                break
        labels.append(outcome if not future.empty else 0)
    return pd.Series(labels, index=group.index, dtype="int64")


def create_labels(frame: pd.DataFrame, config: LabelConfig | None = None) -> pd.DataFrame:
    config = config or LabelConfig()
    if frame.empty:
        return frame.copy()

    df = frame.copy()
    df = df.sort_values(["symbol", "timeframe", "timestamp"]).reset_index(drop=True)

    def per_group(group: pd.DataFrame) -> pd.DataFrame:
        # Preserve grouping keys across pandas versions where groupby.apply may omit key columns.
        group_key = group.name if isinstance(group.name, tuple) else (group.name, None)
        symbol_key = group_key[0]
        timeframe_key = group_key[1]

        group = group.copy()
        horizon = config.horizon_bars
        future_close = group["close"].shift(-horizon)
        group[f"next_return_{horizon}"] = future_close / group["close"] - 1
        group[f"direction_label_{horizon}"] = group[f"next_return_{horizon}"].apply(
            lambda value: 1 if value > 0 else (-1 if value < 0 else 0)
        )
        threshold = config.return_threshold
        group[f"threshold_label_{horizon}"] = group[f"next_return_{horizon}"].apply(
            lambda value: 1 if value >= threshold else (-1 if value <= -threshold else 0)
        )
        if config.barrier.enabled:
            group[f"barrier_label_{horizon}"] = _compute_barrier_label(group, config)
        group["symbol"] = group.get("symbol", pd.Series([symbol_key] * len(group), index=group.index))
        group["timeframe"] = group.get("timeframe", pd.Series([timeframe_key] * len(group), index=group.index))
        return group

    return df.groupby(["symbol", "timeframe"], group_keys=False).apply(per_group).reset_index(drop=True)
