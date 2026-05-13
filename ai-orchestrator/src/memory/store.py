import json
import structlog
from typing import Any
from redis.asyncio import Redis

logger = structlog.get_logger()


class MemoryStore:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis: Redis | None = None

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            self._redis = await Redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def store(self, pipeline_id: str, stage: str, data: dict) -> None:
        redis = await self._get_redis()
        key = f"pipeline:{pipeline_id}:{stage}"
        await redis.set(key, json.dumps(data, default=str))
        await redis.expire(key, 86400)
        logger.debug("memory_stored", key=key)

    async def retrieve(self, pipeline_id: str, stage: str) -> dict | None:
        redis = await self._get_redis()
        key = f"pipeline:{pipeline_id}:{stage}"
        data = await redis.get(key)
        return json.loads(data) if data else None

    async def clear_pipeline(self, pipeline_id: str) -> None:
        redis = await self._get_redis()
        async for key in redis.scan_iter(match=f"pipeline:{pipeline_id}:*"):
            await redis.delete(key)
        logger.info("pipeline_memory_cleared", pipeline_id=pipeline_id)
