from __future__ import annotations

import threading
import time
from collections import deque
from typing import Literal

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


class InMemoryRateLimiter:
    """Small process-local sliding-window limiter.

    Render runs a single API instance on the free tier, so a process-local
    limiter is sufficient for this deployment. A multi-instance deployment
    should replace it with a shared store (Redis or the database).
    """

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str, *, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(window_seconds - (now - events[0])) + 1)
                return False, retry_after
            events.append(now)
            if len(self._events) > 10_000:
                self._prune(cutoff)
            return True, 0

    def _prune(self, cutoff: float) -> None:
        empty: list[str] = []
        for key, events in self._events.items():
            while events and events[0] <= cutoff:
                events.popleft()
            if not events:
                empty.append(key)
        for key in empty:
            self._events.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


limiter = InMemoryRateLimiter()


def _client_key(request: Request) -> str:
    # Render terminates the public connection and appends the observed client
    # address to X-Forwarded-For. Use the rightmost value so a client-supplied
    # prefix cannot trivially rotate the rate-limit key.
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        candidate = forwarded.rsplit(",", 1)[-1].strip()
        if candidate:
            return candidate
    if request.client:
        return request.client.host
    return "unknown"


def rate_limit(scope: str, kind: Literal["auth", "mutation"] = "mutation"):
    async def dependency(request: Request) -> None:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return
        limit = (
            settings.auth_rate_limit_per_minute
            if kind == "auth"
            else settings.mutation_rate_limit_per_minute
        )
        allowed, retry_after = limiter.hit(
            f"{scope}:{_client_key(request)}",
            limit=limit,
            window_seconds=60,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Try again shortly.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
