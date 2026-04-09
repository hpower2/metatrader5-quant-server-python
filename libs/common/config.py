from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class QuantSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "mt5-quant-platform"
    environment: str = "development"
    log_level: str = "INFO"
    log_json: bool = True

    database_url: str = "postgresql+psycopg://admin:1234@postgres:5432/postgres"
    mt5_api_base_url: str = "http://mt5:5001"
    mt5_api_auth_header: str = Field(default="", description="Full Authorization header value.")
    mt5_api_timeout_seconds: float = 15.0
    mt5_api_max_retries: int = 3
    mt5_api_retry_backoff_seconds: float = 1.0
    mt5_api_verify_tls: bool = True

    internal_api_host: str = "0.0.0.0"
    internal_api_port: int = 8010

    default_symbols: Annotated[list[str], NoDecode] = Field(default_factory=list)
    default_timeframes: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["M1", "M5", "M15"])
    symbol_visible_only: bool = True

    incremental_sync_num_bars: int = 500
    incremental_sync_overlap_bars: int = 50
    historical_backfill_chunk_minutes: int = 1440

    feature_windows: Annotated[list[int], NoDecode] = Field(default_factory=lambda: [5, 14, 20, 50])
    label_horizon_bars: int = 5
    label_return_threshold: float = 0.0005

    dataset_output_dir: Path = Path("artifacts/datasets")
    backtest_output_dir: Path = Path("artifacts/backtests")

    worker_sync_interval_seconds: int = 300
    worker_bootstrap_on_start: bool = False
    worker_incremental_on_start: bool = False

    paper_initial_cash: float = 100_000.0
    paper_default_slippage_bps: float = 1.0

    @field_validator("default_symbols", "default_timeframes", "feature_windows", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            if not items:
                return []
            if all(item.lstrip("-").isdigit() for item in items):
                return [int(item) for item in items]
            return items
        return value


@lru_cache(maxsize=1)
def get_settings() -> QuantSettings:
    return QuantSettings()
