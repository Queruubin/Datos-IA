"""Simple in-memory sliding-window rate limiter (one process; enough for the MVP demo)."""

import threading
import time
from collections import deque
from collections.abc import Callable


class RateLimiter:
    """Allows `limit` requests per `window_seconds` for each client key. Keys are kept only in
    memory and never logged."""

    def __init__(
        self,
        limit: int,
        window_seconds: float = 60,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = self._clock()
        with self._lock:
            self._prune(now)
            hits = self._hits.setdefault(key, deque())
            if len(hits) >= self._limit:
                return False
            hits.append(now)
            return True

    def _prune(self, now: float) -> None:
        for key in list(self._hits):
            hits = self._hits[key]
            while hits and now - hits[0] >= self._window:
                hits.popleft()
            if not hits:
                del self._hits[key]
