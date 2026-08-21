"""
In-memory cache for common aggregate queries.

Usage:
    cache = QueryCache()
    result = cache.get("monthly_mean_30N_80E")
    if result is None:
        result = expensive_query()
        cache.set("monthly_mean_30N_80E", result, ttl=3600)
"""

import time
from typing import Any, Optional


class QueryCache:
    """Simple TTL-aware in-memory cache keyed by query strings."""

    def __init__(self, default_ttl: int = 3600):
        self._store: dict[str, tuple[Any, float]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else self.default_ttl
        self._store[key] = (value, time.time() + ttl)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


# Module-level singleton shared across request handlers
query_cache = QueryCache(default_ttl=3600)
