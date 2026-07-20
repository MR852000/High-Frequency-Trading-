import os

# Must be set before `app.config` (and anything importing it) is loaded,
# so tests never touch a real Postgres/Redis instance.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app import models  # noqa: F401 — registers ORM tables on Base.metadata
from app.database import Base, engine


@pytest_asyncio.fixture(autouse=True)
async def _prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # aiosqlite connections are bound to the event loop that created them;
    # pytest-asyncio spins up a fresh loop per test, so the pool must be
    # disposed here or the next test's queries hang/fail against a dead loop.
    await engine.dispose()


@pytest_asyncio.fixture
async def client():
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
