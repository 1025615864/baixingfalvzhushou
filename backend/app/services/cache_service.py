"""Redis 缓存服务"""
import json
import logging
import time
import functools
from typing import Optional, Any, TypeVar, ParamSpec

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

JsonDict = dict[str, Any]
JsonList = list[Any]
JsonValue = JsonDict | JsonList
TJson = TypeVar("TJson", bound=JsonValue)
P = ParamSpec("P")

_memory_cache: dict[str, tuple[Any, float]] = {}


class CacheService:
    """Redis 缓存服务"""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._connected: bool = False
        self.hits: int = 0
        self.misses: int = 0

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self, redis_url: str) -> bool:
        try:
            self._redis = aioredis.from_url(redis_url, decode_responses=True)
            await self._redis.ping()
            self._connected = True
            logger.info(f"Redis 连接成功: {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")
            return True
        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            self._redis = None
            self._connected = False
            return False

    async def disconnect(self):
        if self._redis:
            await self._redis.close()
            self._redis = None
        self._connected = False
        logger.info("Redis 连接已断开")

    @property
    def redis(self) -> Optional[aioredis.Redis]:
        return self._redis

    def _get_memory(self, key: str) -> Optional[str]:
        if key in _memory_cache:
            value, expires_at = _memory_cache[key]
            if time.time() > expires_at:
                del _memory_cache[key]
                return None
            return value
        return None

    def _set_memory(self, key: str, value: str, ttl: int = 300) -> None:
        _memory_cache[key] = (value, time.time() + ttl)

    def _delete_memory(self, key: str) -> bool:
        if key in _memory_cache:
            del _memory_cache[key]
            return True
        return False

    async def get(self, key: str) -> Optional[str]:
        if self._connected and self._redis:
            try:
                result = await self._redis.get(key)
                if result is not None:
                    self.hits += 1
                    return result
            except Exception as e:
                logger.error(f"Redis GET 失败: {e}")
        mem = self._get_memory(key)
        if mem is not None:
            self.hits += 1
            return mem
        self.misses += 1
        return None

    async def set(self, key: str, value: str, expire: int = 3600) -> bool:
        if self._connected and self._redis:
            try:
                await self._redis.setex(key, expire, value)
                return True
            except Exception as e:
                logger.error(f"Redis SET 失败: {e}")
        self._set_memory(key, value, ttl=expire)
        return True

    async def delete(self, key: str) -> bool:
        if self._connected and self._redis:
            try:
                await self._redis.delete(key)
            except Exception as e:
                logger.error(f"Redis DELETE 失败: {e}")
        return self._delete_memory(key)

    async def get_json(self, key: str) -> Optional[JsonValue]:
        value = await self.get(key)
        if value is None:
            return None
        try:
            parsed = json.loads(value)
            if isinstance(parsed, (dict, list)):
                return parsed
            return None
        except (json.JSONDecodeError, ValueError):
            return None

    async def set_json(self, key: str, value: JsonValue, expire: int = 3600) -> bool:
        return await self.set(key, json.dumps(value, ensure_ascii=False), expire=expire)

    async def clear_pattern(self, pattern: str) -> int:
        count = 0
        if self._connected and self._redis:
            try:
                keys = []
                async for k in self._redis.scan_iter(match=pattern):
                    keys.append(k)
                if keys:
                    count = await self._redis.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear_pattern 失败: {e}")
        import fnmatch
        to_delete = [k for k in list(_memory_cache.keys()) if fnmatch.fnmatch(k, pattern)]
        for k in to_delete:
            del _memory_cache[k]
            count += 1
        return count

    async def setnx(self, key: str, value: str, expire: int = 300) -> bool:
        if self._connected and self._redis:
            try:
                result = await self._redis.set(key, value, nx=True, ex=expire)
                return result is not None
            except Exception as e:
                logger.error(f"Redis SETNX 失败: {e}")
        existing = self._get_memory(key)
        if existing is not None:
            return False
        self._set_memory(key, value, ttl=expire)
        return True

    async def increment(self, key: str, amount: int = 1) -> int:
        if self._connected and self._redis:
            try:
                return await self._redis.incrby(key, amount)
            except Exception as e:
                logger.error(f"Redis INCREMENT 失败: {e}")
        existing = self._get_memory(key)
        if existing is not None:
            try:
                new_val = int(existing) + amount
                self._set_memory(key, str(new_val), ttl=300)
                return new_val
            except (ValueError, TypeError):
                return 0
        else:
            self._set_memory(key, str(amount), ttl=300)
            return amount

    async def acquire_lock(self, key: str, value: str, expire: int) -> bool:
        if self._connected and self._redis:
            try:
                return bool(await self._redis.set(key, value, nx=True, ex=expire))
            except Exception as e:
                logger.error(f"获取锁失败: {e}")
                return False
        existing = self._get_memory(key)
        if existing is not None:
            return False
        self._set_memory(key, value, ttl=expire)
        return True

    async def refresh_lock(self, key: str, value: str, expire: int) -> bool:
        if self._connected and self._redis:
            try:
                lua_script = """
                if redis.call("get", KEYS[1]) == ARGV[1] then
                    redis.call("expire", KEYS[1], ARGV[2])
                    return 1
                end
                return 0
                """
                result = await self._redis.eval(lua_script, 1, key, value, expire)
                return int(result or 0) > 0
            except Exception as e:
                logger.error(f"续期锁失败: {e}")
        existing = self._get_memory(key)
        if existing is None:
            return True
        if existing == value:
            self._set_memory(key, value, ttl=expire)
            return True
        return False

    async def release_lock(self, key: str, value: str) -> bool:
        if self._connected and self._redis:
            try:
                lua_script = """
                if redis.call("get", KEYS[1]) == ARGV[1] then
                    return redis.call("del", KEYS[1])
                end
                return 0
                """
                result = await self._redis.eval(lua_script, 1, key, value)
                return int(result or 0) > 0
            except Exception as e:
                logger.error(f"释放锁失败: {e}")
        existing = self._get_memory(key)
        if existing is None:
            return True
        if existing == value:
            self._delete_memory(key)
            return True
        return True

    def reset_stats(self) -> None:
        self.hits = 0
        self.misses = 0


def cached(prefix: str, expire: int = 3600):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{prefix}:{args}:{kwargs}"
            result = await cache_service.get(cache_key)
            if result is not None:
                try:
                    return json.loads(result)
                except (json.JSONDecodeError, ValueError):
                    return result
            value = await func(*args, **kwargs)
            if value is not None:
                await cache_service.set(cache_key, json.dumps(value, ensure_ascii=False, default=str), expire=expire)
            return value
        return wrapper
    return decorator


cache_service = CacheService()


def get_cache_service() -> CacheService:
    return cache_service
