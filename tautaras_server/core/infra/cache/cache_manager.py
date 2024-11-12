import pickle
from typing import Any, Type, Callable
import redis.asyncio as aioredis
import ujson
from core.infra.cache.base.backend import BaseBackend
from functools import wraps


class CacheManager:
    def __init__(self):
        self.backend = None

    def init(self, backend: Type[BaseBackend]) -> None:
        self.backend = backend

    def cached(self, key: str = None, ttl: int = 60):
        def _cached(function):
            @wraps(function)
            async def __cached(*args, **kwargs):
                if not self.backend:
                    raise ValueError("Backend not initialized")

                cache_key = key or self._generate_key(function, args, kwargs)

                cached_response = await self.backend.get(key=cache_key)
                if cached_response:
                    return cached_response

                response = await function(*args, **kwargs)
                await self.backend.set(key=cache_key, response=response, ttl=ttl)
                return response

            return __cached

        return _cached

    def _generate_key(self, function: Callable, args: tuple, kwargs: dict) -> str:
        key = f"{function.__module__}.{function.__name__}"
        if args:
            key += f"::{args}"
        if kwargs:
            key += f"::{kwargs}"
        return key


Cache = CacheManager()
