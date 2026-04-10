# Trading Research CLI (Backend-First)

This repository was refactored into a clean, CLI-first trading research system.

Note: Docker Compose keeps the MT5 stack with Traefik/MT5/backend/monitoring, and removes `quant-api`, `quant-worker`, and `web` flow services.

Core design goals:

- no frontend/UI dependency
- terminal-first operation
- reproducible config-driven runs
- leakage-safe time-series workflow
- honest data sufficiency diagnostics

## Repository Layout

- `app/cli/`
- `app/config/`
- `app/data/`
- `app/features/`
- `app/datasets/`
- `app/models/`
- `app/training/`
- `app/evaluation/`
- `app/backtest/`
- `app/utils/`
- `configs/`
- `runs/`
- `tests/`
- `docs/migration-plan.md`

## Install

```bash
python -m pip install -e .[dev]
```

## Shared Volume Convention

For containerized workflows, data and run artifacts are expected under:

- `/mnt/shared/mt5/data`
- `/mnt/shared/mt5/runs`

In containers, `APP_RUNS_ROOT` defaults to `/mnt/shared/mt5/runs`.

## Services Kept

Compose keeps the MT5 operational stack and monitoring/logging stack, including:

- `traefik`
- `mt5`
- `postgres`
- `django`
- `redis`
- `celery`
- `celery-beat`
- `grafana`
- `prometheus`
- `alertmanager`
- `loki`
- `promtail`
- `cadvisor`
- `node-exporter`
- `uncomplicated-alert-receiver`

Removed from compose:

- `quant-api`
- `quant-worker`
- `web`

## Data Requirements

Input supports CSV/parquet with required fields:

- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `volume` (or `tick_volume` / `real_volume`)

`symbol` and `timeframe` are optional; defaults can be provided by CLI flags.

## CLI Commands

### Data quality and sufficiency

```bash
python -m app data validate --input data/eurusd_1m.csv --default-symbol EURUSD --default-timeframe M1
python -m app data inspect --input data/eurusd_1m.csv --default-symbol EURUSD --default-timeframe M1
python -m app data sufficiency --input data/eurusd_1m.csv --window 500 --horizon 60 --default-symbol EURUSD --default-timeframe M1
```

`data sufficiency` reports:

- total rows, symbols, timeframes, date range
- missing timestamps, duplicates, NaNs
- usable windows for `window/horizon/stride`
- split-adjusted windows
- walk-forward fold count
- verdict: `insufficient`, `marginal`, `sufficient`
- warnings for deep-model sample risk and horizon ambition

### Feature and dataset build

```bash
python -m app features build --input data/eurusd_1m.csv --output artifacts/features.parquet --default-symbol EURUSD --default-timeframe M1
python -m app dataset build --input data/eurusd_1m.csv --output-dir artifacts/dataset_bundle --target-mode future_close_return --window 500 --horizon 60 --default-symbol EURUSD --default-timeframe M1
```

### Config workflow

```bash
python -m app config validate --config configs/close_return_cnn.yaml
python -m app train --config configs/close_return_cnn.yaml
python -m app evaluate --run-id <run_id>
python -m app evaluate --run-id <run_id> --walk-forward
python -m app backtest --run-id <run_id>
python -m app predict --run-id <run_id> --input data/latest.csv
```

### Run registry

```bash
python -m app runs list
python -m app runs show --run-id <run_id>
```

## Docker Workflow

### Docker Compose (mounted to `/mnt/shared/mt5`)

1. Optional env setup:

```bash
cp .env.example .env
```

2. Build and start:

```bash
make docker-build
make docker-up
make docker-ps
```

3. Run predefined commands inside container:

```bash
make docker-data-validate DATA_PATH=/mnt/shared/mt5/data/eurusd_1m.csv
make docker-data-sufficiency DATA_PATH=/mnt/shared/mt5/data/eurusd_1m.csv
make docker-train CONFIG_PATH=/workspace/configs/close_return_cnn.yaml
make docker-runs-list
make docker-evaluate RUN_ID=<run_id>
make docker-backtest RUN_ID=<run_id>
make docker-predict RUN_ID=<run_id> LATEST_PATH=/mnt/shared/mt5/data/latest.csv
```

4. Open shell:

```bash
make docker-shell
```

5. Follow MT5 logs if needed:

```bash
make docker-mt5-logs
```

## Target Modes

Supported dataset targets:

- `future_close_return`
- `future_close_path`
- `future_ohlc_path`
- `direction_over_horizon`
- `tp_before_sl`
- `mfe_mae`

MVP training focus:

- `future_close_return`
- `direction_over_horizon`
- `tp_before_sl`

## Models

- `mlp`
- `cnn1d`
- `gru`

## Leakage Controls

- strictly chronological split
- optional split gap between train/validation/test
- no random shuffling for split
- feature scaler fit on train only
- scaler reused unchanged on validation/test/predict

## Run Artifacts

Each run writes into `runs/<run_id>/`:

- `config.yaml`
- `run_manifest.json`
- `training_summary.json`
- `training_history.json`
- `dataset/` bundle (`dataset.npz`, `sample_metadata.parquet`, `metadata.json`, `scaler.pkl`)
- `checkpoints/best.pt`
- `evaluation/<split>/metrics.json`
- `evaluation/<split>/predictions.parquet`
- `backtest/<split>/metrics.json`

## Important Note On Sufficiency

If data is too short for `window=500` and `horizon=60`, CLI reports insufficiency explicitly.
This is intentional: weak data quality or weak sample count is never hidden by optimistic defaults.

