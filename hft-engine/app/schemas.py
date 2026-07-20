"""
Pydantic (v2) schemas — the request/response contracts for the API.
Kept separate from the ORM models so the DB layer can evolve independently
of what's exposed over the wire.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SignalReadingCreate(BaseModel):
    signal_key: str = Field(..., examples=["obi"])
    channel_code: str = Field(..., examples=["IN"])
    order_throughput: int
    latency_ms: float
    load_percentage: int


class SignalReadingOut(SignalReadingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recorded_at: datetime


class BacktestRunCreate(BaseModel):
    strategy_name: str = Field(..., examples=["mean_reversion_v1"])


class BacktestRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    strategy_name: str
    status: str
    sharpe_ratio: float | None = None
    max_drawdown: float | None = None
    total_return_pct: float | None = None
    created_at: datetime
    completed_at: datetime | None = None


class HealthOut(BaseModel):
    status: str
    environment: str
    database: str
    cache: str
