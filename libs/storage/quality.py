from __future__ import annotations

import math
from datetime import UTC, datetime

import pandas as pd

from libs.common.hashing import stable_json_hash
from libs.common.time import timeframe_to_timedelta
from libs.mt5_adapter.models import CandlePayload
from libs.storage.schemas import CanonicalCandleRecord, QualityIssueRecord


def normalize_candles(
    *,
    symbol: str,
    timeframe: str,
    payloads: list[CandlePayload],
    source: str = "mt5_api",
) -> tuple[list[CanonicalCandleRecord], list[QualityIssueRecord]]:
    issues: list[QualityIssueRecord] = []
    deduped: dict[datetime, CandlePayload] = {}
    original_order = [payload.time for payload in payloads]
    ingestion_time = datetime.now(tz=UTC)

    for payload in payloads:
        if payload.time in deduped:
            issues.append(
                QualityIssueRecord(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=payload.time,
                    issue_type="duplicate_bar",
                    severity="warning",
                    details={"timestamp": payload.time.isoformat()},
                )
            )
        deduped[payload.time] = payload

    if original_order != sorted(original_order):
        for previous, current in zip(original_order, original_order[1:]):
            if current < previous:
                issues.append(
                    QualityIssueRecord(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=current,
                        issue_type="out_of_order_timestamp",
                        severity="warning",
                        details={"previous": previous.isoformat(), "current": current.isoformat()},
                    )
                )

    records: list[CanonicalCandleRecord] = []
    for timestamp in sorted(deduped):
        payload = deduped[timestamp]
        quality_flags: list[str] = []
        prices = [payload.open, payload.high, payload.low, payload.close]
        if any(not math.isfinite(price) or price <= 0 for price in prices):
            quality_flags.append("non_positive_or_non_finite_price")
        if payload.low > min(payload.open, payload.close, payload.high):
            quality_flags.append("low_inconsistent")
        if payload.high < max(payload.open, payload.close, payload.low):
            quality_flags.append("high_inconsistent")

        if quality_flags:
            issues.append(
                QualityIssueRecord(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    issue_type="malformed_ohlc",
                    severity="error",
                    details={"flags": quality_flags},
                )
            )

        raw_payload = payload.model_dump(mode="json")
        records.append(
            CanonicalCandleRecord(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=timestamp,
                open=payload.open,
                high=payload.high,
                low=payload.low,
                close=payload.close,
                tick_volume=payload.tick_volume,
                real_volume=payload.real_volume,
                spread=payload.spread,
                source=source,
                ingestion_time=ingestion_time,
                raw_hash=stable_json_hash(raw_payload),
                raw_payload=raw_payload,
                quality_flags=quality_flags,
            )
        )

    issues.extend(detect_gaps(symbol=symbol, timeframe=timeframe, timestamps=[record.timestamp for record in records]))
    return records, issues


def detect_gaps(*, symbol: str, timeframe: str, timestamps: list[datetime]) -> list[QualityIssueRecord]:
    if len(timestamps) < 2:
        return []
    delta = timeframe_to_timedelta(timeframe)
    issues: list[QualityIssueRecord] = []
    for previous, current in zip(timestamps, timestamps[1:]):
        gap = current - previous
        if gap > delta:
            missing_bars = int(gap / delta) - 1
            if missing_bars > 0:
                issues.append(
                    QualityIssueRecord(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=current,
                        issue_type="missing_bars",
                        severity="warning",
                        details={
                            "previous": previous.isoformat(),
                            "current": current.isoformat(),
                            "missing_bars": missing_bars,
                        },
                    )
                )
    return issues


def audit_candles_frame(*, symbol: str, timeframe: str, frame: pd.DataFrame) -> list[QualityIssueRecord]:
    if frame.empty:
        return []

    issues: list[QualityIssueRecord] = []
    ordered = frame.sort_values("timestamp").reset_index(drop=True)
    duplicated = ordered[ordered.duplicated(subset=["timestamp"], keep=False)]
    for row in duplicated.to_dict(orient="records"):
        issues.append(
            QualityIssueRecord(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=row["timestamp"],
                issue_type="duplicate_bar",
                severity="warning",
                details={"timestamp": row["timestamp"].isoformat()},
            )
        )

    issues.extend(
        detect_gaps(
            symbol=symbol,
            timeframe=timeframe,
            timestamps=list(ordered["timestamp"]),
        )
    )

    for row in ordered.to_dict(orient="records"):
        flags: list[str] = []
        prices = [row["open"], row["high"], row["low"], row["close"]]
        if any(not math.isfinite(price) or price <= 0 for price in prices):
            flags.append("non_positive_or_non_finite_price")
        if row["low"] > min(row["open"], row["close"], row["high"]):
            flags.append("low_inconsistent")
        if row["high"] < max(row["open"], row["close"], row["low"]):
            flags.append("high_inconsistent")
        if flags:
            issues.append(
                QualityIssueRecord(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=row["timestamp"],
                    issue_type="malformed_ohlc",
                    severity="error",
                    details={"flags": flags},
                )
            )

    return issues

