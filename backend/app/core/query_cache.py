# app/core/query_cache.py
"""
In-memory LRU cache for the last N query responses.
Completely self-contained — no changes to existing modules needed.

Redis upgrade path: swap _store with a Redis client that implements
the same get/set/keys interface.
"""
from collections import OrderedDict
from threading import Lock
from typing import Any, Dict, Optional
from backend.app.core.config import QUERY_CACHE_SIZE


class QueryCache:
    def __init__(self, maxsize: int = QUERY_CACHE_SIZE):
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._maxsize = maxsize
        self._lock = Lock()

    @staticmethod
    def _normalize(query: str) -> str:
        """Lowercase + strip so 'Show Alerts' and 'show alerts' hit same key."""
        return query.strip().lower()

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        key = self._normalize(query)
        with self._lock:
            if key not in self._store:
                return None
            # Move to end (most recently used)
            self._store.move_to_end(key)
            return self._store[key]

    def set(self, query: str, value: Dict[str, Any]) -> None:
        key = self._normalize(query)
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = value
            if len(self._store) > self._maxsize:
                self._store.popitem(last=False)   # evict oldest

    def all_keys(self):
        with self._lock:
            return list(self._store.keys())

    def clear(self):
        with self._lock:
            self._store.clear()


# Singleton — imported by query.py and dashboards.py
query_cache = QueryCache()