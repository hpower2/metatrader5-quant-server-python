import pandas as pd

from app.config.schema import DatasetConfig
from app.datasets.targets import build_target


def _future_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [101, 102, 103],
            "high": [102, 104, 105],
            "low": [99, 100, 102],
            "close": [102, 103, 104],
        }
    )


def test_future_close_return_target():
    target, aux = build_target(_future_frame(), 100.0, DatasetConfig(target_mode="future_close_return", horizon=3))
    assert round(float(target[0]), 6) == 0.04
    assert round(aux["future_return"], 6) == 0.04


def test_direction_target():
    cfg = DatasetConfig(target_mode="direction_over_horizon", horizon=3, direction_threshold=0.01)
    target, _ = build_target(_future_frame(), 100.0, cfg)
    assert int(target[0]) == 1


def test_tp_before_sl_target():
    future = pd.DataFrame(
        {
            "open": [100.2, 100.1, 99.8],
            "high": [100.4, 100.8, 101.1],
            "low": [99.8, 99.7, 99.6],
            "close": [100.1, 100.6, 101.0],
        }
    )
    cfg = DatasetConfig(target_mode="tp_before_sl", horizon=3, tp_pct=0.01, sl_pct=0.01)
    target, aux = build_target(future, 100.0, cfg)
    assert int(target[0]) == 1
    assert int(aux["tp_before_sl"]) == 1


def test_mfe_mae_target():
    cfg = DatasetConfig(target_mode="mfe_mae", horizon=3)
    target, aux = build_target(_future_frame(), 100.0, cfg)
    assert round(float(target[0]), 6) == round(aux["mfe"], 6)
    assert round(float(target[1]), 6) == round(aux["mae"], 6)
