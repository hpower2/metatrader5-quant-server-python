from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from app.cli.main import app


def _write_sample_csv(path: Path) -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=800, freq="1min", tz="UTC"),
            "open": [1.0] * 800,
            "high": [1.01] * 800,
            "low": [0.99] * 800,
            "close": [1.0] * 800,
            "volume": [100.0] * 800,
        }
    )
    frame.to_csv(path, index=False)


def test_cli_data_validate_smoke(tmp_path: Path):
    input_path = tmp_path / "sample.csv"
    _write_sample_csv(input_path)
    runner = CliRunner()
    result = runner.invoke(app, ["data", "validate", "--input", str(input_path), "--default-symbol", "EURUSD", "--default-timeframe", "M1"])
    assert result.exit_code == 0
    assert '"total_rows": 800' in result.stdout


def test_cli_data_sufficiency_smoke(tmp_path: Path):
    input_path = tmp_path / "sample.csv"
    _write_sample_csv(input_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "data",
            "sufficiency",
            "--input",
            str(input_path),
            "--window",
            "500",
            "--horizon",
            "60",
            "--default-symbol",
            "EURUSD",
            "--default-timeframe",
            "M1",
        ],
    )
    assert result.exit_code == 0
    assert '"sufficiency"' in result.stdout
