from __future__ import annotations

import json
import time

import typer

from apps.worker.services import WorkerService, parse_optional_datetime
from libs.common.config import get_settings
from libs.common.logging import configure_logging

app = typer.Typer(help="Quant pipeline worker commands.")


def print_result(result: object) -> None:
    typer.echo(json.dumps(result, default=str, indent=2))


@app.callback()
def bootstrap() -> None:
    settings = get_settings()
    configure_logging(settings)


@app.command("bootstrap-symbols")
def bootstrap_symbols(visible_only: bool = typer.Option(True), search: str | None = typer.Option(None)) -> None:
    result = WorkerService().bootstrap_symbols(visible_only=visible_only, search=search)
    print_result(result.model_dump(mode="json"))


@app.command("historical-backfill")
def historical_backfill(
    symbol: str = typer.Option(...),
    timeframe: str = typer.Option(...),
    start: str = typer.Option(...),
    end: str = typer.Option(...),
) -> None:
    result = WorkerService().historical_backfill(
        symbol=symbol,
        timeframe=timeframe,
        start=parse_optional_datetime(start),
        end=parse_optional_datetime(end),
    )
    print_result(result.model_dump(mode="json"))


@app.command("incremental-sync")
def incremental_sync(
    symbol: str = typer.Option(...),
    timeframe: str = typer.Option(...),
    num_bars: int = typer.Option(500),
) -> None:
    result = WorkerService().incremental_sync(symbol=symbol, timeframe=timeframe, num_bars=num_bars)
    print_result(result.model_dump(mode="json"))


@app.command("data-quality-audit")
def data_quality_audit(
    symbol: str = typer.Option(...),
    timeframe: str = typer.Option(...),
    start: str | None = typer.Option(None),
    end: str | None = typer.Option(None),
) -> None:
    result = WorkerService().data_quality_audit(
        symbol=symbol,
        timeframe=timeframe,
        start=parse_optional_datetime(start),
        end=parse_optional_datetime(end),
    )
    print_result(result.model_dump(mode="json"))


@app.command("sync-status")
def sync_status() -> None:
    print_result(WorkerService().list_sync_status())


@app.command("scheduler")
def scheduler() -> None:
    settings = get_settings()
    service = WorkerService(settings)
    if settings.worker_bootstrap_on_start:
        print_result(service.bootstrap_symbols().model_dump(mode="json"))
    while True:
        if settings.default_symbols:
            results = service.run_incremental_for_defaults()
            print_result([result.model_dump(mode="json") for result in results])
        time.sleep(settings.worker_sync_interval_seconds)


if __name__ == "__main__":
    app()
