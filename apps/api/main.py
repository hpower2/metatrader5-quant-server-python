from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
import pandas as pd
from sqlalchemy import text

from apps.api.schemas import BacktestRunRequest, DatasetRunRequest, FeatureRunRequest, PaperSignalRequest, SyncRunRequest
from apps.worker.services import WorkerService, parse_optional_datetime
from libs.backtest.engine import SignalBacktester
from libs.common.config import get_settings
from libs.common.logging import configure_logging
from libs.datasets.builder import DatasetBuilder
from libs.features.engineering import FeatureConfig, compute_features, join_multi_timeframe_features
from libs.mt5_adapter import MT5ApiClient
from libs.papertrade.engine import PaperExecutionProvider
from libs.storage.db import db_session, get_engine
from libs.storage.repositories import CandleRepository

settings = get_settings()
configure_logging(settings)
logger = logging.getLogger(__name__)

app = FastAPI(title="MT5 Quant Control Plane", version="0.1.0")
worker_service = WorkerService(settings)
dataset_builder = DatasetBuilder(settings)
backtester = SignalBacktester(settings)
paper_provider = PaperExecutionProvider(settings)


def _load_backtest_frame_from_dataset(dataset_name: str, split: str) -> pd.DataFrame:
    if split not in {"train", "validation", "test"}:
        raise HTTPException(status_code=400, detail="dataset_split must be one of: train, validation, test")

    dataset_dir = settings.dataset_output_dir / dataset_name
    split_path = dataset_dir / f"{split}.parquet"
    if not split_path.exists():
        raise HTTPException(status_code=400, detail=f"Dataset split artifact not found: {split_path}")

    frame = pd.read_parquet(split_path)
    if frame.empty:
        raise HTTPException(status_code=400, detail=f"Dataset split '{split}' is empty for dataset '{dataset_name}'")

    required_columns = {"symbol", "timeframe", "timestamp", "open", "high", "low", "close", "spread"}
    missing = required_columns.difference(frame.columns)
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise HTTPException(
            status_code=400,
            detail=f"Dataset split '{split}' is missing required columns for backtesting: {missing_columns}",
        )

    return frame


@app.get("/health")
def health() -> dict:
    db_ok = False
    db_error: str | None = None
    mt5_health: dict | None = None
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
            db_ok = True
    except Exception as exc:
        db_error = str(exc)
    try:
        with MT5ApiClient(settings) as client:
            mt5_health = client.get_health().model_dump(mode="json")
    except Exception as exc:
        mt5_health = {"status": "unhealthy", "error": str(exc)}
    return {
        "status": "ok" if db_ok else "degraded",
        "database": {"ok": db_ok, "error": db_error},
        "mt5": mt5_health,
    }


@app.get("/sync/status")
def sync_status() -> list[dict]:
    return worker_service.list_sync_status()


@app.post("/sync/run")
def sync_run(request: SyncRunRequest) -> dict:
    try:
        if request.job_type == "bootstrap_symbols":
            return worker_service.bootstrap_symbols(
                visible_only=request.visible_only,
                search=request.search,
            ).model_dump(mode="json")
        if request.job_type == "historical_backfill":
            if not all([request.symbol, request.timeframe, request.start, request.end]):
                raise HTTPException(status_code=400, detail="symbol, timeframe, start, and end are required")
            return worker_service.historical_backfill(
                symbol=request.symbol,
                timeframe=request.timeframe,
                start=parse_optional_datetime(request.start),
                end=parse_optional_datetime(request.end),
            ).model_dump(mode="json")
        if request.job_type == "incremental_sync":
            if not all([request.symbol, request.timeframe]):
                raise HTTPException(status_code=400, detail="symbol and timeframe are required")
            return worker_service.incremental_sync(
                symbol=request.symbol,
                timeframe=request.timeframe,
                num_bars=request.num_bars,
            ).model_dump(mode="json")
        if request.job_type == "data_quality_audit":
            if not all([request.symbol, request.timeframe]):
                raise HTTPException(status_code=400, detail="symbol and timeframe are required")
            return worker_service.data_quality_audit(
                symbol=request.symbol,
                timeframe=request.timeframe,
                start=parse_optional_datetime(request.start),
                end=parse_optional_datetime(request.end),
            ).model_dump(mode="json")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise HTTPException(status_code=400, detail=f"Unsupported job type: {request.job_type}")


@app.get("/symbols")
def symbols() -> list[dict]:
    return worker_service.list_symbols()


@app.get("/candles/latest")
def candles_latest(symbol: str = Query(...), timeframe: str = Query(...), limit: int = Query(100, ge=1, le=5000)) -> list[dict]:
    return worker_service.latest_candles(symbol=symbol, timeframe=timeframe, limit=limit)


@app.post("/features/run")
def features_run(request: FeatureRunRequest) -> dict:
    try:
        with db_session() as session:
            repo = CandleRepository(session)
            base_frame = repo.to_frame(symbol=request.symbol, timeframe=request.timeframe)
            feature_frame = compute_features(base_frame, request.feature_config)
            if request.higher_timeframe:
                higher_frame = repo.to_frame(symbol=request.symbol, timeframe=request.higher_timeframe)
                higher_features = compute_features(higher_frame, request.feature_config)
                feature_frame = join_multi_timeframe_features(
                    feature_frame,
                    higher_features,
                    request.higher_timeframe.lower(),
                )
        artifact_dir = Path("artifacts/features")
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_dir / f"{request.symbol}_{request.timeframe}.parquet"
        feature_frame.to_parquet(artifact_path, index=False)
        return {
            "rows": len(feature_frame),
            "columns": list(feature_frame.columns),
            "artifact_path": str(artifact_path),
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("features_run failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/datasets/build")
def datasets_build(request: DatasetRunRequest) -> dict:
    try:
        artifacts = dataset_builder.build(request)
        return {
            "artifact_dir": str(artifacts.artifact_dir),
            "dataset_rows": len(artifacts.dataset),
            "train_rows": len(artifacts.train),
            "validation_rows": len(artifacts.validation),
            "test_rows": len(artifacts.test),
            "walk_forward_slices": artifacts.walk_forward_slices,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("datasets_build failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/backtests/run")
def backtests_run(request: BacktestRunRequest) -> dict:
    if request.fast_window >= request.slow_window:
        raise HTTPException(status_code=400, detail="fast_window must be smaller than slow_window")

    try:
        data_source = {"mode": "warehouse", "dataset_name": None, "dataset_split": None}
        if request.dataset_name:
            frame = _load_backtest_frame_from_dataset(request.dataset_name, request.dataset_split)
            data_source = {"mode": "dataset", "dataset_name": request.dataset_name, "dataset_split": request.dataset_split}
        else:
            with db_session() as session:
                repo = CandleRepository(session)
                frame = repo.to_frame(symbol=request.symbol, timeframe=request.timeframe)

        if frame.empty:
            raise HTTPException(status_code=400, detail="No candle data found for the requested symbol/timeframe")

        feature_windows = sorted({*FeatureConfig().windows, request.fast_window, request.slow_window})
        feature_frame = compute_features(frame, FeatureConfig(windows=feature_windows))
        fast_column = f"rolling_mean_close_w{request.fast_window}"
        slow_column = f"rolling_mean_close_w{request.slow_window}"

        signal_frame = feature_frame.copy()
        signal_frame["signal"] = 0
        signal_frame.loc[signal_frame[fast_column] > signal_frame[slow_column], "signal"] = 1
        signal_frame.loc[signal_frame[fast_column] < signal_frame[slow_column], "signal"] = -1

        prepared = signal_frame.dropna(subset=[fast_column, slow_column])
        if prepared.empty:
            raise HTTPException(
                status_code=400,
                detail="Not enough historical candles to evaluate the selected fast/slow windows",
            )

        artifacts = backtester.run(prepared, request.config)
        return {
            "artifact_dir": str(artifacts.artifact_dir),
            "config": request.config.model_dump(mode="json"),
            "data_source": data_source,
            "metrics": artifacts.metrics,
            "trade_count": len(artifacts.trades),
            "equity_rows": len(artifacts.equity_curve),
            "equity_curve": artifacts.equity_curve.to_dict(orient="records"),
            "trades": artifacts.trades.to_dict(orient="records"),
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("backtests_run failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/paper/status")
def paper_status(account_name: str = Query("default")) -> dict:
    return paper_provider.get_status(account_name)


@app.post("/paper/signal")
def paper_signal(request: PaperSignalRequest) -> dict:
    return paper_provider.submit_signal(request)
