from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from libs.common.types import PlatformModel


class SymbolCatalogRecord(PlatformModel):
    symbol: str
    description: str | None = None
    path: str | None = None
    visible: bool = False
    digits: int | None = None
    trade_mode: int | None = None
    points: int | None = None
    price_digits: int | None = None
    spread: float | None = None
    volume_max: float | None = None
    volume_min: float | None = None
    volume_step: float | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    source_updated_at: datetime
    last_seen_at: datetime


class CanonicalCandleRecord(PlatformModel):
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    real_volume: int
    spread: int
    source: str = "mt5_api"
    ingestion_time: datetime
    raw_hash: str
    raw_payload: dict[str, Any]
    quality_flags: list[str] = Field(default_factory=list)


class QualityIssueRecord(PlatformModel):
    symbol: str
    timeframe: str
    issue_type: str
    severity: str
    timestamp: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class CheckpointRecord(PlatformModel):
    job_type: str
    symbol: str = "__all__"
    timeframe: str = "__all__"
    last_synced_at: datetime | None = None
    last_ingested_bar_at: datetime | None = None
    cursor: dict[str, Any] = Field(default_factory=dict)
    last_status: str = "pending"
    last_error: str | None = None
