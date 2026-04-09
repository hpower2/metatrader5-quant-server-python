from __future__ import annotations

from typing import Literal

from pydantic import Field

from libs.backtest.engine import BacktestConfig
from libs.common.types import PlatformModel
from libs.datasets.builder import DatasetBuildConfig
from libs.features.engineering import FeatureConfig
from libs.papertrade.engine import PaperOrderRequest


class SyncRunRequest(PlatformModel):
    job_type: Literal["bootstrap_symbols", "historical_backfill", "incremental_sync", "data_quality_audit"]
    symbol: str | None = None
    timeframe: str | None = None
    start: str | None = None
    end: str | None = None
    visible_only: bool | None = None
    search: str | None = None
    num_bars: int | None = None


class FeatureRunRequest(PlatformModel):
    symbol: str
    timeframe: str
    higher_timeframe: str | None = None
    feature_config: FeatureConfig = Field(default_factory=FeatureConfig)


class BacktestRunRequest(PlatformModel):
    symbol: str
    timeframe: str
    dataset_name: str | None = None
    dataset_split: Literal["train", "validation", "test"] = "test"
    fast_window: int = 5
    slow_window: int = 20
    config: BacktestConfig = Field(default_factory=BacktestConfig)


class DatasetRunRequest(DatasetBuildConfig):
    pass


class PaperSignalRequest(PaperOrderRequest):
    pass
