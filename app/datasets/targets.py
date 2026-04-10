from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from app.config.schema import DatasetConfig, TargetMode

TaskType = Literal["regression", "binary_classification"]


def infer_task_type(target_mode: TargetMode) -> TaskType:
    if target_mode in {"direction_over_horizon", "tp_before_sl"}:
        return "binary_classification"
    return "regression"


def target_dimension(target_mode: TargetMode, horizon: int) -> int:
    if target_mode == "future_close_path":
        return horizon
    if target_mode == "future_ohlc_path":
        return horizon * 4
    if target_mode == "mfe_mae":
        return 2
    return 1


def build_target(
    future: pd.DataFrame,
    anchor_close: float,
    config: DatasetConfig,
) -> tuple[np.ndarray, dict[str, float]]:
    if future.empty:
        raise ValueError("Future slice is empty while building target.")

    anchor = anchor_close if abs(anchor_close) > 1e-12 else 1e-12
    close_returns = future["close"].to_numpy(dtype=np.float64) / anchor - 1.0
    future_return = float(close_returns[-1])
    highs = future["high"].to_numpy(dtype=np.float64)
    lows = future["low"].to_numpy(dtype=np.float64)
    max_favorable = float(np.max(highs / anchor - 1.0))
    max_adverse = float(np.min(lows / anchor - 1.0))

    tp_level = anchor * (1.0 + config.tp_pct)
    sl_level = anchor * (1.0 - config.sl_pct)
    tp_hit_index = _first_hit_index(highs >= tp_level)
    sl_hit_index = _first_hit_index(lows <= sl_level)
    tp_before_sl = 1.0 if _tp_hit_before_sl(tp_hit_index, sl_hit_index) else 0.0

    mode = config.target_mode
    if mode == "future_close_return":
        target = np.array([future_return], dtype=np.float32)
    elif mode == "future_close_path":
        target = close_returns.astype(np.float32)
    elif mode == "future_ohlc_path":
        ohlc = future[["open", "high", "low", "close"]].to_numpy(dtype=np.float64)
        target = (ohlc / anchor - 1.0).reshape(-1).astype(np.float32)
    elif mode == "direction_over_horizon":
        label = 1.0 if future_return > config.direction_threshold else 0.0
        target = np.array([label], dtype=np.float32)
    elif mode == "tp_before_sl":
        target = np.array([tp_before_sl], dtype=np.float32)
    elif mode == "mfe_mae":
        target = np.array([max_favorable, max_adverse], dtype=np.float32)
    else:
        raise ValueError(f"Unsupported target mode: {mode}")

    aux = {
        "future_return": future_return,
        "direction_label": 1.0 if future_return > config.direction_threshold else 0.0,
        "tp_before_sl": tp_before_sl,
        "mfe": max_favorable,
        "mae": max_adverse,
    }
    return target, aux


def _first_hit_index(mask: np.ndarray) -> int | None:
    indices = np.where(mask)[0]
    if len(indices) == 0:
        return None
    return int(indices[0])


def _tp_hit_before_sl(tp_hit_index: int | None, sl_hit_index: int | None) -> bool:
    if tp_hit_index is None:
        return False
    if sl_hit_index is None:
        return True
    return tp_hit_index < sl_hit_index
