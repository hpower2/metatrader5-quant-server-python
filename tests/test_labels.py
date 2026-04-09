import pandas as pd

from libs.labels.engine import LabelConfig, create_labels


def test_labels_use_future_horizon_only():
    frame = pd.DataFrame(
        {
            "symbol": ["EURUSD"] * 5,
            "timeframe": ["M1"] * 5,
            "timestamp": pd.date_range("2024-01-01", periods=5, freq="1min", tz="UTC"),
            "open": [1, 2, 3, 4, 5],
            "high": [1, 2, 3, 4, 5],
            "low": [1, 2, 3, 4, 5],
            "close": [1, 2, 3, 4, 5],
            "spread": [1, 1, 1, 1, 1],
        }
    )

    labelled = create_labels(frame, LabelConfig(horizon_bars=2, return_threshold=0.5))

    assert round(labelled.loc[0, "next_return_2"], 6) == 2.0
    assert labelled.loc[0, "direction_label_2"] == 1
    assert pd.isna(labelled.loc[4, "next_return_2"])

