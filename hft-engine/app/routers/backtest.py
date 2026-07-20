import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/v1/backtests", tags=["backtests"])


@router.post("", response_model=schemas.BacktestRunOut, status_code=201)
async def create_backtest(
    payload: schemas.BacktestRunCreate, db: AsyncSession = Depends(get_db)
):
    """Kick off a backtest run record. In production this would enqueue a
    Celery task; here it creates the tracking row so the API contract is
    already in place for that worker to fill in later."""
    return await crud.create_backtest_run(db, payload)


@router.get("", response_model=list[schemas.BacktestRunOut])
async def list_backtests(db: AsyncSession = Depends(get_db)):
    return await crud.list_backtest_runs(db)


@router.get("/{run_id}", response_model=schemas.BacktestRunOut)
async def get_backtest(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    run = await crud.get_backtest_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return run
