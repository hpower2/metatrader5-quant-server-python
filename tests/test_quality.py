from datetime import UTC, datetime

from libs.mt5_adapter.models import CandlePayload
from libs.storage.quality import normalize_candles


def test_normalize_candles_detects_duplicates_gaps_and_malformed_prices():
    payloads = [
        CandlePayload(
            time=datetime(2024, 1, 1, 0, 1, tzinfo=UTC),
            open=1.2,
            high=1.25,
            low=1.19,
            close=1.24,
            tick_volume=10,
            spread=2,
            real_volume=10,
        ),
        CandlePayload(
            time=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            open=1.1,
            high=1.15,
            low=1.09,
            close=1.12,
            tick_volume=10,
            spread=2,
            real_volume=10,
        ),
        CandlePayload(
            time=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            open=1.1,
            high=1.15,
            low=1.09,
            close=1.12,
            tick_volume=11,
            spread=2,
            real_volume=11,
        ),
        CandlePayload(
            time=datetime(2024, 1, 1, 0, 3, tzinfo=UTC),
            open=1.3,
            high=1.29,
            low=1.31,
            close=1.28,
            tick_volume=10,
            spread=2,
            real_volume=10,
        ),
    ]

    records, issues = normalize_candles(symbol="EURUSD", timeframe="M1", payloads=payloads)

    assert len(records) == 3
    issue_types = {issue.issue_type for issue in issues}
    assert "duplicate_bar" in issue_types
    assert "out_of_order_timestamp" in issue_types
    assert "missing_bars" in issue_types
    assert "malformed_ohlc" in issue_types

