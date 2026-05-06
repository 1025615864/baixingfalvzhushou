"""Redis缓存和会话服务"""
import json
import logging
from typing import Optional, Any
from datetime import timedelta

import redis.asyncio as redis

from ..config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class RedisService:
    """Redis服务"""

    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self) -> bool:
        """连接Redis"""
        try:
            password = settings.redis_password
            url = settings.redis_url
            if password:
                url = url.replace("redis://", f"redis://:{password}@")

            self._client = redis.from_url(
                url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await self._client.ping()
            self._connected = True
            logger.info("Redis connected successfully")
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """断开Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None
            self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        if not self._client:
            return None
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: str,
        expire_seconds: Optional[int] = None
    ) -> bool:
        """设置值"""
        if not self._client:
            return False
        try:
            if expire_seconds:
                await self._client.setex(key, expire_seconds, value)
            else:
                await self._client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除键"""
        if not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._client:
            return False
        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    async def incr(self, key: str) -> int:
        """递增计数器"""
        if not self._client:
            return 0
        try:
            return await self._client.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return 0

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not self._client:
            return False
        try:
            return await self._client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """获取剩余生存时间"""
        if not self._client:
            return -1
        try:
            return await self._client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error: {e}")
            return -1


class SessionStore:
    """会话存储"""

    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
        self.session_prefix = "session:"
        self.session_ttl = settings.refresh_token_expire_days * 24 * 3600

    def _session_key(self, user_id: int) -> str:
        return f"{self.session_prefix}{user_id}"

    async def save_session(self, user_id: int, session_data: dict) -> bool:
        """保存会话数据"""
        key = self._session_key(user_id)
        value = json.dumps(session_data)
        return await self.redis.set(key, value, self.session_ttl)

    async def get_session(self, user_id: int) -> Optional[dict]:
        """获取会话数据"""
        key = self._session_key(user_id)
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    async def delete_session(self, user_id: int) -> bool:
        """删除会话"""
        key = self._session_key(user_id)
        return await self.redis.delete(key)


class RateLimiter:
    """限流器 - 滑动窗口算法"""

    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
        self.window_size = 60
        self.max_requests = 100

    async def is_allowed(self, identifier: str, max_requests: int = None, window_seconds: int = None) -> tuple[bool, int]:
        """检查是否允许请求

        Returns:
            (is_allowed, remaining_requests)
        """
        if not self.redis.is_connected:
            return True, max_requests or self.max_requests

        max_requests = max_requests or self.max_requests
        window_seconds = window_seconds or self.window_size

        key = f"rate_limit:{identifier}"

        try:
            current = await self.redis.client.incr(key)
            if current == 1:
                await self.redis.client.expire(key, window_seconds)

            remaining = max(0, max_requests - current)
            is_allowed = current <= max_requests

            return is_allowed, remaining
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True, max_requests


redis_service = RedisService()
session_store = SessionStore(redis_service)
rate_limiter = RateLimiter(redis_service)
