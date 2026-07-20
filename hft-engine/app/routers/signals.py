from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


@router.post("", response_model=schemas.SignalReadingOut, status_code=201)
async def record_signal(
    payload: schemas.SignalReadingCreate, db: AsyncSession = Depends(get_db)
):
    """Persist a single HFT signal reading (order throughput, latency,
    gateway load) for a feed channel. The ReactPy dashboard calls this
    every tick so history survives restarts and can be replayed."""
    return await crud.create_signal_reading(db, payload)


@router.get("", response_model=list[schemas.SignalReadingOut])
async def get_signals(
    channel_code: str | None = Query(default=None, examples=["IN"]),
    signal_key: str | None = Query(default=None, examples=["obi"]),
    limit: int = Query(default=50, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await crud.list_signal_readings(db, channel_code, signal_key, limit)
