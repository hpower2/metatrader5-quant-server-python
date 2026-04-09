from __future__ import annotations

from datetime import UTC, datetime, timedelta

from dateutil import parser


TIMEFRAME_TO_DELTA = {
    "M1": timedelta(minutes=1),
    "M5": timedelta(minutes=5),
    "M15": timedelta(minutes=15),
    "M30": timedelta(minutes=30),
    "H1": timedelta(hours=1),
    "H4": timedelta(hours=4),
    "D1": timedelta(days=1),
}


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def parse_api_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return ensure_utc(value)
    try:
        return ensure_utc(parser.isoparse(value))
    except (ValueError, TypeError):
        return ensure_utc(parser.parse(value))


def timeframe_to_timedelta(timeframe: str) -> timedelta:
    try:
        return TIMEFRAME_TO_DELTA[timeframe.upper()]
    except KeyError as exc:
        raise ValueError(f"Unsupported timeframe: {timeframe}") from exc
