"""限流中间件"""
import os
import time
from typing import Optional
from fastapi import Request, HTTPException, status
import redis.asyncio as redis


class RateLimiter:
    RULES = {
        "post": {"limit": 1, "window": 300},
        "comment": {"limit": 5, "window": 60},
        "like": {"limit": 20, "window": 60},
        "report": {"limit": 10, "window": 3600},
    }

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client: Optional[redis.Redis] = None
        self._enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in {"1", "true", "yes"}

    async def _get_client(self) -> Optional[redis.Redis]:
        if not self._enabled:
            return None
        if self._client is None:
            try:
                self._client = redis.from_url(self.redis_url, decode_responses=True)
                await self._client.ping()
            except Exception:
                self._client = None
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    async def check_rate_limit(
        self,
        user_id: int,
        action: str
    ) -> tuple[bool, Optional[int]]:
        if action not in self.RULES:
            return True, None

        client = await self._get_client()
        if not client:
            return True, None

        rule = self.RULES[action]
        key = f"rate:{action}:{user_id}"

        try:
            current = await client.get(key)
            if current is None:
                await client.setex(key, rule["window"], 1)
                return True, rule["limit"] - 1

            count = int(current)
            if count >= rule["limit"]:
                ttl = await client.ttl(key)
                return False, ttl

            await client.incr(key)
            return True, rule["limit"] - count - 1

        except Exception:
            return True, None

    async def get_remaining(
        self,
        user_id: int,
        action: str
    ) -> Optional[int]:
        if action not in self.RULES:
            return None

        client = await self._get_client()
        if not client:
            return None

        key = f"rate:{action}:{user_id}"
        try:
            current = await client.get(key)
            if current is None:
                return self.RULES[action]["limit"]
            return max(0, self.RULES[action]["limit"] - int(current))
        except Exception:
            return None


rate_limiter = RateLimiter()


async def check_post_rate(request: Request) -> None:
    if request.method != "POST":
        return

    path = request.url.path
    user_id_header = request.headers.get("X-User-ID")

    if not user_id_header:
        return

    try:
        user_id = int(user_id_header)
    except ValueError:
        return

    action = None
    if "/posts" in path and request.method == "POST":
        action = "post"
    elif "/comments" in path and request.method == "POST":
        action = "comment"
    elif "/like" in path:
        action = "like"
    elif "/reports" in path and request.method == "POST":
        action = "report"

    if action:
        allowed, remaining = await rate_limiter.check_rate_limit(user_id, action)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"操作过于频繁，请 {remaining} 秒后重试",
                headers={"Retry-After": str(remaining or 60)},
            )
