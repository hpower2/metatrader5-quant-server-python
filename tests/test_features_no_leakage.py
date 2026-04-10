import numpy as np
import pandas as pd

from app.config.schema import FeatureConfig
from app.features.engineering import build_features


def _frame(rows: int = 80) -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-01", periods=rows, freq="1min", tz="UTC")
    close = 1.2 + np.linspace(0, 0.01, rows)
    open_ = close - 0.0002
    high = close + 0.0005
    low = close - 0.0005
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.full(rows, 100.0),
            "symbol": ["EURUSD"] * rows,
            "timeframe": ["M1"] * rows,
        }
    )


def test_features_do_not_use_future_rows():
    base = _frame()
    modified = base.copy()
    modified.loc[60, "close"] = modified.loc[60, "close"] * 10.0

    cfg = FeatureConfig(rolling_vol_window=5, atr_window=5, ema_window=5, include_ema_distance=True)
    base_feat = build_features(base, cfg)
    mod_feat = build_features(modified, cfg)

    cutoff = 59
    columns = [
        "log_return",
        "candle_body",
        "upper_wick",
        "lower_wick",
        "range",
        "rolling_volatility",
        "atr_like",
        "ema_distance",
    ]
    for column in columns:
        left = base_feat.loc[:cutoff, column].to_numpy()
        right = mod_feat.loc[:cutoff, column].to_numpy()
        np.testing.assert_allclose(left, right, equal_nan=True)
