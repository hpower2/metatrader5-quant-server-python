import pandas as pd

from app.data.sufficiency import data_sufficiency_report


def test_sufficiency_flags_small_dataset_as_insufficient():
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=400, freq="1min", tz="UTC"),
            "open": [1.0] * 400,
            "high": [1.1] * 400,
            "low": [0.9] * 400,
            "close": [1.0] * 400,
            "volume": [100.0] * 400,
            "symbol": ["EURUSD"] * 400,
            "timeframe": ["M1"] * 400,
        }
    )
    report = data_sufficiency_report(
        frame,
        window=500,
        horizon=60,
        stride=1,
        train_ratio=0.7,
        validation_ratio=0.15,
        gap=60,
        wf_train_windows=3000,
        wf_validation_windows=1000,
        wf_test_windows=1000,
        wf_step_windows=500,
    )
    assert report["verdict"] == "insufficient"
    assert report["groups"][0]["usable_windows"] == 0
