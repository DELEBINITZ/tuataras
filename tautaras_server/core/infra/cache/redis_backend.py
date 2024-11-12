from core.infra.cache.base.backend import BaseBackend
from typing import Any
import redis.asyncio as aioredis
import ujson
import pickle

from core.config.env_config import sttgs

redis = aioredis.from_url(url=sttgs.get("REDIS_HOST"))
class RedisBackend(BaseBackend):
    async def get(self, key: str) -> Any:
        result = await redis.get(key)
        if not result:
            return None
        try:
            return ujson.loads(result.decode("utf8"))
        except UnicodeDecodeError:
            return pickle.loads(result)

    async def set(self, key: str, response: Any, ttl: int = 60) -> None:
        if isinstance(response, dict):
            response = ujson.dumps(response)
        elif isinstance(response, object):
            response = pickle.dumps(response)
        await redis.set(name=key, value=response, ex=ttl)

    async def delete_startswith(self, prefix: str) -> None:
        async for key in redis.scan_iter(f"{prefix}::*"):
            await redis.delete(key)
