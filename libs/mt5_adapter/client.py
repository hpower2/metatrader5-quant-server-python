from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from libs.common.config import QuantSettings
from libs.common.time import ensure_utc
from libs.mt5_adapter.exceptions import MT5RequestError, MT5ResponseError, MT5UnavailableError
from libs.mt5_adapter.models import (
    CandlePayload,
    MT5HealthPayload,
    SymbolInfoPayload,
    SymbolListPayload,
    SymbolTickPayload,
)


class MT5ApiClient:
    def __init__(self, settings: QuantSettings) -> None:
        self._settings = settings
        headers: dict[str, str] = {}
        if settings.mt5_api_auth_header:
            headers["Authorization"] = settings.mt5_api_auth_header

        self._client = httpx.Client(
            base_url=settings.mt5_api_base_url.rstrip("/"),
            headers=headers,
            timeout=httpx.Timeout(settings.mt5_api_timeout_seconds),
            verify=settings.mt5_api_verify_tls,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "MT5ApiClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, MT5RequestError)),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._client.request(method, path, **kwargs)
        if response.status_code >= 500:
            raise MT5RequestError(f"MT5 server error {response.status_code}: {response.text}")
        if response.status_code >= 400:
            raise MT5RequestError(f"MT5 request failed {response.status_code}: {response.text}")
        try:
            return response.json()
        except ValueError as exc:
            raise MT5ResponseError(f"Invalid JSON response from MT5: {response.text}") from exc

    def get_health(self) -> MT5HealthPayload:
        payload = self._request("GET", "/health")
        return MT5HealthPayload.model_validate(payload)

    def ensure_healthy(self) -> MT5HealthPayload:
        payload = self.get_health()
        if not payload.mt5_initialized or not payload.mt5_connected:
            raise MT5UnavailableError(
                f"MT5 unavailable: initialized={payload.mt5_initialized} connected={payload.mt5_connected}"
            )
        return payload

    def list_forex_symbols(
        self,
        *,
        visible_only: bool = False,
        search: str | None = None,
    ) -> SymbolListPayload:
        params: dict[str, Any] = {"visible_only": str(visible_only).lower()}
        if search:
            params["search"] = search
        payload = self._request("GET", "/symbols/forex", params=params)
        return SymbolListPayload.model_validate(payload)

    def get_symbol_info(self, symbol: str) -> SymbolInfoPayload:
        payload = self._request("GET", f"/symbol_info/{symbol}")
        return SymbolInfoPayload.model_validate(payload)

    def get_symbol_tick(self, symbol: str) -> SymbolTickPayload:
        payload = self._request("GET", f"/symbol_info_tick/{symbol}")
        return SymbolTickPayload.model_validate(payload)

    def fetch_data_range(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> list[CandlePayload]:
        start_param = ensure_utc(start).strftime("%Y-%m-%dT%H-%M-%S")
        end_param = ensure_utc(end).strftime("%Y-%m-%dT%H-%M-%S")
        payload = self._request(
            "GET",
            "/fetch_data_range",
            params={
                "symbol": symbol,
                "timeframe": timeframe,
                "start": start_param,
                "end": end_param,
            },
        )
        return [CandlePayload.model_validate(item) for item in payload]

    def fetch_data_pos(
        self,
        *,
        symbol: str,
        timeframe: str,
        num_bars: int,
    ) -> list[CandlePayload]:
        payload = self._request(
            "GET",
            "/fetch_data_pos",
            params={"symbol": symbol, "timeframe": timeframe, "num_bars": num_bars},
        )
        return [CandlePayload.model_validate(item) for item in payload]
