# MT5 Quant Research And Paper-Trading Platform

This repository now includes a production-oriented quant pipeline around the existing MetaTrader 5 HTTP API. The upstream MT5 service remains the provider of market data and symbol metadata; a new internal FastAPI service, worker, and TimescaleDB-backed warehouse handle ingestion, data quality, research datasets, backtesting, and paper execution.

The implementation uses the real contract published at `https://api-mt5.irvine.web.id/apispec_1.json`, specifically:

- `GET /fetch_data_range`
- `GET /fetch_data_pos`
- `GET /symbols/forex`
- `GET /symbol_info/{symbol}`
- `GET /symbol_info_tick/{symbol}`
- `GET /health`

## What’s Included

- MT5 HTTP adapter with typed models, timeout, retries, and `Authorization` header support
- Symbol bootstrap and metadata cache
- PostgreSQL + TimescaleDB candle warehouse
- Historical backfill and incremental sync jobs
- Data quality auditing for gaps, duplicates, out-of-order bars, and malformed OHLC
- Reusable feature engineering and label generation modules
- Dataset builder with parquet export and walk-forward slice generation
- Signal-driven backtesting foundation
- Paper-trading scaffold with simulated fills and persisted state
- FastAPI control plane
- Next.js operations and research dashboard
- Alembic migrations
- Docker Compose integration
- Pytest coverage for critical logic

## Architecture

The quant layer is organized as:

- `apps/api`
- `apps/worker`
- `libs/common`
- `libs/mt5_adapter`
- `libs/storage`
- `libs/features`
- `libs/labels`
- `libs/datasets`
- `libs/backtest`
- `libs/papertrade`
- `migrations`
- `infra/docker`

The frontend lives at:

- `apps/web`

Detailed design, assumptions, API ambiguities, schema notes, and workflow behavior live in [docs/architecture.md](/home/irvine/metatrader5-quant-server-python/docs/architecture.md).
Frontend-specific architecture notes live in [docs/frontend-architecture.md](/home/irvine/metatrader5-quant-server-python/docs/frontend-architecture.md).

## Quick Start

1. Create the environment file.

```bash
cp .env.example .env
```

2. Set the MT5 auth header exactly as expected by the upstream service.

```env
MT5_API_AUTH_HEADER=Bearer your-token-or-api-key
```

3. Point persistent compose storage at your shared mount.

```env
SHARED_VOLUME_ROOT=/mnt/shared/mt5
```

4. Start the stack.

```bash
docker compose up -d --build
```

5. The quant control plane will run Alembic migrations automatically on startup and expose endpoints through the `quant-api` service.
6. The frontend dashboard is exposed through the `web` service and routed by Traefik via `WEB_DOMAIN`.

## Internal Control API

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

## Frontend Routes

- `/dashboard`
- `/market-data`
- `/features-explorer`
- `/datasets`
- `/backtests`
- `/paper-trading`
- `/admin`

## Worker Commands

The worker service exposes the same core workflows through a CLI:

```bash
python -m apps.worker.main bootstrap-symbols
python -m apps.worker.main historical-backfill --symbol EURUSD --timeframe M1 --start 2024-01-01T00:00:00Z --end 2024-01-31T00:00:00Z
python -m apps.worker.main incremental-sync --symbol EURUSD --timeframe M5 --num-bars 500
python -m apps.worker.main data-quality-audit --symbol EURUSD --timeframe M15
```

## Notes On Correctness

- Candle timestamps are normalized to UTC.
- Candle continuity is never assumed; gaps are audited explicitly.
- OHLC consistency is validated before persistence.
- Raw payloads and hashes are preserved.
- Features use current/past rows only.
- Labels use future rows only.
- Paper execution is simulated locally; live order endpoints are not part of the primary execution path.
