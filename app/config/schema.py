from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

TargetMode = Literal[
    "future_close_return",
    "future_close_path",
    "future_ohlc_path",
    "direction_over_horizon",
    "tp_before_sl",
    "mfe_mae",
]

ModelName = Literal["mlp", "cnn1d", "gru"]


class DataConfig(BaseModel):
    input_path: Path
    timestamp_col: str = "timestamp"
    open_col: str = "open"
    high_col: str = "high"
    low_col: str = "low"
    close_col: str = "close"
    volume_col: str = "volume"
    symbol_col: str = "symbol"
    timeframe_col: str = "timeframe"
    default_symbol: str = "UNKNOWN"
    default_timeframe: str = "UNKNOWN"
    timezone: str = "UTC"


class FeatureConfig(BaseModel):
    rolling_vol_window: int = 20
    atr_window: int = 14
    ema_window: int = 20
    include_ema_distance: bool = True


class DatasetConfig(BaseModel):
    window: int = 500
    horizon: int = 60
    stride: int = 1
    target_mode: TargetMode = "future_close_return"
    direction_threshold: float = 0.0
    tp_pct: float = 0.003
    sl_pct: float = 0.002

    @model_validator(mode="after")
    def validate_window(self) -> "DatasetConfig":
        if self.window < 5:
            raise ValueError("dataset.window must be >= 5")
        if self.horizon < 1:
            raise ValueError("dataset.horizon must be >= 1")
        if self.stride < 1:
            raise ValueError("dataset.stride must be >= 1")
        if self.tp_pct <= 0 or self.sl_pct <= 0:
            raise ValueError("dataset.tp_pct and dataset.sl_pct must be > 0")
        return self


class SplitConfig(BaseModel):
    train_ratio: float = 0.7
    validation_ratio: float = 0.15
    test_ratio: float = 0.15
    gap: int = 60

    @model_validator(mode="after")
    def validate_ratios(self) -> "SplitConfig":
        if min(self.train_ratio, self.validation_ratio, self.test_ratio) <= 0:
            raise ValueError("split ratios must all be > 0")
        ratio_sum = self.train_ratio + self.validation_ratio + self.test_ratio
        if abs(ratio_sum - 1.0) > 1e-9:
            raise ValueError("split ratios must sum to 1.0")
        if self.gap < 0:
            raise ValueError("split.gap must be >= 0")
        return self


class WalkForwardConfig(BaseModel):
    enabled: bool = True
    train_windows: int = 3000
    validation_windows: int = 1000
    test_windows: int = 1000
    step_windows: int = 500
    max_folds: int = 5

    @model_validator(mode="after")
    def validate_values(self) -> "WalkForwardConfig":
        if min(self.train_windows, self.validation_windows, self.test_windows, self.step_windows, self.max_folds) <= 0:
            raise ValueError("walk_forward values must all be > 0")
        return self


class ModelConfig(BaseModel):
    name: ModelName = "mlp"
    hidden_dim: int = 128
    num_layers: int = 2
    dropout: float = 0.1
    cnn_channels: int = 64
    cnn_kernel_size: int = 5
    gru_hidden_size: int = 96
    gru_num_layers: int = 2


class TrainingConfig(BaseModel):
    batch_size: int = 128
    epochs: int = 30
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5
    early_stopping_patience: int = 6
    seed: int = 42
    device: Literal["auto", "cpu", "cuda"] = "auto"
    num_workers: int = 0


class BacktestConfig(BaseModel):
    signal_threshold: float = 0.0005
    probability_threshold: float = 0.55
    fee_bps: float = 1.0
    spread_bps: float = 0.5
    slippage_bps: float = 0.5


class RunConfig(BaseModel):
    run_name: str | None = None
    data: DataConfig
    features: FeatureConfig = Field(default_factory=FeatureConfig)
    dataset: DatasetConfig = Field(default_factory=DatasetConfig)
    split: SplitConfig = Field(default_factory=SplitConfig)
    walk_forward: WalkForwardConfig = Field(default_factory=WalkForwardConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
