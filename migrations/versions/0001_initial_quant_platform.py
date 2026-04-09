"""Initial quant platform schema."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_quant_platform"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.create_table(
        "symbol_catalog",
        sa.Column("symbol", sa.String(length=64), primary_key=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("path", sa.Text(), nullable=True),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("digits", sa.Integer(), nullable=True),
        sa.Column("trade_mode", sa.Integer(), nullable=True),
        sa.Column("points", sa.Integer(), nullable=True),
        sa.Column("price_digits", sa.Integer(), nullable=True),
        sa.Column("spread", sa.Float(), nullable=True),
        sa.Column("volume_max", sa.Float(), nullable=True),
        sa.Column("volume_min", sa.Float(), nullable=True),
        sa.Column("volume_step", sa.Float(), nullable=True),
        sa.Column("source_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "candles",
        sa.Column("symbol", sa.String(length=64), sa.ForeignKey("symbol_catalog.symbol"), nullable=False),
        sa.Column("timeframe", sa.String(length=16), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("tick_volume", sa.BigInteger(), nullable=False),
        sa.Column("real_volume", sa.BigInteger(), nullable=False),
        sa.Column("spread", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="mt5_api"),
        sa.Column("ingestion_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("quality_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.PrimaryKeyConstraint("symbol", "timeframe", "timestamp", name="pk_candles"),
    )
    op.create_index("ix_candles_symbol_timeframe_timestamp", "candles", ["symbol", "timeframe", "timestamp"], unique=False)
    op.create_index("ix_candles_timestamp", "candles", ["timestamp"], unique=False)
    op.execute("SELECT create_hypertable('candles', 'timestamp', if_not_exists => TRUE)")

    op.create_table(
        "sync_checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False, server_default="__all__"),
        sa.Column("timeframe", sa.String(length=16), nullable=False, server_default="__all__"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_ingested_bar_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cursor", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("last_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("job_type", "symbol", "timeframe", name="uq_sync_checkpoints_scope"),
    )

    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=True),
        sa.Column("timeframe", sa.String(length=16), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_seen", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_written", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.create_table(
        "data_quality_issues",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("ingestion_runs.id"), nullable=True),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("timeframe", sa.String(length=16), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issue_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_data_quality_symbol_timeframe", "data_quality_issues", ["symbol", "timeframe"], unique=False)
    op.create_index("ix_data_quality_detected_at", "data_quality_issues", ["detected_at"], unique=False)

    op.create_table(
        "dataset_manifests",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("artifact_path", sa.Text(), nullable=False),
        sa.Column("train_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("validation_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("test_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "backtest_runs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("strategy_name", sa.String(length=128), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("artifact_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "paper_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("currency", sa.String(length=16), nullable=False, server_default="USD"),
        sa.Column("cash", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("equity", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("last_mark_to_market_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "paper_positions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("paper_accounts.id"), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("current_price", sa.Float(), nullable=False),
        sa.Column("stop_loss", sa.Float(), nullable=True),
        sa.Column("take_profit", sa.Float(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("realized_pnl", sa.Float(), nullable=False, server_default="0"),
        sa.Column("unrealized_pnl", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
    )

    op.create_table(
        "paper_fills",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("paper_accounts.id"), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("paper_positions.id"), nullable=True),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("fees", sa.Float(), nullable=False, server_default="0"),
        sa.Column("slippage_bps", sa.Float(), nullable=False, server_default="0"),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )


def downgrade() -> None:
    op.drop_table("paper_fills")
    op.drop_table("paper_positions")
    op.drop_table("paper_accounts")
    op.drop_table("backtest_runs")
    op.drop_table("dataset_manifests")
    op.drop_index("ix_data_quality_detected_at", table_name="data_quality_issues")
    op.drop_index("ix_data_quality_symbol_timeframe", table_name="data_quality_issues")
    op.drop_table("data_quality_issues")
    op.drop_table("ingestion_runs")
    op.drop_table("sync_checkpoints")
    op.drop_index("ix_candles_timestamp", table_name="candles")
    op.drop_index("ix_candles_symbol_timeframe_timestamp", table_name="candles")
    op.drop_table("candles")
    op.drop_table("symbol_catalog")
