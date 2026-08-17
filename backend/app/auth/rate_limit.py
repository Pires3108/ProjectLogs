from collections.abc import Callable
from functools import lru_cache
from time import time
from typing import Annotated, Protocol

from fastapi import Depends
from redis import Redis
from redis.exceptions import RedisError

from app.auth.keys import ApiPrincipal, require_api_key
from app.config import get_settings
from app.errors import ApiError


class RateLimiter(Protocol):
    def check(self, principal_id: str) -> None: ...


class RedisFixedWindowRateLimiter:
    def __init__(
        self,
        *,
        client: Redis,
        limit: int,
        clock: Callable[[], float] = time,
    ) -> None:
        self.client = client
        self.limit = max(1, limit)
        self.clock = clock

    def check(self, principal_id: str) -> None:
        now = int(self.clock())
        window = now // 60
        key = f"ataviva:rate:{principal_id}:{window}"
        try:
            pipeline = self.client.pipeline(transaction=True)
            pipeline.incr(key)
            pipeline.expire(key, 61)
            count, _ = pipeline.execute()
        except RedisError as exception:
            raise ApiError(
                status_code=503,
                code="RATE_LIMIT_UNAVAILABLE",
                message="O controle de requisições está indisponível.",
            ) from exception
        if int(count) > self.limit:
            raise ApiError(
                status_code=429,
                code="RATE_LIMIT_EXCEEDED",
                message="O limite de requisições foi excedido.",
                details={
                    "limit_per_minute": self.limit,
                    "retry_after_seconds": 60 - now % 60,
                },
                headers={"Retry-After": str(60 - now % 60)},
            )


@lru_cache
def get_rate_limiter() -> RateLimiter:
    settings = get_settings()
    return RedisFixedWindowRateLimiter(
        client=Redis.from_url(settings.redis_url, decode_responses=True),
        limit=settings.api_rate_limit_per_minute,
    )


def require_rate_limited_api_key(
    principal: Annotated[ApiPrincipal, Depends(require_api_key)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> ApiPrincipal:
    limiter.check(principal.id)
    return principal
