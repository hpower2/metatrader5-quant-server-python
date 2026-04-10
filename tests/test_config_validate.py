from pathlib import Path

from typer.testing import CliRunner

from app.cli.main import app


def test_config_validate_command(tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
data:
  input_path: data/example.csv
dataset:
  window: 500
  horizon: 60
  target_mode: future_close_return
model:
  name: mlp
""".strip(),
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(app, ["config", "validate", "--config", str(config_path)])
    assert result.exit_code == 0
    assert '"valid": true' in result.stdout.lower()
