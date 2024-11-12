from abc import ABC, abstractmethod
from typing import Any

class BaseBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any:
        """Retrieve a value by key."""
        pass

    @abstractmethod
    async def set(self, key: str, response: Any, ttl: int = 60) -> None:
        """Store a value with the given key and time-to-live (TTL)."""
        pass

    @abstractmethod
    async def delete_startswith(self, prefix: str) -> None:
        """Delete all keys that start with the given prefix."""
        pass
