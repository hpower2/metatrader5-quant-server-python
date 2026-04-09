import pandas as pd

from libs.features.engineering import FeatureConfig, compute_features


def test_compute_features_builds_expected_columns():
    frame = pd.DataFrame(
        {
            "symbol": ["EURUSD"] * 30,
            "timeframe": ["M1"] * 30,
            "timestamp": pd.date_range("2024-01-01", periods=30, freq="1min", tz="UTC"),
            "open": [1.0 + idx * 0.01 for idx in range(30)],
            "high": [1.01 + idx * 0.01 for idx in range(30)],
            "low": [0.99 + idx * 0.01 for idx in range(30)],
            "close": [1.0 + idx * 0.01 for idx in range(30)],
            "tick_volume": [100] * 30,
            "real_volume": [100] * 30,
            "spread": [2] * 30,
        }
    )

    features = compute_features(frame, FeatureConfig(windows=[5, 14]))

    assert "simple_return" in features.columns
    assert "log_return" in features.columns
    assert "atr_w5" in features.columns
    assert "rsi_w14" in features.columns
    assert features["rolling_mean_close_w5"].notna().sum() > 0

