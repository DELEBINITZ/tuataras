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


Cache = CacheManager()
