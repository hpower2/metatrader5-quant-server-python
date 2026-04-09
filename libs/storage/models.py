from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.storage.base import Base


def utcnow() -> datetime:
    return datetime.now(tz=UTC)


class SymbolCatalog(Base):
    __tablename__ = "symbol_catalog"

    symbol: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    path: Mapped[str | None] = mapped_column(Text, nullable=True)
    visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    digits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trade_mode: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_digits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spread: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_step: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    source_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Candle(Base):
    __tablename__ = "candles"

    symbol: Mapped[str] = mapped_column(String(64), ForeignKey("symbol_catalog.symbol"), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(16), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    tick_volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    real_volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    spread: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="mt5_api", nullable=False)
    ingestion_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    raw_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    quality_flags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    symbol_ref: Mapped[SymbolCatalog] = relationship(SymbolCatalog)


class SyncCheckpoint(Base):
    __tablename__ = "sync_checkpoints"
    __table_args__ = (UniqueConstraint("job_type", "symbol", "timeframe", name="uq_sync_checkpoints_scope"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False, default="__all__")
    timeframe: Mapped[str] = mapped_column(String(16), nullable=False, default="__all__")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_ingested_bar_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cursor: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    last_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timeframe: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    records_seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_written: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    run_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)


class DataQualityIssue(Base):
    __tablename__ = "data_quality_issues"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("ingestion_runs.id"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(16), nullable=False)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="warning")
    details: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class DatasetManifest(Base):
    __tablename__ = "dataset_manifests"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    artifact_path: Mapped[str] = mapped_column(Text, nullable=False)
    train_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    validation_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    test_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    strategy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class PaperAccount(Base):
    __tablename__ = "paper_accounts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(16), default="USD", nullable=False)
    cash: Mapped[float] = mapped_column(Numeric(20, 8), default=0, nullable=False)
    equity: Mapped[float] = mapped_column(Numeric(20, 8), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    last_mark_to_market_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class PaperPosition(Base):
    __tablename__ = "paper_positions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    account_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("paper_accounts.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)


class PaperFill(Base):
    __tablename__ = "paper_fills"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    account_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("paper_accounts.id"), nullable=False)
    position_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("paper_positions.id"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    fees: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    slippage_bps: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    fill_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
