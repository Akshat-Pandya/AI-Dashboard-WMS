# app/core/query_cache.py
"""
In-memory LRU cache for the last N query responses.
Completely self-contained — no changes to existing modules needed.

TTL (time-to-live): cache entries expire after CACHE_TTL_SECONDS.
This ensures the auto-refresh polling in the frontend always gets
fresh DB data after the TTL window, not stale cached results.

Redis upgrade path: swap _store with a Redis client that implements
the same get/set/keys interface.
"""
import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Dict, Optional, Tuple

CACHE_SIZE        = 15
CACHE_TTL_SECONDS = 9   # expire just under the 10s frontend refresh interval


class QueryCache:
    def __init__(self, maxsize: int = CACHE_SIZE, ttl: int = CACHE_TTL_SECONDS):
        # Store: key → (value, timestamp)
        self._store:   OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._maxsize  = maxsize
        self._ttl      = ttl
        self._lock     = Lock()

    @staticmethod
    def _normalize(query: str) -> str:
        """Lowercase + strip so 'Show Alerts' and 'show alerts' hit same key."""
        return query.strip().lower()

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        key = self._normalize(query)
        with self._lock:
            if key not in self._store:
                return None
            value, ts = self._store[key]
            # Expired — remove and treat as cache miss
            if time.monotonic() - ts > self._ttl:
                del self._store[key]
                print(f"⏱ Cache expired: {key!r}")
                return None
            # Move to end (most recently used)
            self._store.move_to_end(key)
            return value

    def set(self, query: str, value: Dict[str, Any]) -> None:
        key = self._normalize(query)
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (value, time.monotonic())
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