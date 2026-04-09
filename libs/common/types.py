from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PlatformModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class JobResult(PlatformModel):
    job_type: str
    symbol: str | None = None
    timeframe: str | None = None
    started_at: datetime
    finished_at: datetime
    status: str
    records_seen: int = 0
    records_written: int = 0
    metadata: dict[str, Any] = {}
    errors: list[str] = []

