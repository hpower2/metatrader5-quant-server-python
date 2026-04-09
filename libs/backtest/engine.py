from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import Field

from libs.common.config import QuantSettings, get_settings
from libs.common.types import PlatformModel
from libs.storage.db import db_session
from libs.storage.repositories import ArtifactRepository


class BacktestConfig(PlatformModel):
    strategy_name: str = "signal_strategy"
    signal_column: str = "signal"
    initial_cash: float = 100_000.0
    fee_bps: float = 1.0
    slippage_bps: float = 1.0
    fixed_quantity: float = 1.0
    risk_per_trade: float | None = None
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None


class TradeRecord(PlatformModel):
    entry_time: str
    exit_time: str
    side: int
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float


@dataclass
class BacktestArtifacts:
    trades: pd.DataFrame
    equity_curve: pd.DataFrame
    metrics: dict[str, float]
    artifact_dir: Path


class SignalBacktester:
    def __init__(self, settings: QuantSettings | None = None) -> None:
        self.settings = settings or get_settings()

    def run(self, frame: pd.DataFrame, config: BacktestConfig) -> BacktestArtifacts:
        if frame.empty:
            raise ValueError("Backtest frame is empty")
        if config.signal_column not in frame.columns:
            raise ValueError(f"Missing signal column: {config.signal_column}")

        df = frame.sort_values("timestamp").reset_index(drop=True).copy()
        cash = config.initial_cash
        position_side = 0
        position_qty = 0.0
        entry_price = 0.0
        entry_time = None
        trades: list[dict[str, float | str | int]] = []
        equity_rows: list[dict[str, float | str]] = []

        for idx in range(1, len(df)):
            previous_signal = int(np.sign(df.iloc[idx - 1][config.signal_column]))
            bar = df.iloc[idx]
            open_price = float(bar["open"])
            high = float(bar["high"])
            low = float(bar["low"])
            close = float(bar["close"])
            timestamp = bar["timestamp"]

            if position_side != 0:
                stop_hit, target_hit, exit_price = self._check_exit_hooks(
                    entry_price=entry_price,
                    side=position_side,
                    high=high,
                    low=low,
                    config=config,
                )
                if stop_hit or target_hit:
                    trade_pnl = self._close_position(
                        trades=trades,
                        cash=cash,
                        side=position_side,
                        quantity=position_qty,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        entry_time=entry_time,
                        exit_time=timestamp,
                        config=config,
                    )
                    cash += trade_pnl
                    position_side = 0
                    position_qty = 0.0
                    entry_price = 0.0
                    entry_time = None

            if previous_signal != position_side:
                if position_side != 0:
                    trade_pnl = self._close_position(
                        trades=trades,
                        cash=cash,
                        side=position_side,
                        quantity=position_qty,
                        entry_price=entry_price,
                        exit_price=self._apply_slippage(open_price, -position_side, config.slippage_bps),
                        entry_time=entry_time,
                        exit_time=timestamp,
                        config=config,
                    )
                    cash += trade_pnl
                    position_side = 0
                    position_qty = 0.0
                    entry_price = 0.0
                    entry_time = None
                if previous_signal != 0:
                    position_side = previous_signal
                    position_qty = self._position_size(cash=cash, open_price=open_price, config=config)
                    entry_price = self._apply_slippage(open_price, position_side, config.slippage_bps)
                    entry_time = timestamp
                    cash -= self._transaction_cost(entry_price, position_qty, config.fee_bps)

            unrealized = 0.0
            if position_side != 0:
                unrealized = (close - entry_price) * position_qty * position_side
            equity_rows.append({"timestamp": timestamp, "equity": cash + unrealized})

        trades_df = pd.DataFrame(trades)
        equity_curve = pd.DataFrame(equity_rows)
        metrics = self._metrics(trades_df, equity_curve, config.initial_cash)
        artifact_dir = self._export(trades_df, equity_curve, metrics, config)

        with db_session() as session:
            ArtifactRepository(session).create_backtest_run(
                strategy_name=config.strategy_name,
                config=config.model_dump(mode="json"),
                metrics=metrics,
                artifact_path=str(artifact_dir),
            )

        return BacktestArtifacts(trades=trades_df, equity_curve=equity_curve, metrics=metrics, artifact_dir=artifact_dir)

    def _apply_slippage(self, price: float, side: int, slippage_bps: float) -> float:
        adjustment = price * (slippage_bps / 10_000.0)
        return price + adjustment if side > 0 else price - adjustment

    def _transaction_cost(self, price: float, quantity: float, fee_bps: float) -> float:
        return price * quantity * (fee_bps / 10_000.0)

    def _position_size(self, *, cash: float, open_price: float, config: BacktestConfig) -> float:
        if config.risk_per_trade and config.stop_loss_pct:
            risk_capital = cash * config.risk_per_trade
            stop_distance = open_price * config.stop_loss_pct
            return max(risk_capital / stop_distance, 0.0)
        return config.fixed_quantity

    def _check_exit_hooks(
        self,
        *,
        entry_price: float,
        side: int,
        high: float,
        low: float,
        config: BacktestConfig,
    ) -> tuple[bool, bool, float]:
        stop_hit = False
        target_hit = False
        exit_price = entry_price
        if side > 0:
            if config.stop_loss_pct is not None and low <= entry_price * (1 - config.stop_loss_pct):
                stop_hit = True
                exit_price = entry_price * (1 - config.stop_loss_pct)
            if config.take_profit_pct is not None and high >= entry_price * (1 + config.take_profit_pct):
                target_hit = True
                exit_price = entry_price * (1 + config.take_profit_pct)
        else:
            if config.stop_loss_pct is not None and high >= entry_price * (1 + config.stop_loss_pct):
                stop_hit = True
                exit_price = entry_price * (1 + config.stop_loss_pct)
            if config.take_profit_pct is not None and low <= entry_price * (1 - config.take_profit_pct):
                target_hit = True
                exit_price = entry_price * (1 - config.take_profit_pct)
        return stop_hit, target_hit, exit_price

    def _close_position(
        self,
        *,
        trades: list[dict[str, float | str | int]],
        cash: float,
        side: int,
        quantity: float,
        entry_price: float,
        exit_price: float,
        entry_time: object,
        exit_time: object,
        config: BacktestConfig,
    ) -> float:
        fees = self._transaction_cost(exit_price, quantity, config.fee_bps)
        pnl = (exit_price - entry_price) * quantity * side - fees
        trades.append(
            {
                "entry_time": str(entry_time),
                "exit_time": str(exit_time),
                "side": side,
                "quantity": quantity,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl": pnl,
            }
        )
        return pnl

    def _metrics(self, trades: pd.DataFrame, equity_curve: pd.DataFrame, initial_cash: float) -> dict[str, float]:
        if equity_curve.empty:
            return {}
        returns = equity_curve["equity"].pct_change().dropna()
        downside = returns[returns < 0]
        rolling_max = equity_curve["equity"].cummax()
        drawdown = (equity_curve["equity"] - rolling_max) / rolling_max.replace(0, np.nan)
        metrics = {
            "final_equity": float(equity_curve["equity"].iloc[-1]),
            "total_return": float(equity_curve["equity"].iloc[-1] / initial_cash - 1),
            "max_drawdown": float(drawdown.min()) if not drawdown.empty else 0.0,
            "trade_count": float(len(trades)),
            "expectancy": float(trades["pnl"].mean()) if not trades.empty else 0.0,
            "win_rate": float((trades["pnl"] > 0).mean()) if not trades.empty else 0.0,
            "sharpe": float((returns.mean() / returns.std()) * np.sqrt(252)) if len(returns) > 1 and returns.std() else 0.0,
            "sortino": float((returns.mean() / downside.std()) * np.sqrt(252)) if len(downside) > 1 and downside.std() else 0.0,
        }
        return metrics

    def _export(
        self,
        trades: pd.DataFrame,
        equity_curve: pd.DataFrame,
        metrics: dict[str, float],
        config: BacktestConfig,
    ) -> Path:
        artifact_dir = self.settings.backtest_output_dir / config.strategy_name
        artifact_dir.mkdir(parents=True, exist_ok=True)
        trades.to_parquet(artifact_dir / "trades.parquet", index=False)
        equity_curve.to_parquet(artifact_dir / "equity_curve.parquet", index=False)
        (artifact_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return artifact_dir
