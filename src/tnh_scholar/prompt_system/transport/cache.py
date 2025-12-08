"""Cache transport abstractions."""

from typing import Generic, Protocol, TypeVar

T = TypeVar("T")


class CacheTransport(Protocol, Generic[T]):
    """Abstract cache transport."""

    def get(self, key: str) -> T | None:
        ...

    def set(self, key: str, value: T, ttl_s: int | None = None) -> None:
        ...

    def invalidate(self, key: str) -> None:
        ...

    def clear(self) -> None:
        ...


class InMemoryCacheTransport(Generic[T]):
    """In-memory cache implementation with TTL."""

    def __init__(self, default_ttl_s: int = 300):
        self._cache: dict[str, tuple[T, float]] = {}
        self._default_ttl = default_ttl_s

    def get(self, key: str) -> T | None:
        import time

        if key not in self._cache:
            return None
        value, expires_at = self._cache[key]
        if time.time() > expires_at:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: T, ttl_s: int | None = None) -> None:
        import time

        ttl = ttl_s if ttl_s is not None else self._default_ttl
        expires_at = time.time() + ttl
        self._cache[key] = (value, expires_at)

    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()

