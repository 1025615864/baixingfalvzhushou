"""限流中间件 - 分级限流"""
import os
import time
import logging
from typing import Optional, Tuple
from fastapi import Request, HTTPException, status
import redis.asyncio as redis

logger = logging.getLogger(__name__)


RATE_LIMIT_RULES = {
    "/api/v1/legal/consultations": (30, 60),
    "/api/v1/legal/appointments": (10, 60),
    "/api/v1/legal/lawyers/search": (60, 60),
    "/api/v1/legal/documents": (20, 60),
    "/api/v1/legal/admin": (5, 60),
    "/api/v1/legal/reviews": (15, 60),
}


class RateLimiter:
    """统一限流器"""

    DEFAULT_LIMIT = 100
    DEFAULT_WINDOW = 60

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
                logger.error("Redis限流客户端初始化失败")
                self._client = None
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    def _get_rule(self, path: str) -> Tuple[int, int]:
        for prefix, rule in RATE_LIMIT_RULES.items():
            if path.startswith(prefix):
                return rule
        return self.DEFAULT_LIMIT, self.DEFAULT_WINDOW

    async def check_rate_limit(
        self,
        user_id: str,
        path: str,
    ) -> Tuple[bool, Optional[int], int]:
        limit, window = self._get_rule(path)
        key = f"rate:{path}:{user_id}"

        client = await self._get_client()
        if not client:
            return True, None, limit

        try:
            current = await client.get(key)
            if current is None:
                await client.setex(key, window, 1)
                return True, limit - 1, limit

            count = int(current)
            if count >= limit:
                ttl = await client.ttl(key)
                return False, ttl, limit

            await client.incr(key)
            return True, limit - count - 1, limit

        except Exception:
            logger.error("限流检查失败，默认放行")
            return True, None, limit

    async def get_remaining(
        self,
        user_id: str,
        path: str,
    ) -> Optional[int]:
        limit, window = self._get_rule(path)
        key = f"rate:{path}:{user_id}"

        client = await self._get_client()
        if not client:
            return limit

        try:
            current = await client.get(key)
            if current is None:
                return limit
            return max(0, limit - int(current))
        except Exception:
            logger.error("获取限流剩余次数失败")
            return None


rate_limiter = RateLimiter()


async def check_request_rate_limit(request: Request) -> None:
    """检查请求速率限制"""
    if request.method not in ("POST", "PUT", "PATCH"):
        return

    path = request.url.path
    user_id = request.headers.get("X-User-ID", "anonymous")

    allowed, remaining, limit = await rate_limiter.check_rate_limit(user_id, path)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"请求过于频繁，请 {remaining} 秒后重试",
            headers={
                "Retry-After": str(remaining or 60),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(remaining or 0),
            },
        )


async def check_consultation_rate(user_id: str) -> Tuple[bool, Optional[int], int]:
    """检查咨询速率限制（30次/分钟）"""
    return await rate_limiter.check_rate_limit(user_id, "/api/v1/legal/consultations")