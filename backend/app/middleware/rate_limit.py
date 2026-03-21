"""接口限流中间件增强版

支持:
- 基于IP的限流
- 基于用户ID的限流
- 基于API端点的限流
- 滑动窗口算法
- Redis分布式限流
- Prometheus指标
"""
import asyncio
import time
from collections import defaultdict
from typing import Optional, Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from ..services.cache_service import cache_service
from ..services.prometheus_metrics import prometheus_metrics

# 限流维度
class LimitDimension:
    IP = "ip"
    USER = "user"
    ENDPOINT = "endpoint"
    GLOBAL = "global"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """增强版请求速率限制中间件

    支持多维度限流:
    - IP限流: 防止爬虫/恶意攻击
    - 用户限流: 防止单个用户过度使用
    - 端点限流: 针对特定接口的精细限流
    - 全局限流: 保护整体系统
    """

    # 全局限流配置
    GLOBAL_LIMIT = 10000  # 全局 10000 req/s
    IP_LIMIT = 100  # IP 100 req/min
    USER_LIMIT = 60  # 用户 60 req/min

    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        requests_per_second: int = 10,
        excluded_paths: list[str] | None = None,
        trusted_proxies: list[str] | None = None,
        max_tracked_ips: int = 10000,
        enable_user_limit: bool = True,
        enable_global_limit: bool = True,
        global_limit: int = 10000,
    ):
        super().__init__(app)
        self.requests_per_minute: int = requests_per_minute
        self.requests_per_second: int = requests_per_second
        self.excluded_paths: list[str] = excluded_paths or [
            "/docs", "/redoc", "/openapi.json", "/health", "/"]
        self.trusted_proxies: set[str] = set(trusted_proxies or [])
        self.max_tracked_ips: int = max(100, int(max_tracked_ips))
        self.enable_user_limit = enable_user_limit
        self.enable_global_limit = enable_global_limit
        self.global_limit = global_limit

        self.request_records: dict[str, list[float]] = defaultdict(list)
        self._ip_last_seen: dict[str, float] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        remote = request.client.host if request.client else "unknown"

        if remote in self.trusted_proxies:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip.strip()

        return remote

    def _get_user_id(self, request: Request) -> Optional[str]:
        """获取用户ID"""
        return getattr(request.state, "user_id", None)

    def _get_rate_limit_key(self, request: Request, dimension: str) -> str:
        """生成限流键"""
        parts = ["rl", dimension]

        if dimension == LimitDimension.IP:
            parts.append(self._get_client_ip(request))
        elif dimension == LimitDimension.USER:
            user_id = self._get_user_id(request)
            if user_id:
                parts.append(str(user_id))
            else:
                return ""  # 未登录用户不进行用户维限流
        elif dimension == LimitDimension.ENDPOINT:
            parts.append(request.url.path)
        elif dimension == LimitDimension.GLOBAL:
            parts.append("global")

        return ":".join(parts)

    def _evict_if_needed(self) -> None:
        if len(self.request_records) < self.max_tracked_ips:
            return

        oldest_ip: str | None = None
        oldest_time = float("inf")
        for ip, last_seen in self._ip_last_seen.items():
            if last_seen < oldest_time:
                oldest_time = last_seen
                oldest_ip = ip

        if oldest_ip is not None:
            _ = self.request_records.pop(oldest_ip, None)
            _ = self._ip_last_seen.pop(oldest_ip, None)

    async def _clean_old_records(self, ip: str, current_time: float):
        """清理过期的请求记录"""
        cutoff = current_time - 60
        async with self._lock:
            self.request_records[ip] = [
                t for t in self.request_records[ip] if t > cutoff
            ]
            if not self.request_records[ip]:
                _ = self.request_records.pop(ip, None)
                _ = self._ip_last_seen.pop(ip, None)

    async def _check_rate_limit_memory(
        self, key: str, limit: int
    ) -> tuple[bool, str, int]:
        """内存限流检查"""
        current_time = time.time()

        async with self._lock:
            if key not in self.request_records:
                self._evict_if_needed()
                if key not in self.request_records:
                    self.request_records[key] = []

            records = self.request_records[key]
            cutoff = current_time - 60
            records = [t for t in records if t > cutoff]
            self.request_records[key] = records

            if len(records) >= limit:
                return False, "请求过于频繁，请稍后再试", 0

            self.request_records[key].append(current_time)
            return True, "", max(0, limit - len(self.request_records[key]))

    async def _check_rate_limit_redis(
        self, key: str, limit: int, window: int = 60
    ) -> tuple[bool, str, int]:
        """Redis限流检查（滑动窗口）"""
        redis = cache_service.redis
        if redis is None:
            return await self._check_rate_limit_memory(key, limit)

        count_key = f"{key}:count"
        window_key = f"{key}:window"

        current_time = time.time()
        window_start = current_time - window

        pipe = redis.pipeline()

        pipe.zremrangebyscore(window_key, 0, window_start)
        pipe.zadd(window_key, {str(current_time): current_time})
        pipe.zcard(window_key)
        pipe.expire(window_key, window + 1)

        results = await pipe.execute()
        current_count = results[2]

        if current_count > limit:
            ttl = await redis.ttl(window_key)
            wait_time = max(1, ttl) if ttl > 0 else window
            return False, "请求过于频繁，请稍后再试", 0

        remaining = max(0, limit - current_count - 1)
        return True, "", remaining

    async def _check_global_limit(self) -> tuple[bool, str, int]:
        """检查全局限流"""
        if not self.enable_global_limit:
            return True, "", self.global_limit

        key = "rl:global"
        return await self._check_rate_limit_redis(key, self.global_limit, window=1)

    async def _check_ip_limit(self, request: Request) -> tuple[bool, str, int]:
        """检查IP限流"""
        ip = self._get_client_ip(request)
        key = f"rl:ip:{ip}"
        return await self._check_rate_limit_redis(key, self.IP_LIMIT)

    async def _check_user_limit(self, request: Request) -> tuple[bool, str, int]:
        """检查用户限流"""
        if not self.enable_user_limit:
            return True, "", self.USER_LIMIT

        user_id = self._get_user_id(request)
        if not user_id:
            return True, "", self.USER_LIMIT

        key = f"rl:user:{user_id}"
        return await self._check_rate_limit_redis(key, self.USER_LIMIT)

    def _record_metrics(self, endpoint: str, allowed: bool, dimension: str):
        """记录Prometheus指标"""
        try:
            prometheus_metrics.record_rate_limit(
                endpoint=endpoint,
                allowed=allowed,
                dimension=dimension
            )
        except Exception:
            pass

    async def dispatch(self, request: Request,
                       call_next: RequestResponseEndpoint) -> Response:
        """处理请求"""
        path = request.url.path

        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)

        endpoint = path

        # 1. 检查全局限流
        allowed, message, remaining = await self._check_global_limit()
        if not allowed:
            self._record_metrics(endpoint, False, LimitDimension.GLOBAL)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "系统请求过于频繁，请稍后再试"},
                headers={
                    "Retry-After": "1",
                    "X-RateLimit-Dimension": "global",
                },
            )

        # 2. 检查IP限流
        allowed, message, remaining = await self._check_ip_limit(request)
        if not allowed:
            self._record_metrics(endpoint, False, LimitDimension.IP)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": message},
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Dimension": "ip",
                },
            )

        # 3. 检查用户限流（如果已登录）
        user_id = self._get_user_id(request)
        if user_id:
            allowed, message, remaining = await self._check_user_limit(request)
            if not allowed:
                self._record_metrics(endpoint, False, LimitDimension.USER)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": message},
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Dimension": "user",
                    },
                )

        # 继续处理请求
        response = await call_next(request)

        # 添加速率限制头信息
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Global"] = str(self.global_limit)

        return response


class APIKeyRateLimiter:
    """基于API Key的速率限制器（用于特定接口）"""

    def __init__(self, requests_per_minute: int = 20):
        self.requests_per_minute: int = requests_per_minute
        self.request_records: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> bool:
        """检查是否允许请求"""
        current_time = time.time()
        cutoff = current_time - 60

        # 清理过期记录
        self.request_records[key] = [
            t for t in self.request_records[key] if t > cutoff
        ]

        # 检查限制
        if len(self.request_records[key]) >= self.requests_per_minute:
            return False

        self.request_records[key].append(current_time)
        return True


# AI聊天接口限流器（更严格）
ai_chat_limiter = APIKeyRateLimiter(requests_per_minute=30)

# 文书生成接口限流器
document_limiter = APIKeyRateLimiter(requests_per_minute=10)

# 关键词检查接口限流器
keyword_check_limiter = APIKeyRateLimiter(requests_per_minute=60)
