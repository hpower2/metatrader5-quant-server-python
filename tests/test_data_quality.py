import pandas as pd

from app.data.quality import dataset_quality_report


def test_quality_detects_malformed_ohlc():
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=5, freq="1min", tz="UTC"),
            "open": [1, 1, 1, 1, 1],
            "high": [1.1, 1.1, 0.8, 1.1, 1.1],
            "low": [0.9, 0.9, 1.2, 0.9, 0.9],
            "close": [1, 1, 1, 1, 1],
            "volume": [100, 100, 100, 100, 100],
            "symbol": ["EURUSD"] * 5,
            "timeframe": ["M1"] * 5,
        }
    )
    report = dataset_quality_report(frame)
    assert report["malformed_ohlc_rows"] > 0
