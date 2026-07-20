"""
Thin async Redis wrapper, used for the live order-book snapshot cache and
as a lightweight pub/sub bus for pushing tick updates to the dashboard.
"""
import json
from typing import Any

import redis.asyncio as redis

from app.config import settings

_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=_pool)


async def cache_set(key: str, value: Any, ttl_seconds: int = 30) -> None:
    client = get_redis()
    await client.set(key, json.dumps(value), ex=ttl_seconds)


async def cache_get(key: str) -> Any | None:
    client = get_redis()
    raw = await client.get(key)
    return json.loads(raw) if raw is not None else None


async def ping() -> bool:
    try:
        client = get_redis()
        return await client.ping()
    except Exception:
        return False
