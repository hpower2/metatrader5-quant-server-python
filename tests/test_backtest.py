from contextlib import contextmanager

import pandas as pd

from libs.backtest.engine import BacktestConfig, SignalBacktester
from libs.common.config import QuantSettings


def test_signal_backtester_runs_and_generates_metrics(monkeypatch, tmp_path):
    @contextmanager
    def fake_db_session():
        class DummySession:
            pass

        yield DummySession()

    class DummyArtifactRepository:
        def __init__(self, session):
            self.session = session

        def create_backtest_run(self, **kwargs):
            return kwargs

    monkeypatch.setattr("libs.backtest.engine.db_session", fake_db_session)
    monkeypatch.setattr("libs.backtest.engine.ArtifactRepository", DummyArtifactRepository)

    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=6, freq="1min", tz="UTC"),
            "open": [100, 101, 102, 103, 104, 105],
            "high": [101, 102, 103, 104, 105, 106],
            "low": [99, 100, 101, 102, 103, 104],
            "close": [100, 101, 102, 103, 104, 105],
            "signal": [0, 1, 1, 0, -1, 0],
        }
    )

    settings = QuantSettings(backtest_output_dir=tmp_path)
    result = SignalBacktester(settings).run(frame, BacktestConfig(strategy_name="unit_test_strategy"))

    assert "final_equity" in result.metrics
    assert result.artifact_dir.exists()
