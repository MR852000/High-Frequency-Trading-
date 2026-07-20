from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import cache, schemas
from app.config import settings
from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health", response_model=schemas.HealthOut)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Used by Docker healthchecks, k8s liveness/readiness probes, and CI."""
    db_ok = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_ok = "unreachable"

    cache_ok = "ok" if await cache.ping() else "unreachable"

    return schemas.HealthOut(
        status="ok" if db_ok == "ok" else "degraded",
        environment=settings.ENVIRONMENT,
        database=db_ok,
        cache=cache_ok,
    )
