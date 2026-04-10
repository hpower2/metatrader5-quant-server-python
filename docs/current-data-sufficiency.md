# Current Data Sufficiency Status

Audit date: 2026-04-10

## Finding

No local market dataset files (`.csv` or `.parquet`) were found in this repository during audit.

## Implication for Planned Setup (`window=500`, `horizon=60`)

Without an input dataset, the system cannot compute:

- usable training windows
- split-adjusted windows
- walk-forward fold count
- target-label coverage (`future_close_return`, `direction_over_horizon`, `tp_before_sl`, `mfe_mae`)

Therefore, current effective sufficiency status is:

- `insufficient`

## Operational Guidance

Use:

```bash
python -m app data sufficiency --input <your_dataset.csv> --window 500 --horizon 60 --default-symbol EURUSD --default-timeframe M1
```

to generate the real sufficiency report once a dataset is provided.
