from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import Field, field_validator

from libs.common.time import parse_api_datetime
from libs.common.types import PlatformModel


class Timeframe(str, Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


class CandlePayload(PlatformModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int
    real_volume: int

    @field_validator("time", mode="before")
    @classmethod
    def _normalize_time(cls, value: object) -> datetime:
        dt = parse_api_datetime(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)


class SymbolSummaryPayload(PlatformModel):
    name: str
    description: str | None = None
    path: str | None = None
    visible: bool = False
    trade_mode: int | None = None
    digits: int | None = None


class SymbolListPayload(PlatformModel):
    count: int
    symbols: list[SymbolSummaryPayload]


class SymbolInfoPayload(PlatformModel):
    name: str
    description: str | None = None
    path: str | None = None
    points: int | None = None
    price_digits: int | None = None
    spread: float | None = None
    trade_mode: int | None = None
    volume_max: float | None = None
    volume_min: float | None = None
    volume_step: float | None = None


class SymbolTickPayload(PlatformModel):
    ask: float
    bid: float
    last: float
    time: datetime
    volume: int

    @field_validator("time", mode="before")
    @classmethod
    def _parse_epoch_seconds(cls, value: object) -> datetime:
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromtimestamp(int(value), tz=UTC)
        return dt.astimezone(UTC)


class MT5HealthPayload(PlatformModel):
    status: str = Field(default="unknown")
    mt5_initialized: bool = False
    mt5_connected: bool = False
    mt5_terminal_installed: bool | None = None
