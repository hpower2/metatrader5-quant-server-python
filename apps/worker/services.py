from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from libs.common.config import QuantSettings, get_settings
from libs.common.logging import get_logger
from libs.common.time import ensure_utc, parse_api_datetime
from libs.common.types import JobResult
from libs.mt5_adapter import MT5ApiClient
from libs.storage.db import db_session
from libs.storage.quality import audit_candles_frame, normalize_candles
from libs.storage.repositories import (
    CandleRepository,
    CheckpointRepository,
    IngestionRunRepository,
    QualityRepository,
    SymbolRepository,
)
from libs.storage.schemas import CheckpointRecord, SymbolCatalogRecord


class WorkerService:
    def __init__(self, settings: QuantSettings | None = None) -> None:
        self.settings = settings or get_settings()
        self.logger = get_logger(__name__)

    def bootstrap_symbols(self, *, visible_only: bool | None = None, search: str | None = None) -> JobResult:
        started_at = datetime.now(tz=UTC)
        with MT5ApiClient(self.settings) as client, db_session() as session:
            health = client.ensure_healthy()
            run_repo = IngestionRunRepository(session)
            checkpoint_repo = CheckpointRepository(session)
            symbol_repo = SymbolRepository(session)
            run = run_repo.start(
                job_type="bootstrap_symbols",
                symbol=None,
                timeframe=None,
                metadata={"visible_only": visible_only, "search": search, "health": health.model_dump(mode="json")},
            )
            try:
                payload = client.list_forex_symbols(
                    visible_only=self.settings.symbol_visible_only if visible_only is None else visible_only,
                    search=search,
                )
                now = datetime.now(tz=UTC)
                records: list[SymbolCatalogRecord] = []
                for summary in payload.symbols:
                    info = client.get_symbol_info(summary.name)
                    records.append(
                        SymbolCatalogRecord(
                            symbol=summary.name,
                            description=info.description or summary.description,
                            path=info.path or summary.path,
                            visible=summary.visible,
                            digits=summary.digits,
                            trade_mode=info.trade_mode if info.trade_mode is not None else summary.trade_mode,
                            points=info.points,
                            price_digits=info.price_digits,
                            spread=info.spread,
                            volume_max=info.volume_max,
                            volume_min=info.volume_min,
                            volume_step=info.volume_step,
                            source_metadata={
                                "summary": summary.model_dump(mode="json"),
                                "info": info.model_dump(mode="json"),
                            },
                            source_updated_at=now,
                            last_seen_at=now,
                        )
                    )
                written = symbol_repo.upsert_many(records)
                checkpoint_repo.upsert(
                    CheckpointRecord(
                        job_type="bootstrap_symbols",
                        symbol="__all__",
                        timeframe="__all__",
                        last_synced_at=now,
                        last_status="success",
                        cursor={"count": payload.count},
                    )
                )
                run_repo.finish(run, status="success", records_seen=payload.count, records_written=written)
                self.logger.info("bootstrap_symbols_completed", count=payload.count, written=written)
                return JobResult(
                    job_type="bootstrap_symbols",
                    started_at=started_at,
                    finished_at=datetime.now(tz=UTC),
                    status="success",
                    records_seen=payload.count,
                    records_written=written,
                    metadata={"visible_only": visible_only, "search": search},
                )
            except Exception as exc:
                checkpoint_repo.upsert(
                    CheckpointRecord(
                        job_type="bootstrap_symbols",
                        symbol="__all__",
                        timeframe="__all__",
                        last_synced_at=datetime.now(tz=UTC),
                        last_status="failed",
                        last_error=str(exc),
                    )
                )
                run_repo.finish(run, status="failed", records_seen=0, records_written=0, errors=[str(exc)])
                raise

    def historical_backfill(self, *, symbol: str, timeframe: str, start: datetime, end: datetime) -> JobResult:
        started_at = datetime.now(tz=UTC)
        start = ensure_utc(start)
        end = ensure_utc(end)
        total_seen = 0
        total_written = 0
        chunk_start = start
        chunk_delta = timedelta(minutes=self.settings.historical_backfill_chunk_minutes)

        with MT5ApiClient(self.settings) as client, db_session() as session:
            client.ensure_healthy()
            run_repo = IngestionRunRepository(session)
            checkpoint_repo = CheckpointRepository(session)
            candle_repo = CandleRepository(session)
            quality_repo = QualityRepository(session)
            run = run_repo.start(
                job_type="historical_backfill",
                symbol=symbol,
                timeframe=timeframe,
                metadata={"start": start.isoformat(), "end": end.isoformat()},
            )
            try:
                while chunk_start < end:
                    chunk_end = min(chunk_start + chunk_delta, end)
                    payloads = client.fetch_data_range(symbol=symbol, timeframe=timeframe, start=chunk_start, end=chunk_end)
                    records, issues = normalize_candles(symbol=symbol, timeframe=timeframe, payloads=payloads)
                    total_seen += len(payloads)
                    total_written += candle_repo.upsert_many(records)
                    quality_repo.add_many(issues, run.id)
                    last_bar = records[-1].timestamp if records else checkpoint_repo.get("historical_backfill", symbol, timeframe)
                    checkpoint_repo.upsert(
                        CheckpointRecord(
                            job_type="historical_backfill",
                            symbol=symbol,
                            timeframe=timeframe,
                            last_synced_at=datetime.now(tz=UTC),
                            last_ingested_bar_at=records[-1].timestamp if records else None,
                            last_status="success",
                            cursor={
                                "requested_start": start.isoformat(),
                                "requested_end": end.isoformat(),
                                "chunk_end": chunk_end.isoformat(),
                            },
                        )
                    )
                    self.logger.info(
                        "historical_backfill_chunk_completed",
                        symbol=symbol,
                        timeframe=timeframe,
                        chunk_start=chunk_start.isoformat(),
                        chunk_end=chunk_end.isoformat(),
                        seen=len(payloads),
                        issues=len(issues),
                    )
                    chunk_start = chunk_end
                run_repo.finish(run, status="success", records_seen=total_seen, records_written=total_written)
                return JobResult(
                    job_type="historical_backfill",
                    symbol=symbol,
                    timeframe=timeframe,
                    started_at=started_at,
                    finished_at=datetime.now(tz=UTC),
                    status="success",
                    records_seen=total_seen,
                    records_written=total_written,
                    metadata={"start": start.isoformat(), "end": end.isoformat()},
                )
            except Exception as exc:
                checkpoint_repo.upsert(
                    CheckpointRecord(
                        job_type="historical_backfill",
                        symbol=symbol,
                        timeframe=timeframe,
                        last_synced_at=datetime.now(tz=UTC),
                        last_status="failed",
                        last_error=str(exc),
                        cursor={"requested_start": start.isoformat(), "requested_end": end.isoformat()},
                    )
                )
                run_repo.finish(
                    run,
                    status="failed",
                    records_seen=total_seen,
                    records_written=total_written,
                    errors=[str(exc)],
                )
                raise

    def incremental_sync(self, *, symbol: str, timeframe: str, num_bars: int | None = None) -> JobResult:
        started_at = datetime.now(tz=UTC)
        requested_bars = num_bars or self.settings.incremental_sync_num_bars
        total_seen = 0
        total_written = 0

        with MT5ApiClient(self.settings) as client, db_session() as session:
            client.ensure_healthy()
            run_repo = IngestionRunRepository(session)
            checkpoint_repo = CheckpointRepository(session)
            candle_repo = CandleRepository(session)
            quality_repo = QualityRepository(session)
            run = run_repo.start(
                job_type="incremental_sync",
                symbol=symbol,
                timeframe=timeframe,
                metadata={"num_bars": requested_bars},
            )
            try:
                payloads = client.fetch_data_pos(symbol=symbol, timeframe=timeframe, num_bars=requested_bars)
                records, issues = normalize_candles(symbol=symbol, timeframe=timeframe, payloads=payloads)
                total_seen = len(payloads)
                total_written = candle_repo.upsert_many(records)
                quality_repo.add_many(issues, run.id)
                checkpoint_repo.upsert(
                    CheckpointRecord(
                        job_type="incremental_sync",
                        symbol=symbol,
                        timeframe=timeframe,
                        last_synced_at=datetime.now(tz=UTC),
                        last_ingested_bar_at=records[-1].timestamp if records else None,
                        last_status="success",
                        cursor={"num_bars": requested_bars},
                    )
                )
                run_repo.finish(run, status="success", records_seen=total_seen, records_written=total_written)
                self.logger.info(
                    "incremental_sync_completed",
                    symbol=symbol,
                    timeframe=timeframe,
                    seen=total_seen,
                    written=total_written,
                    issues=len(issues),
                )
                return JobResult(
                    job_type="incremental_sync",
                    symbol=symbol,
                    timeframe=timeframe,
                    started_at=started_at,
                    finished_at=datetime.now(tz=UTC),
                    status="success",
                    records_seen=total_seen,
                    records_written=total_written,
                    metadata={"num_bars": requested_bars},
                )
            except Exception as exc:
                checkpoint_repo.upsert(
                    CheckpointRecord(
                        job_type="incremental_sync",
                        symbol=symbol,
                        timeframe=timeframe,
                        last_synced_at=datetime.now(tz=UTC),
                        last_status="failed",
                        last_error=str(exc),
                        cursor={"num_bars": requested_bars},
                    )
                )
                run_repo.finish(run, status="failed", records_seen=total_seen, records_written=total_written, errors=[str(exc)])
                raise

    def data_quality_audit(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> JobResult:
        started_at = datetime.now(tz=UTC)
        with db_session() as session:
            run_repo = IngestionRunRepository(session)
            checkpoint_repo = CheckpointRepository(session)
            candle_repo = CandleRepository(session)
            quality_repo = QualityRepository(session)
            run = run_repo.start(
                job_type="data_quality_audit",
                symbol=symbol,
                timeframe=timeframe,
                metadata={
                    "start": start.isoformat() if start else None,
                    "end": end.isoformat() if end else None,
                },
            )
            try:
                frame = candle_repo.to_frame(symbol=symbol, timeframe=timeframe, start=start, end=end)
                issues = audit_candles_frame(symbol=symbol, timeframe=timeframe, frame=frame)
                quality_repo.add_many(issues, run.id)
                checkpoint_repo.upsert(
                    CheckpointRecord(
                        job_type="data_quality_audit",
                        symbol=symbol,
                        timeframe=timeframe,
                        last_synced_at=datetime.now(tz=UTC),
                        last_ingested_bar_at=frame["timestamp"].max().to_pydatetime() if not frame.empty else None,
                        last_status="success",
                        cursor={"audited_rows": len(frame)},
                    )
                )
                run_repo.finish(run, status="success", records_seen=len(frame), records_written=len(issues))
                return JobResult(
                    job_type="data_quality_audit",
                    symbol=symbol,
                    timeframe=timeframe,
                    started_at=started_at,
                    finished_at=datetime.now(tz=UTC),
                    status="success",
                    records_seen=len(frame),
                    records_written=len(issues),
                    metadata={"issues_found": len(issues)},
                )
            except Exception as exc:
                checkpoint_repo.upsert(
                    CheckpointRecord(
                        job_type="data_quality_audit",
                        symbol=symbol,
                        timeframe=timeframe,
                        last_synced_at=datetime.now(tz=UTC),
                        last_status="failed",
                        last_error=str(exc),
                    )
                )
                run_repo.finish(run, status="failed", records_seen=0, records_written=0, errors=[str(exc)])
                raise

    def list_symbols(self) -> list[dict[str, Any]]:
        with db_session() as session:
            repo = SymbolRepository(session)
            return [
                {
                    "symbol": item.symbol,
                    "description": item.description,
                    "path": item.path,
                    "visible": item.visible,
                    "digits": item.digits,
                    "trade_mode": item.trade_mode,
                }
                for item in repo.list_symbols()
            ]

    def list_sync_status(self) -> list[dict[str, Any]]:
        with db_session() as session:
            repo = CheckpointRepository(session)
            return [
                {
                    "job_type": item.job_type,
                    "symbol": None if item.symbol == "__all__" else item.symbol,
                    "timeframe": None if item.timeframe == "__all__" else item.timeframe,
                    "last_synced_at": item.last_synced_at,
                    "last_ingested_bar_at": item.last_ingested_bar_at,
                    "last_status": item.last_status,
                    "last_error": item.last_error,
                    "cursor": item.cursor,
                }
                for item in repo.list_all()
            ]

    def latest_candles(self, *, symbol: str, timeframe: str, limit: int = 100) -> list[dict[str, Any]]:
        with db_session() as session:
            repo = CandleRepository(session)
            candles = repo.get_latest(symbol=symbol, timeframe=timeframe, limit=limit)
            return [
                {
                    "symbol": candle.symbol,
                    "timeframe": candle.timeframe,
                    "timestamp": candle.timestamp,
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "tick_volume": candle.tick_volume,
                    "real_volume": candle.real_volume,
                    "spread": candle.spread,
                    "quality_flags": candle.quality_flags,
                }
                for candle in candles
            ]

    def run_incremental_for_defaults(self) -> list[JobResult]:
        results: list[JobResult] = []
        for symbol in self.settings.default_symbols:
            for timeframe in self.settings.default_timeframes:
                results.append(self.incremental_sync(symbol=symbol, timeframe=timeframe))
        return results


def parse_optional_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return parse_api_datetime(value)
