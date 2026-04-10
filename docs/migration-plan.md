# Migration Plan: Backend-First CLI Refactor

## Audit Summary

Current repository state is mixed and over-scoped for the objective:

- Strongly useful concepts:
  - time-series feature ideas
  - basic label generation patterns
  - backtest metric concepts
  - Typer-based command style
- Misaligned for target architecture:
  - Next.js frontend (`apps/web`)
  - Django legacy backend (`backend/django`)
  - MT5 service runtime/docker coupling (`backend/mt5`, `infra`, `monitoring`, `traefik`)
  - DB-first architecture where local file-first research is preferred
  - duplicated orchestration paths (`apps/api` and `apps/worker`)
- Data availability finding:
  - No local market datasets (`.csv` / `.parquet`) currently present in repository.
  - This means training-data sufficiency is currently unknown for real runs and should be reported as insufficient until a dataset is supplied.

## Keep / Delete Decisions

Keep only what directly supports CLI trading research:

- Keep:
  - Python packaging entrypoint and tests folder pattern
  - selected ideas rewritten into new clean modules
- Delete:
  - `apps/` legacy API/worker/web
  - `backend/`
  - `libs/` old modules
  - `infra/`, `migrations/`, `monitoring/`, `traefik/`
  - old architecture docs and old README content
  - non-essential compose/ops artifacts

## Target Architecture

The repository will be restructured to:

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

## Required Delivery Order

1. Audit (done).
2. Remove non-essential modules and frontend.
3. Implement data validation/inspection/sufficiency CLI first.
4. Implement feature + dataset + target generation pipeline.
5. Implement baseline models (MLP/CNN/GRU).
6. Implement train/evaluate/backtest/predict workflows.
7. Add tests for leakage, splitting, targets, metrics, CLI smoke, sufficiency.
8. Update README with terminal-first usage.

## Data Sufficiency Policy

Sufficiency output must explicitly report:

- total rows
- symbol/timeframe coverage
- date range
- missing/duplicate timestamps
- NaN counts
- usable windows for `(window=500, horizon=60)`
- split-adjusted usable windows
- verdict: `insufficient`, `marginal`, or `sufficient`
- warning when deep sequence models are likely underpowered by sample count

If no dataset is supplied or discovered, CLI must return an honest insufficiency warning.
