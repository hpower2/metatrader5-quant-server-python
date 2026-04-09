from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import Select, desc, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from libs.storage.models import (
    BacktestRun,
    Candle,
    DataQualityIssue,
    DatasetManifest,
    IngestionRun,
    PaperAccount,
    PaperFill,
    PaperPosition,
    SymbolCatalog,
    SyncCheckpoint,
)
from libs.storage.schemas import CanonicalCandleRecord, CheckpointRecord, QualityIssueRecord, SymbolCatalogRecord


class SymbolRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_many(self, records: Iterable[SymbolCatalogRecord]) -> int:
        payload = [record.model_dump() for record in records]
        if not payload:
            return 0
        stmt = insert(SymbolCatalog).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=[SymbolCatalog.symbol],
            set_={
                "description": stmt.excluded.description,
                "path": stmt.excluded.path,
                "visible": stmt.excluded.visible,
                "digits": stmt.excluded.digits,
                "trade_mode": stmt.excluded.trade_mode,
                "points": stmt.excluded.points,
                "price_digits": stmt.excluded.price_digits,
                "spread": stmt.excluded.spread,
                "volume_max": stmt.excluded.volume_max,
                "volume_min": stmt.excluded.volume_min,
                "volume_step": stmt.excluded.volume_step,
                "source_metadata": stmt.excluded.source_metadata,
                "source_updated_at": stmt.excluded.source_updated_at,
                "last_seen_at": stmt.excluded.last_seen_at,
                "updated_at": datetime.now(tz=UTC),
            },
        )
        self.session.execute(stmt)
        return len(payload)

    def list_symbols(self) -> list[SymbolCatalog]:
        return list(self.session.scalars(select(SymbolCatalog).order_by(SymbolCatalog.symbol)))


class CandleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_many(self, records: Iterable[CanonicalCandleRecord]) -> int:
        payload = [record.model_dump() for record in records]
        if not payload:
            return 0
        stmt = insert(Candle).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Candle.symbol, Candle.timeframe, Candle.timestamp],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "tick_volume": stmt.excluded.tick_volume,
                "real_volume": stmt.excluded.real_volume,
                "spread": stmt.excluded.spread,
                "source": stmt.excluded.source,
                "ingestion_time": stmt.excluded.ingestion_time,
                "raw_hash": stmt.excluded.raw_hash,
                "raw_payload": stmt.excluded.raw_payload,
                "quality_flags": stmt.excluded.quality_flags,
            },
        )
        self.session.execute(stmt)
        return len(payload)

    def latest_timestamp(self, symbol: str, timeframe: str) -> datetime | None:
        stmt = (
            select(Candle.timestamp)
            .where(Candle.symbol == symbol, Candle.timeframe == timeframe)
            .order_by(desc(Candle.timestamp))
            .limit(1)
        )
        return self.session.scalar(stmt)

    def get_candles(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> list[Candle]:
        stmt: Select[Any] = select(Candle).where(Candle.symbol == symbol, Candle.timeframe == timeframe)
        if start is not None:
            stmt = stmt.where(Candle.timestamp >= start)
        if end is not None:
            stmt = stmt.where(Candle.timestamp <= end)
        stmt = stmt.order_by(Candle.timestamp)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt))

    def get_latest(self, *, symbol: str, timeframe: str, limit: int = 100) -> list[Candle]:
        stmt = (
            select(Candle)
            .where(Candle.symbol == symbol, Candle.timeframe == timeframe)
            .order_by(desc(Candle.timestamp))
            .limit(limit)
        )
        rows = list(self.session.scalars(stmt))
        return list(reversed(rows))

    def to_frame(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        if limit is not None and start is None and end is None:
            rows = self.get_latest(symbol=symbol, timeframe=timeframe, limit=limit)
        else:
            rows = self.get_candles(symbol=symbol, timeframe=timeframe, start=start, end=end)
            if limit is not None:
                rows = rows[-limit:]
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(
            [
                {
                    "symbol": row.symbol,
                    "timeframe": row.timeframe,
                    "timestamp": row.timestamp,
                    "open": row.open,
                    "high": row.high,
                    "low": row.low,
                    "close": row.close,
                    "tick_volume": row.tick_volume,
                    "real_volume": row.real_volume,
                    "spread": row.spread,
                }
                for row in rows
            ]
        )


class CheckpointRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _scope(value: str | None) -> str:
        return value or "__all__"

    def get(self, job_type: str, symbol: str | None, timeframe: str | None) -> SyncCheckpoint | None:
        stmt = select(SyncCheckpoint).where(
            SyncCheckpoint.job_type == job_type,
            SyncCheckpoint.symbol == self._scope(symbol),
            SyncCheckpoint.timeframe == self._scope(timeframe),
        )
        return self.session.scalar(stmt)

    def upsert(self, record: CheckpointRecord) -> SyncCheckpoint:
        payload = record.model_dump()
        payload["symbol"] = self._scope(payload.get("symbol"))
        payload["timeframe"] = self._scope(payload.get("timeframe"))
        stmt = insert(SyncCheckpoint).values(payload)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_sync_checkpoints_scope",
            set_={
                "last_synced_at": stmt.excluded.last_synced_at,
                "last_ingested_bar_at": stmt.excluded.last_ingested_bar_at,
                "cursor": stmt.excluded.cursor,
                "last_status": stmt.excluded.last_status,
                "last_error": stmt.excluded.last_error,
                "updated_at": datetime.now(tz=UTC),
            },
        ).returning(SyncCheckpoint)
        return self.session.execute(stmt).scalar_one()

    def list_all(self) -> list[SyncCheckpoint]:
        return list(
            self.session.scalars(
                select(SyncCheckpoint).order_by(SyncCheckpoint.job_type, SyncCheckpoint.symbol, SyncCheckpoint.timeframe)
            )
        )


class IngestionRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def start(self, *, job_type: str, symbol: str | None, timeframe: str | None, metadata: dict[str, Any]) -> IngestionRun:
        run = IngestionRun(job_type=job_type, symbol=symbol, timeframe=timeframe, run_metadata=metadata)
        self.session.add(run)
        self.session.flush()
        return run

    def finish(
        self,
        run: IngestionRun,
        *,
        status: str,
        records_seen: int,
        records_written: int,
        errors: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IngestionRun:
        run.status = status
        run.finished_at = datetime.now(tz=UTC)
        run.records_seen = records_seen
        run.records_written = records_written
        if errors is not None:
            run.errors = errors
        if metadata is not None:
            run.run_metadata = metadata
        self.session.add(run)
        self.session.flush()
        return run


class QualityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_many(self, issues: Iterable[QualityIssueRecord], run_id: str | None = None) -> int:
        payload = [DataQualityIssue(run_id=run_id, **issue.model_dump()) for issue in issues]
        self.session.add_all(payload)
        return len(payload)

    def recent(self, limit: int = 100) -> list[DataQualityIssue]:
        stmt = select(DataQualityIssue).order_by(desc(DataQualityIssue.detected_at)).limit(limit)
        return list(self.session.scalars(stmt))


class ArtifactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_dataset_manifest(
        self,
        *,
        name: str,
        config: dict[str, Any],
        artifact_path: Path,
        train_rows: int,
        validation_rows: int,
        test_rows: int,
    ) -> DatasetManifest:
        manifest = DatasetManifest(
            name=name,
            config=config,
            artifact_path=str(artifact_path),
            train_rows=train_rows,
            validation_rows=validation_rows,
            test_rows=test_rows,
        )
        self.session.add(manifest)
        self.session.flush()
        return manifest

    def create_backtest_run(
        self,
        *,
        strategy_name: str,
        config: dict[str, Any],
        metrics: dict[str, Any],
        artifact_path: str | None = None,
    ) -> BacktestRun:
        run = BacktestRun(
            strategy_name=strategy_name,
            config=config,
            metrics=metrics,
            artifact_path=artifact_path,
        )
        self.session.add(run)
        self.session.flush()
        return run


class PaperTradeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_account(self, *, name: str, currency: str, initial_cash: float) -> PaperAccount:
        stmt = select(PaperAccount).where(PaperAccount.name == name)
        account = self.session.scalar(stmt)
        if account is not None:
            return account
        account = PaperAccount(name=name, currency=currency, cash=initial_cash, equity=initial_cash)
        self.session.add(account)
        self.session.flush()
        return account

    def list_open_positions(self, account_id: str) -> list[PaperPosition]:
        stmt = select(PaperPosition).where(PaperPosition.account_id == account_id, PaperPosition.status == "open")
        return list(self.session.scalars(stmt))

    def add_fill(self, fill: PaperFill) -> PaperFill:
        self.session.add(fill)
        self.session.flush()
        return fill
