"""Redis-backed rate limiting using sliding window algorithm."""

import time
from typing import Literal

from fastapi import Depends, Request
from fastapi.responses import JSONResponse

from ..core.redis import get_redis
from ..middleware.auth import get_optional_user
from ..models.user import User

EndpointGroup = Literal["auth", "api", "upload"]

# Configurable limits: (requests, window_seconds)
RATE_LIMITS: dict[EndpointGroup, tuple[int, int]] = {
    "auth": (5, 60),      # 5 per minute for login/register
    "api": (100, 60),     # 100 per minute per user
    "upload": (10, 60),   # 10 per minute for file uploads
}


async def _get_identifier(request: Request, user: User | None, group: EndpointGroup) -> str:
    """Get rate limit identifier: IP for auth, user_id for api/upload when authenticated."""
    if group == "auth":
        client_host = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("x-forwarded-for")
        ip = forwarded.split(",")[0].strip() if forwarded else client_host
        return ip
    if user:
        return f"user:{user.id}"
    client_host = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else client_host
    return f"ip:{ip}"


async def _sliding_window_check(redis, key: str, limit: int, window: int) -> tuple[bool, int]:
    """
    Sliding window: add current timestamp to sorted set, remove old entries,
    count remaining. Returns (allowed, retry_after_seconds).
    """
    now = time.time()
    window_start = now - window
    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window + 1)
    results = await pipe.execute()
    count = results[2]
    if count > limit:
        # Get oldest timestamp in window to compute retry-after
        oldest = await redis.zrange(key, 0, 0, withscores=True)
        retry_after = int((oldest[0][1] + window - now) + 1) if oldest else window
        return False, max(1, retry_after)
    return True, 0


class RateLimiter:
    """FastAPI dependency for rate limiting by endpoint group."""

    def __init__(self, group: EndpointGroup = "api"):
        self.group = group
        self.limit, self.window = RATE_LIMITS[group]

    async def __call__(
        self,
        request: Request,
        user: User | None = Depends(get_optional_user),
    ) -> None:
        redis = await get_redis()
        identifier = await _get_identifier(request, user, self.group)
        key = f"ratelimit:{identifier}:{self.group}:{int(time.time() // self.window)}"
        allowed, retry_after = await _sliding_window_check(
            redis, key, self.limit, self.window
        )
        if not allowed:
            raise RateLimitExceeded(retry_after=retry_after)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after


def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return 429 with Retry-After header."""
    return JSONResponse(
        status_code=429,
        content={"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"}},
        headers={"Retry-After": str(exc.retry_after)},
    )
