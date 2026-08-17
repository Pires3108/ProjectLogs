import pytest
from redis.exceptions import ConnectionError

from app.auth.rate_limit import RedisFixedWindowRateLimiter
from app.errors import ApiError


class FakePipeline:
    def __init__(self, client) -> None:
        self.client = client
        self.key = ""

    def incr(self, key: str) -> None:
        self.key = key

    def expire(self, key: str, seconds: int) -> None:
        assert key == self.key
        assert seconds == 61

    def execute(self) -> tuple[int, bool]:
        self.client.count += 1
        return self.client.count, True


class FakeRedis:
    def __init__(self) -> None:
        self.count = 0

    def pipeline(self, transaction: bool) -> FakePipeline:
        assert transaction is True
        return FakePipeline(self)


class FailingRedis:
    def pipeline(self, transaction: bool):
        raise ConnectionError("synthetic outage")


def test_fixed_window_rejects_requests_above_limit() -> None:
    limiter = RedisFixedWindowRateLimiter(client=FakeRedis(), limit=2, clock=lambda: 125)

    limiter.check("client-id")
    limiter.check("client-id")
    with pytest.raises(ApiError) as captured:
        limiter.check("client-id")

    assert captured.value.status_code == 429
    assert captured.value.details["retry_after_seconds"] == 55
    assert captured.value.headers["Retry-After"] == "55"


def test_rate_limiter_fails_closed_when_redis_is_unavailable() -> None:
    limiter = RedisFixedWindowRateLimiter(client=FailingRedis(), limit=2)

    with pytest.raises(ApiError) as captured:
        limiter.check("client-id")

    assert captured.value.code == "RATE_LIMIT_UNAVAILABLE"
