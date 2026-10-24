from __future__ import annotations

from app.core.ratelimit import InMemoryRateLimiter


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = InMemoryRateLimiter()
    for _ in range(3):
        allowed, retry_after = limiter.hit("auth:test", limit=3, window_seconds=60)
        assert allowed is True
        assert retry_after == 0

    allowed, retry_after = limiter.hit("auth:test", limit=3, window_seconds=60)
    assert allowed is False
    assert retry_after >= 1


def test_rate_limiter_isolated_by_key() -> None:
    limiter = InMemoryRateLimiter()
    assert limiter.hit("a", limit=1)[0] is True
    assert limiter.hit("b", limit=1)[0] is True
    assert limiter.hit("a", limit=1)[0] is False
