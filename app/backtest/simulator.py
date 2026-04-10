from __future__ import annotations

import numpy as np
import pandas as pd

from app.config.io import load_run_config
from app.evaluation.core import evaluate_run
from app.utils.io import save_json
from app.utils.paths import resolve_run_path


def run_backtest(run_id: str, split: str = "test") -> dict:
    run_path = resolve_run_path(run_id)
    if not run_path.exists():
        raise FileNotFoundError(f"Run not found: {run_id}")

    prediction_path = run_path / "evaluation" / split / "predictions.parquet"
    if not prediction_path.exists():
        evaluate_run(run_id, split=split)  # ensure predictions exist

    config = load_run_config(run_path / "config.yaml")
    predictions = pd.read_parquet(prediction_path)
    mode = config.dataset.target_mode
    threshold = config.backtest.signal_threshold
    prob_threshold = config.backtest.probability_threshold

    if mode in {"future_close_return", "future_close_path", "future_ohlc_path", "mfe_mae"}:
        predictions["predicted_return"] = predictions["y_pred"].apply(_predicted_return_from_vector)
        predictions["signal"] = 0
        predictions.loc[predictions["predicted_return"] >= threshold, "signal"] = 1
        predictions.loc[predictions["predicted_return"] <= -threshold, "signal"] = -1
        predictions["realized_return"] = predictions["future_return"].astype(float)
    elif mode == "direction_over_horizon":
        predictions["signal"] = 0
        predictions.loc[predictions["probability"] >= prob_threshold, "signal"] = 1
        predictions.loc[predictions["probability"] <= (1.0 - prob_threshold), "signal"] = -1
        predictions["realized_return"] = predictions["future_return"].astype(float)
    elif mode == "tp_before_sl":
        predictions["signal"] = (predictions["probability"] >= prob_threshold).astype(int)
        predictions["realized_return"] = np.where(
            predictions["tp_before_sl"] >= 0.5,
            config.dataset.tp_pct,
            -config.dataset.sl_pct,
        )
    else:
        raise ValueError(f"Unsupported target mode for backtest: {mode}")

    total_cost_bps = config.backtest.fee_bps + config.backtest.spread_bps + config.backtest.slippage_bps
    total_cost = total_cost_bps / 10_000.0

    predictions["gross_return"] = predictions["signal"] * predictions["realized_return"]
    predictions["cost"] = predictions["signal"].abs() * total_cost
    predictions["net_return"] = predictions["gross_return"] - predictions["cost"]
    predictions["equity"] = (1.0 + predictions["net_return"]).cumprod()

    trades = predictions[predictions["signal"] != 0].copy()
    positive = trades[trades["net_return"] > 0]["net_return"].sum()
    negative = trades[trades["net_return"] < 0]["net_return"].sum()
    profit_factor = float(positive / abs(negative)) if negative < 0 else None

    metrics = {
        "run_id": run_id,
        "split": split,
        "target_mode": mode,
        "total_trades": int(len(trades)),
        "win_rate": float((trades["net_return"] > 0).mean()) if len(trades) else 0.0,
        "average_return": float(trades["net_return"].mean()) if len(trades) else 0.0,
        "expected_return_next_horizon": float(predictions["gross_return"].mean()),
        "profit_factor": profit_factor,
        "max_drawdown": float(_max_drawdown(predictions["equity"].to_numpy(dtype=float))),
    }

    output_dir = run_path / "backtest" / split
    output_dir.mkdir(parents=True, exist_ok=True)
    trades.to_parquet(output_dir / "trades.parquet", index=False)
    predictions[["anchor_timestamp", "equity"]].to_csv(output_dir / "equity_curve.csv", index=False)
    save_json(metrics, output_dir / "metrics.json")
    return metrics


def _predicted_return_from_vector(values: object) -> float:
    if isinstance(values, list):
        if not values:
            return 0.0
        return float(values[-1])
    if isinstance(values, (float, int)):
        return float(values)
    return 0.0


def _max_drawdown(equity: np.ndarray) -> float:
    if equity.size == 0:
        return 0.0
    peak = np.maximum.accumulate(equity)
    drawdowns = 1.0 - np.divide(equity, np.where(peak == 0.0, 1.0, peak))
    return float(np.max(drawdowns))
