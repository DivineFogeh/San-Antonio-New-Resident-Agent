# app/cache.py — Redis session and checklist cache
import redis.asyncio as aioredis
from app.config import settings

redis_client: aioredis.Redis | None = None

async def init_redis():
    global redis_client
    redis_client = await aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )

async def get_redis():
    return redis_client

async def cache_set(key: str, value: str, ttl: int = 3600):
    await redis_client.setex(key, ttl, value)

async def cache_get(key: str):
    return await redis_client.get(key)

async def cache_delete(key: str):
    await redis_client.delete(key)
