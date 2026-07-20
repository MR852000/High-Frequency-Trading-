"""
Database access functions. Kept plain (no ORM leakage into routers) so
routes stay thin and testable.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas


async def create_signal_reading(
    db: AsyncSession, payload: schemas.SignalReadingCreate
) -> models.SignalReading:
    row = models.SignalReading(**payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_signal_readings(
    db: AsyncSession,
    channel_code: str | None = None,
    signal_key: str | None = None,
    limit: int = 50,
) -> list[models.SignalReading]:
    stmt = select(models.SignalReading).order_by(
        models.SignalReading.recorded_at.desc()
    )
    if channel_code:
        stmt = stmt.where(models.SignalReading.channel_code == channel_code)
    if signal_key:
        stmt = stmt.where(models.SignalReading.signal_key == signal_key)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_backtest_run(
    db: AsyncSession, payload: schemas.BacktestRunCreate
) -> models.BacktestRun:
    row = models.BacktestRun(strategy_name=payload.strategy_name, status="pending")
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_backtest_run(
    db: AsyncSession, run_id: uuid.UUID
) -> models.BacktestRun | None:
    return await db.get(models.BacktestRun, run_id)


async def list_backtest_runs(
    db: AsyncSession, limit: int = 50
) -> list[models.BacktestRun]:
    stmt = (
        select(models.BacktestRun)
        .order_by(models.BacktestRun.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
