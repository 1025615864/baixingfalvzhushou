"""Redis 缓存服务"""
import logging
from typing import Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class CacheService:
    """Redis 缓存服务"""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self, redis_url: str) -> bool:
        """连接 Redis"""
        try:
            self._redis = aioredis.from_url(redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info(f"Redis 连接成功: {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")
            return True
        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            self._redis = None
            return False

    async def disconnect(self):
        """断开 Redis 连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis 连接已断开")

    @property
    def redis(self) -> Optional[aioredis.Redis]:
        """获取 Redis 实例"""
        return self._redis

    async def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        if self._redis:
            try:
                return await self._redis.get(key)
            except Exception as e:
                logger.error(f"Redis GET 失败: {e}")
        return None

    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """设置缓存值"""
        if self._redis:
            try:
                await self._redis.set(key, value, ex=ttl)
                return True
            except Exception as e:
                logger.error(f"Redis SET 失败: {e}")
        return False

    async def acquire_lock(self, key: str, value: str, expire: int) -> bool:
        """获取分布式锁"""
        if not self._redis:
            logger.warning("Redis未连接，无法获取锁")
            return False
        try:
            return bool(await self._redis.set(key, value, nx=True, ex=expire))
        except Exception as e:
            logger.error(f"获取锁失败: {e}")
            return False

    async def refresh_lock(self, key: str, value: str, expire: int) -> bool:
        """续期分布式锁"""
        if not self._redis:
            logger.warning("Redis未连接，无法续期锁")
            return False
        try:
            current_value = await self._redis.get(key)
            if current_value == value:
                await self._redis.expire(key, expire)
                return True
            return False
        except Exception as e:
            logger.error(f"续期锁失败: {e}")
            return False

    async def release_lock(self, key: str, value: str) -> bool:
        """释放分布式锁"""
        if not self._redis:
            logger.warning("Redis未连接，无法释放锁")
            return False
        try:
            current_value = await self._redis.get(key)
            if current_value == value:
                await self._redis.delete(key)
                return True
            return False
        except Exception as e:
            logger.error(f"释放锁失败: {e}")
            return False


# 全局单例
cache_service = CacheService()


def get_cache_service() -> CacheService:
    """获取缓存服务实例（依赖注入）"""
    return cache_service
