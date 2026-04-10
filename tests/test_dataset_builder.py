import numpy as np
import pandas as pd

from app.config.schema import DatasetConfig, FeatureConfig, SplitConfig, WalkForwardConfig
from app.datasets.builder import build_dataset_bundle


def _frame(rows: int = 220) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    close = 1.1 + np.cumsum(rng.normal(0.0, 0.0003, size=rows))
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) + 0.0004
    low = np.minimum(open_, close) - 0.0004
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=rows, freq="1min", tz="UTC"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.integers(100, 200, size=rows).astype(float),
            "symbol": ["EURUSD"] * rows,
            "timeframe": ["M1"] * rows,
        }
    )


def test_dataset_builder_generates_non_empty_splits():
    bundle = build_dataset_bundle(
        _frame(),
        feature_config=FeatureConfig(rolling_vol_window=5, atr_window=5, ema_window=5),
        dataset_config=DatasetConfig(window=20, horizon=10, stride=2, target_mode="future_close_return"),
        split_config=SplitConfig(train_ratio=0.7, validation_ratio=0.15, test_ratio=0.15, gap=2),
        walk_forward_config=WalkForwardConfig(enabled=True, train_windows=30, validation_windows=10, test_windows=10, step_windows=5, max_folds=3),
    )

    assert bundle.x_train.shape[0] > 0
    assert bundle.x_validation.shape[0] > 0
    assert bundle.x_test.shape[0] > 0
    assert bundle.x_train.shape[1] == 20
    assert bundle.y_train.shape[1] == 1
    assert bundle.dataset_metadata["num_samples"] == len(bundle.sample_metadata)
