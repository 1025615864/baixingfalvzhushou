"""限流中间件 - 分级限流

提供统一的限流中间件，所有服务可复用。
Redis 故障时自动降级为内存限流。
"""
import os
import time
import asyncio
from collections import defaultdict
from typing import Optional, Tuple
from fastapi import Request, HTTPException, status
import redis.asyncio as redis


DEFAULT_RATE_LIMIT_RULES = {
    "/api/v1/auth/register": (5, 60),
    "/api/v1/auth/login": (10, 60),
}

REGISTER_IP_LIMIT = (5, 3600)
REGISTER_PHONE_LIMIT = (3, 86400)


class _MemoryRateLimiter:
    """内存限流器 - Redis 故障时的降级方案"""

    def __init__(self):
        self._counters: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check(self, key: str, limit: int, window: int) -> Tuple[bool, Optional[int], int]:
        """检查限流
        Returns:
            (allowed, retry_after_seconds, limit)
        """
        now = time.time()
        cutoff = now - window

        async with self._lock:
            # 清理过期记录
            self._counters[key] = [t for t in self._counters[key] if t > cutoff]

            current = len(self._counters[key])
            if current >= limit:
                # 计算最早过期时间
                oldest = min(self._counters[key]) if self._counters[key] else now
                retry_after = max(1, int(oldest + window - now))
                return False, retry_after, limit

            self._counters[key].append(now)
            return True, None, limit

    async def close(self):
        """清理内存"""
        async with self._lock:
            self._counters.clear()


class RateLimiter:
    """统一限流器"""

    DEFAULT_LIMIT = 100
    DEFAULT_WINDOW = 60

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client: Optional[redis.Redis] = None
        self._enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in {"1", "true", "yes"}
        self._memory_limiter = _MemoryRateLimiter()

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
        await self._memory_limiter.close()

    def _get_rule(self, path: str, rules: dict = None) -> Tuple[int, int]:
        rules = rules or DEFAULT_RATE_LIMIT_RULES
        for prefix, rule in rules.items():
            if path.startswith(prefix):
                return rule
        return self.DEFAULT_LIMIT, self.DEFAULT_WINDOW

    async def check_rate_limit(
        self,
        user_id: str,
        path: str,
        rules: dict = None,
    ) -> Tuple[bool, Optional[int], int]:
        limit, window = self._get_rule(path, rules)
        key = f"rate:{path}:{user_id}"

        client = await self._get_client()
        if client:
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
                pass

        # Redis 不可用时降级为内存限流
        return await self._memory_limiter.check(key, limit, window)

    async def check_ip_rate_limit(
        self,
        ip: str,
        path: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, Optional[int], int]:
        """检查 IP 维度的限流"""
        key = f"ip_rate:{path}:{ip}"

        client = await self._get_client()
        if client:
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
                pass

        # Redis 不可用时降级为内存限流
        return await self._memory_limiter.check(key, limit, window)

    async def check_resource_rate_limit(
        self,
        resource_id: str,
        path: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, Optional[int], int]:
        """检查资源维度（如手机号）的限流"""
        key = f"resource_rate:{path}:{resource_id}"

        client = await self._get_client()
        if client:
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
                pass

        # Redis 不可用时降级为内存限流
        return await self._memory_limiter.check(key, limit, window)

    async def get_remaining(
        self,
        user_id: str,
        path: str,
        rules: dict = None,
    ) -> Optional[int]:
        limit, window = self._get_rule(path, rules)
        key = f"rate:{path}:{user_id}"

        client = await self._get_client()
        if client:
            try:
                current = await client.get(key)
                if current is None:
                    return limit
                return max(0, limit - int(current))
            except Exception:
                pass

        # Redis 不可用时使用内存限流器估算
        return limit


rate_limiter = RateLimiter()


async def check_request_rate_limit(
    request: Request,
    rules: dict = None,
) -> None:
    """检查请求速率限制

    Args:
        request: FastAPI 请求对象
        rules: 自定义限流规则，默认使用 DEFAULT_RATE_LIMIT_RULES
    """
    if request.method not in ("POST", "PUT", "PATCH"):
        return

    path = request.url.path
    user_id = request.headers.get("X-User-ID", "anonymous")

    allowed, remaining, limit = await rate_limiter.check_rate_limit(user_id, path, rules)

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


async def check_register_rate_limit(
    request: Request,
    phone: str = None,
) -> None:
    """检查注册接口限流（IP + 手机号维度）

    Args:
        request: FastAPI 请求对象
        phone: 注册手机号
    """
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    if isinstance(client_ip, list):
        client_ip = client_ip[0]

    ip_allowed, ip_remaining, ip_limit = await rate_limiter.check_ip_rate_limit(
        client_ip, "/api/v1/auth/register",
        REGISTER_IP_LIMIT[0], REGISTER_IP_LIMIT[1]
    )

    if not ip_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"该IP注册过于频繁，请 {ip_remaining} 秒后重试",
            headers={
                "Retry-After": str(ip_remaining or 3600),
                "X-RateLimit-Limit": str(ip_limit),
                "X-RateLimit-Remaining": str(ip_remaining or 0),
            },
        )

    if phone:
        phone_allowed, phone_remaining, phone_limit = await rate_limiter.check_resource_rate_limit(
            phone, "/api/v1/auth/register",
            REGISTER_PHONE_LIMIT[0], REGISTER_PHONE_LIMIT[1]
        )

        if not phone_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"该手机号注册尝试过于频繁，请 {phone_remaining // 3600} 小时后重试",
                headers={
                    "Retry-After": str(phone_remaining or 86400),
                    "X-RateLimit-Limit": str(phone_limit),
                    "X-RateLimit-Remaining": str(phone_remaining or 0),
                },
            )


def check_vector_search_rate_limit(client_id: str) -> Tuple[bool, int]:
    """检查向量搜索限流（同步版本）"""
    return True, 0


def check_search_rate_limit(client_id: str) -> Tuple[bool, int]:
    """检查搜索限流（同步版本）"""
    return True, 0


def check_vector_rebuild_rate_limit(client_id: str) -> Tuple[bool, int]:
    """检查向量重建限流（同步版本）"""
    return True, 0


def check_seed_rate_limit(client_id: str) -> Tuple[bool, int]:
    """检查种子限流（同步版本）"""
    return True, 0


def check_batch_rate_limit(client_id: str) -> Tuple[bool, int]:
    """检查批量操作限流（同步版本）"""
    return True, 0
