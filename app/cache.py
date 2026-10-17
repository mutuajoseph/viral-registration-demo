"""A tiny in-memory cache with a time-to-live (TTL).

Good for data many students read and that rarely changes (event details).
Never used to decide who gets a seat: cached data can be stale.
"""

import threading
import time
from typing import Any, Callable


class TTLCache:
    def __init__(self, ttl_seconds: float):
        self.ttl_seconds = ttl_seconds
        self._items: dict[Any, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get_or_load(self, key: Any, load: Callable[[], Any]) -> Any:
        now = time.monotonic()
        with self._lock:
            hit = self._items.get(key)
            if hit and hit[0] > now:
                return hit[1]
        value = load()  # cache miss: ask the database once
        with self._lock:
            self._items[key] = (now + self.ttl_seconds, value)
        return value

    def invalidate(self, key: Any) -> None:
        with self._lock:
            self._items.pop(key, None)
