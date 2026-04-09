from datetime import UTC, datetime

import httpx

from libs.common.config import QuantSettings
from libs.mt5_adapter.client import MT5ApiClient


def test_mt5_client_sends_authorization_header_and_parses_candles():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(
            200,
            json=[
                {
                    "time": "2024-01-01T00:00:00+00:00",
                    "open": 1.1,
                    "high": 1.2,
                    "low": 1.0,
                    "close": 1.15,
                    "tick_volume": 10,
                    "spread": 2,
                    "real_volume": 10,
                }
            ],
        )

    settings = QuantSettings(mt5_api_base_url="https://example.test", mt5_api_auth_header="Bearer test-token")
    client = MT5ApiClient(settings)
    client._client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://example.test")

    candles = client.fetch_data_pos(symbol="EURUSD", timeframe="M1", num_bars=1)

    assert candles[0].time == datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
    assert candles[0].close == 1.15

