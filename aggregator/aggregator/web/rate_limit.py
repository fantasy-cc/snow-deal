"""Small in-memory sliding-window rate limiter for sensitive web endpoints."""

from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Request


class SlidingWindowRateLimiter:
    """Track request timestamps per key within a fixed time window."""

    def __init__(self, window_seconds: int):
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int) -> bool:
        """Return True if the request should be allowed."""
        now = monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._buckets[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True

    def clear(self) -> None:
        """Reset all tracked request history."""
        with self._lock:
            self._buckets.clear()


def client_key(request: Request, scope: str) -> str:
    """Build a stable limiter key from the client IP and route scope."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        client_ip = forwarded.split(",", 1)[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    return f"{scope}:{client_ip}"
