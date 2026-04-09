# Quant Pipeline Architecture

## Overview

This repository now contains two layers:

1. The existing MT5 terminal/API service in `backend/mt5`, which exposes the real HTTP contract documented by `https://api-mt5.irvine.web.id/apispec_1.json`.
2. A new quant research and paper-trading platform that treats the MT5 service as a provider and builds a production-style ingestion, storage, research, backtesting, and paper-execution pipeline around it.

The quant layer is intentionally isolated so the upstream MT5 provider can be swapped later without rewriting the storage, feature, dataset, backtest, or paper-trading modules.

## Module Layout

- `apps/api`
  FastAPI control plane for sync, research, backtests, and paper-trading state.
- `apps/worker`
  CLI and scheduler entrypoints for symbol bootstrap, historical backfill, incremental sync, and quality audits.
- `libs/common`
  Shared settings, structured logging, time handling, and base model utilities.
- `libs/mt5_adapter`
  Typed client for the MT5 HTTP API with auth header handling, retries, timeout, and response validation.
- `libs/storage`
  SQLAlchemy models, repositories, canonical record schemas, validation, and quality audit helpers.
- `libs/features`
  Leakage-safe rolling feature engineering by symbol and timeframe.
- `libs/labels`
  Future-horizon labels, threshold labels, and optional barrier-style labels.
- `libs/datasets`
  Dataset assembly, walk-forward slicing, parquet export, and dataset manifest persistence.
- `libs/backtest`
  Signal-driven backtesting engine with transaction costs, equity curve, drawdown, expectancy, Sharpe, and Sortino metrics.
- `libs/papertrade`
  Execution abstraction and paper provider that simulates positions/fills without hitting live order endpoints.
- `migrations`
  Alembic migrations and TimescaleDB bootstrap.
- `infra/docker`
  Dockerfiles for the internal quant API and worker services.

## External API Assumptions

These assumptions are based on the live Swagger contract retrieved on April 9, 2026.

- Auth uses an `Authorization` header defined as Swagger `ApiKeyAuth`.
- `/fetch_data_range` and `/fetch_data_pos` return arrays of candles with:
  `time`, `open`, `high`, `low`, `close`, `tick_volume`, `spread`, `real_volume`.
- Candle `time` fields are documented as `date-time` strings.
- `/symbol_info_tick/{symbol}` returns `time` as an integer rather than a `date-time` string.
- `/symbols/forex` returns lightweight symbol summaries, while `/symbol_info/{symbol}` returns richer metadata.
- The contract documents trading endpoints, but the quant platform does not use them for primary execution paths. Paper execution is simulated locally.

## Contract Ambiguities And Risks

- The contract does not specify whether `Authorization` expects a raw token or `Bearer <token>`, so the platform treats the environment value as the full header payload.
- The contract does not specify maximum backfill range sizes for `/fetch_data_range`, so historical sync uses chunked requests.
- The MT5 health semantics are limited by the upstream implementation. The quant worker still checks health before jobs, but a "healthy" response may not prove deep terminal responsiveness.
- Spread units are not explicitly documented as points versus price units, so raw spread is preserved and derived features are named conservatively.
- The API does not guarantee continuous history, retroactive immutability, or gap-free candles, so ingestion validates ordering, OHLC consistency, duplicates, and missing bars explicitly.

## Canonical Candle Model

The warehouse candle schema is:

- `symbol`
- `timeframe`
- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `tick_volume`
- `real_volume`
- `spread`
- `source`
- `ingestion_time`
- `raw_hash`
- `raw_payload`
- `quality_flags`

Every candle is normalized to UTC, deduplicated on `(symbol, timeframe, timestamp)`, and written to a Timescale hypertable.

## Database Schema

### `symbol_catalog`

Cached symbol metadata enriched from `/symbols/forex` and `/symbol_info/{symbol}`.

### `candles`

Timescale hypertable for canonical OHLCV records with composite primary key:

- `symbol`
- `timeframe`
- `timestamp`

Indexes:

- `(symbol, timeframe, timestamp)`
- descending timestamp access path for recent reads

### `sync_checkpoints`

Restart-safe per-job scope checkpoints storing:

- last sync time
- last ingested bar time
- cursor metadata
- last status and error

### `ingestion_runs`

Job audit table for bootstrap/backfill/incremental/audit executions.

### `data_quality_issues`

Persisted validation findings:

- duplicates
- out-of-order bars
- missing bars
- malformed OHLC

### `dataset_manifests`

Dataset build metadata and artifact paths.

### `backtest_runs`

Backtest configuration, metrics, and artifact paths.

### `paper_accounts`, `paper_positions`, `paper_fills`

Paper-trading state, fills, and account snapshots.

## Ingestion Design

### Symbol Bootstrap

1. Call `/health`.
2. Call `/symbols/forex`.
3. Enrich each symbol with `/symbol_info/{symbol}`.
4. Upsert into `symbol_catalog`.
5. Update `sync_checkpoints`.

### Historical Backfill

1. Call `/health`.
2. Chunk the requested time range.
3. Call `/fetch_data_range` per chunk.
4. Normalize and validate candles.
5. Upsert candles and write quality issues.
6. Advance checkpoints after each chunk.

### Incremental Sync

1. Call `/health`.
2. Call `/fetch_data_pos` for a rolling recent window.
3. Normalize and validate.
4. Upsert idempotently into `candles`.
5. Update per-symbol/per-timeframe checkpoints.

### Data Quality Audit

1. Load persisted candles.
2. Re-scan for duplicates, malformed OHLC, and gaps.
3. Persist findings in `data_quality_issues`.

## Research Pipeline

### Features

- simple returns
- log returns
- rolling mean
- rolling standard deviation
- ATR
- RSI
- candle range
- candle body size
- upper/lower wick ratios
- momentum windows
- volatility windows
- spread-to-close ratio

All feature calculations are grouped by `symbol` and `timeframe` and use only current or past rows.

### Labels

- next-N-bars return
- directional label
- thresholded long/short/flat label
- optional barrier-style label

Labels use future rows only and are separated from feature generation to avoid leakage.

### Datasets

The dataset builder:

- joins candles, features, and labels
- drops incomplete rows
- creates train/validation/test splits
- creates walk-forward slice metadata
- exports parquet artifacts
- optionally writes the prepared dataset into a database table

## Backtesting

The backtest engine is signal-driven and includes:

- long/short/flat position states
- transaction cost hooks
- slippage modeling
- stop loss / take profit hooks
- risk-per-trade position sizing hook
- trade log
- equity curve
- drawdown
- expectancy
- Sharpe and Sortino metrics

The control API currently exposes a simple moving-average crossover example strategy on top of the framework.

## Paper Trading

The paper-trading layer:

- uses MT5 tick data for mark prices
- simulates opens/closes locally
- records fills and position state transitions
- maintains account cash/equity state
- never calls live trading endpoints as part of the primary workflow

This is intentionally designed behind an execution-provider abstraction so a live adapter can be added later.

## Internal API Surface

- `GET /health`
- `GET /sync/status`
- `POST /sync/run`
- `GET /symbols`
- `GET /candles/latest`
- `POST /features/run`
- `POST /datasets/build`
- `POST /backtests/run`
- `GET /paper/status`
- `POST /paper/signal`

## Operational Notes

- Run migrations before starting API/worker containers.
- Set `MT5_API_AUTH_HEADER` to the exact header value expected by the upstream MT5 service.
- Bootstrap symbols before large historical backfills.
- Keep default symbol/timeframe lists explicit in `.env` so the scheduler only syncs intended markets.
