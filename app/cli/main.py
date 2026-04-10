from __future__ import annotations

import json
from pathlib import Path

import typer

from app.config.io import load_run_config
from app.config.schema import DataConfig, DatasetConfig, FeatureConfig, SplitConfig, WalkForwardConfig
from app.data.loading import load_ohlcv
from app.data.quality import dataset_quality_report
from app.data.sufficiency import data_sufficiency_report
from app.datasets.builder import build_dataset_bundle, save_dataset_bundle
from app.evaluation.core import evaluate_run, evaluate_walk_forward
from app.evaluation.predict import predict_latest
from app.features.engineering import build_features
from app.training.loop import train_from_config
from app.training.runs import list_runs, show_run
from app.backtest.simulator import run_backtest

app = typer.Typer(help="Backend-first CLI for trading research.")
data_app = typer.Typer(help="Data loading, validation, and sufficiency checks.")
features_app = typer.Typer(help="Feature engineering commands.")
dataset_app = typer.Typer(help="Dataset windowing and target generation.")
runs_app = typer.Typer(help="Run registry commands.")
config_app = typer.Typer(help="Config validation commands.")
app.add_typer(data_app, name="data")
app.add_typer(features_app, name="features")
app.add_typer(dataset_app, name="dataset")
app.add_typer(runs_app, name="runs")
app.add_typer(config_app, name="config")


def emit(payload: object) -> None:
    typer.echo(json.dumps(payload, indent=2, default=str))


def _data_config_from_input(input_path: Path, default_symbol: str, default_timeframe: str) -> DataConfig:
    return DataConfig(
        input_path=input_path,
        default_symbol=default_symbol,
        default_timeframe=default_timeframe,
    )


@data_app.command("validate")
def data_validate(
    input: Path = typer.Option(..., help="Input CSV/parquet dataset."),
    default_symbol: str = typer.Option("UNKNOWN"),
    default_timeframe: str = typer.Option("UNKNOWN"),
) -> None:
    config = _data_config_from_input(input, default_symbol, default_timeframe)
    frame = load_ohlcv(config)
    report = dataset_quality_report(frame)
    report["valid"] = len(report["warnings"]) == 0 and report["total_rows"] > 0
    emit(report)


@data_app.command("inspect")
def data_inspect(
    input: Path = typer.Option(..., help="Input CSV/parquet dataset."),
    default_symbol: str = typer.Option("UNKNOWN"),
    default_timeframe: str = typer.Option("UNKNOWN"),
) -> None:
    config = _data_config_from_input(input, default_symbol, default_timeframe)
    frame = load_ohlcv(config)
    quality = dataset_quality_report(frame)
    summary = {
        "shape": [int(frame.shape[0]), int(frame.shape[1])],
        "columns": list(frame.columns),
        "quality": quality,
    }
    emit(summary)


@data_app.command("sufficiency")
def data_sufficiency(
    input: Path = typer.Option(..., help="Input CSV/parquet dataset."),
    window: int = typer.Option(500, min=5),
    horizon: int = typer.Option(60, min=1),
    stride: int = typer.Option(1, min=1),
    train_ratio: float = typer.Option(0.7, min=0.01, max=0.98),
    validation_ratio: float = typer.Option(0.15, min=0.01, max=0.98),
    gap: int = typer.Option(60, min=0),
    wf_train_windows: int = typer.Option(3000, min=1),
    wf_validation_windows: int = typer.Option(1000, min=1),
    wf_test_windows: int = typer.Option(1000, min=1),
    wf_step_windows: int = typer.Option(500, min=1),
    default_symbol: str = typer.Option("UNKNOWN"),
    default_timeframe: str = typer.Option("UNKNOWN"),
) -> None:
    if train_ratio + validation_ratio >= 1.0:
        raise typer.BadParameter("train_ratio + validation_ratio must be < 1.0")
    config = _data_config_from_input(input, default_symbol, default_timeframe)
    frame = load_ohlcv(config)
    quality = dataset_quality_report(frame)
    sufficiency = data_sufficiency_report(
        frame,
        window=window,
        horizon=horizon,
        stride=stride,
        train_ratio=train_ratio,
        validation_ratio=validation_ratio,
        gap=gap,
        wf_train_windows=wf_train_windows,
        wf_validation_windows=wf_validation_windows,
        wf_test_windows=wf_test_windows,
        wf_step_windows=wf_step_windows,
    )
    emit({"quality": quality, "sufficiency": sufficiency})


@features_app.command("build")
def features_build(
    input: Path = typer.Option(...),
    output: Path = typer.Option(Path("artifacts/features.parquet")),
    default_symbol: str = typer.Option("UNKNOWN"),
    default_timeframe: str = typer.Option("UNKNOWN"),
    rolling_vol_window: int = typer.Option(20, min=2),
    atr_window: int = typer.Option(14, min=2),
    ema_window: int = typer.Option(20, min=2),
    include_ema_distance: bool = typer.Option(True),
) -> None:
    data_cfg = _data_config_from_input(input, default_symbol, default_timeframe)
    feat_cfg = FeatureConfig(
        rolling_vol_window=rolling_vol_window,
        atr_window=atr_window,
        ema_window=ema_window,
        include_ema_distance=include_ema_distance,
    )
    frame = load_ohlcv(data_cfg)
    featured = build_features(frame, feat_cfg)
    featured.to_parquet(output, index=False)
    emit(
        {
            "output_path": str(output),
            "rows": int(len(featured)),
            "columns": list(featured.columns),
        }
    )


@dataset_app.command("build")
def dataset_build(
    input: Path = typer.Option(...),
    output_dir: Path = typer.Option(Path("artifacts/dataset_bundle")),
    target_mode: str = typer.Option("future_close_return"),
    window: int = typer.Option(500, min=5),
    horizon: int = typer.Option(60, min=1),
    stride: int = typer.Option(1, min=1),
    default_symbol: str = typer.Option("UNKNOWN"),
    default_timeframe: str = typer.Option("UNKNOWN"),
) -> None:
    data_cfg = _data_config_from_input(input, default_symbol, default_timeframe)
    feature_cfg = FeatureConfig()
    dataset_cfg = DatasetConfig(
        window=window,
        horizon=horizon,
        stride=stride,
        target_mode=target_mode,  # type: ignore[arg-type]
    )
    split_cfg = SplitConfig()
    walk_cfg = WalkForwardConfig()

    frame = load_ohlcv(data_cfg)
    bundle = build_dataset_bundle(
        frame,
        feature_config=feature_cfg,
        dataset_config=dataset_cfg,
        split_config=split_cfg,
        walk_forward_config=walk_cfg,
    )
    save_dataset_bundle(bundle, output_dir)
    emit(
        {
            "output_dir": str(output_dir),
            "metadata": bundle.dataset_metadata,
        }
    )


@config_app.command("validate")
def config_validate(config: Path = typer.Option(...)) -> None:
    parsed = load_run_config(config)
    emit(
        {
            "valid": True,
            "target_mode": parsed.dataset.target_mode,
            "model": parsed.model.name,
            "window": parsed.dataset.window,
            "horizon": parsed.dataset.horizon,
            "input_path": str(parsed.data.input_path),
        }
    )


@app.command("train")
def train(config: Path = typer.Option(..., help="YAML run config.")) -> None:
    parsed = load_run_config(config)
    result = train_from_config(parsed)
    emit(
        {
            "run_id": result.run_id,
            "run_path": str(result.run_path),
            "best_epoch": result.best_epoch,
            "best_validation_loss": result.best_validation_loss,
            "epochs_ran": len(result.history),
        }
    )


@app.command("evaluate")
def evaluate(
    run_id: str = typer.Option(...),
    split: str = typer.Option("test"),
    walk_forward: bool = typer.Option(False, help="Compute fold metrics across walk-forward test slices."),
) -> None:
    if walk_forward:
        emit(evaluate_walk_forward(run_id))
        return
    emit(evaluate_run(run_id, split=split))  # type: ignore[arg-type]


@app.command("backtest")
def backtest(run_id: str = typer.Option(...), split: str = typer.Option("test")) -> None:
    emit(run_backtest(run_id, split=split))


@app.command("predict")
def predict(run_id: str = typer.Option(...), input: Path | None = typer.Option(None)) -> None:
    emit(predict_latest(run_id, input_path=input))


@runs_app.command("list")
def runs_list() -> None:
    emit({"runs": list_runs()})


@runs_app.command("show")
def runs_show(run_id: str = typer.Option(...)) -> None:
    emit(show_run(run_id))
