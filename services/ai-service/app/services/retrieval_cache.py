"""RAG检索结果缓存"""
import hashlib
import time
import logging
import os
import json
from typing import Optional, Any
from dataclasses import dataclass
from collections import OrderedDict
import asyncio

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    docs: list
    retrieval_level: str
    timestamp: float
    hit_count: int = 0


class RetrievalCache:
    """RAG检索结果缓存 - LRU策略"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

    def _generate_key(self, query: str, intent: str = "legal", top_k: int = 5) -> str:
        """生成缓存键"""
        content = f"{query}:{intent}:{top_k}"
        return hashlib.md5(content.encode()).hexdigest()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查缓存是否过期"""
        return time.time() - entry.timestamp > self.ttl_seconds

    async def get(self, query: str, intent: str = "legal", top_k: int = 5) -> Optional[list]:
        """获取缓存结果"""
        key = self._generate_key(query, intent, top_k)

        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]

                if self._is_expired(entry):
                    del self._cache[key]
                    self._stats["misses"] += 1
                    logger.debug(f"Cache expired for key: {key[:8]}...")
                    return None

                entry.hit_count += 1
                self._cache.move_to_end(key)
                self._stats["hits"] += 1
                logger.debug(f"Cache hit for key: {key[:8]}..., hits: {entry.hit_count}")
                return entry.docs

            self._stats["misses"] += 1
            logger.debug(f"Cache miss for key: {key[:8]}...")
            return None

    async def set(
        self,
        query: str,
        docs: list,
        retrieval_level: str,
        intent: str = "legal",
        top_k: int = 5
    ):
        """设置缓存"""
        key = self._generate_key(query, intent, top_k)

        async with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)

            self._cache[key] = CacheEntry(
                docs=docs,
                retrieval_level=retrieval_level,
                timestamp=time.time()
            )

            if len(self._cache) > self.max_size:
                evicted_key, evicted_entry = self._cache.popitem(last=False)
                self._stats["evictions"] += 1
                logger.info(f"Cache evicted: {evicted_key[:8]}..., hits: {evicted_entry.hit_count}")

            logger.debug(f"Cache set for key: {key[:8]}...")

    async def invalidate(self, pattern: Optional[str] = None):
        """使缓存失效"""
        async with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Cache cleared: {count} entries removed")
            else:
                keys_to_remove = [k for k in self._cache.keys() if pattern in k]
                for key in keys_to_remove:
                    del self._cache[key]
                logger.info(f"Cache pattern '{pattern}': {len(keys_to_remove)} entries removed")

    async def get_stats(self) -> dict:
        """获取缓存统计"""
        async with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": round(hit_rate * 100, 2),
                "evictions": self._stats["evictions"]
            }

    async def cleanup_expired(self):
        """清理过期缓存"""
        async with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if self._is_expired(v)
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


class RedisCache:
    """Redis缓存实现"""

    CACHE_PREFIX = "rag:cache:"
    TTL_SECONDS = 600
    STATS_PREFIX = "rag:stats:"

    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._pool: Optional[redis.ConnectionPool] = None
        self._lock = asyncio.Lock()
        self._use_fallback = False
        self._fallback_cache = RetrievalCache(max_size=1000, ttl_seconds=self.TTL_SECONDS)
        self._init_redis()

    def _init_redis(self):
        """初始化Redis连接"""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            redis_password = os.getenv("REDIS_PASSWORD", None)

            pool = redis.ConnectionPool(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                max_connections=20
            )
            self._redis = redis.Redis(connection_pool=pool)
            self._pool = pool
            logger.info(f"Redis pool initialized: {redis_host}:{redis_port}/{redis_db}")
        except Exception as e:
            logger.warning(f"Redis initialization failed, will use fallback: {e}")
            self._redis = None
            self._pool = None
            self._use_fallback = True

    def _generate_key(self, query: str, intent: str, top_k: int) -> str:
        """生成缓存键"""
        content = f"{query}:{intent}:{top_k}"
        return f"{self.CACHE_PREFIX}{hashlib.md5(content.encode()).hexdigest()}"

    def _get_stats_key(self, stat_type: str) -> str:
        """获取统计键"""
        return f"{self.STATS_PREFIX}{stat_type}"

    async def get(self, query: str, intent: str = "legal", top_k: int = 5) -> Optional[list]:
        """获取缓存结果"""
        if self._use_fallback:
            return await self._fallback_cache.get(query, intent, top_k)

        try:
            if not self._redis:
                return await self._fallback_cache.get(query, intent, top_k)

            key = self._generate_key(query, intent, top_k)
            data = await self._redis.get(key)

            if data:
                parsed = json.loads(data)
                await self._redis.incr(self._get_stats_key("hits"))
                logger.debug(f"Redis cache hit for key: {key[:16]}...")
                return parsed.get("docs")
            else:
                await self._redis.incr(self._get_stats_key("misses"))
                logger.debug(f"Redis cache miss for key: {key[:16]}...")
                return None

        except redis.RedisError as e:
            logger.warning(f"Redis get failed, using fallback: {e}")
            return await self._fallback_cache.get(query, intent, top_k)
        except Exception as e:
            logger.warning(f"Cache get error, using fallback: {e}")
            return await self._fallback_cache.get(query, intent, top_k)

    async def set(
        self,
        query: str,
        docs: list,
        retrieval_level: str,
        intent: str = "legal",
        top_k: int = 5
    ):
        """设置缓存"""
        if self._use_fallback:
            await self._fallback_cache.set(query, docs, retrieval_level, intent, top_k)
            return

        try:
            if not self._redis:
                await self._fallback_cache.set(query, docs, retrieval_level, intent, top_k)
                return

            key = self._generate_key(query, intent, top_k)
            data = json.dumps({
                "docs": docs,
                "retrieval_level": retrieval_level,
                "timestamp": time.time()
            })

            await self._redis.setex(key, self.TTL_SECONDS, data)
            logger.debug(f"Redis cache set for key: {key[:16]}...")

        except redis.RedisError as e:
            logger.warning(f"Redis set failed, using fallback: {e}")
            await self._fallback_cache.set(query, docs, retrieval_level, intent, top_k)
        except Exception as e:
            logger.warning(f"Cache set error, using fallback: {e}")
            await self._fallback_cache.set(query, docs, retrieval_level, intent, top_k)

    async def invalidate(self, pattern: Optional[str] = None):
        """使缓存失效"""
        if self._use_fallback:
            await self._fallback_cache.invalidate(pattern)
            return

        try:
            if not self._redis:
                await self._fallback_cache.invalidate(pattern)
                return

            if pattern is None:
                cursor = 0
                count = 0
                while True:
                    cursor, keys = await self._redis.scan(cursor, match=f"{self.CACHE_PREFIX}*", count=100)
                    if keys:
                        await self._redis.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break
                logger.info(f"Redis cache cleared: {count} entries removed")
            else:
                logger.info(f"Pattern-based invalidation not fully supported in Redis mode")

        except redis.RedisError as e:
            logger.warning(f"Redis invalidate failed: {e}")
            await self._fallback_cache.invalidate(pattern)
        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")
            await self._fallback_cache.invalidate(pattern)

    async def get_stats(self) -> dict:
        """获取缓存统计"""
        if self._use_fallback or not self._redis:
            return await self._fallback_cache.get_stats()

        try:
            hits = int(await self._redis.get(self._get_stats_key("hits")) or 0)
            misses = int(await self._redis.get(self._get_stats_key("misses")) or 0)
            total = hits + misses
            hit_rate = hits / total if total > 0 else 0.0

            info = await self._redis.info("memory")
            used_memory = info.get("used_memory_human", "unknown")

            return {
                "size": await self._redis.dbsize(),
                "max_size": -1,
                "hits": hits,
                "misses": misses,
                "hit_rate": round(hit_rate * 100, 2),
                "evictions": -1,
                "backend": "redis",
                "used_memory": used_memory
            }

        except redis.RedisError as e:
            logger.warning(f"Redis stats failed, using fallback: {e}")
            return await self._fallback_cache.get_stats()
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return await self._fallback_cache.get_stats()

    async def cleanup_expired(self):
        """清理过期缓存 - Redis自动处理TTL"""
        pass

    async def close(self):
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis connections closed")


class RetrievalCacheService:
    """检索缓存服务"""

    def __init__(self):
        self._use_redis = os.getenv("USE_REDIS_CACHE", "true").lower() == "true"
        if self._use_redis:
            self.cache: Any = RedisCache()
            logger.info("Using Redis cache backend")
        else:
            self.cache = RetrievalCache(max_size=1000, ttl_seconds=3600)
            logger.info("Using in-memory cache backend")
        self._cleanup_task = None

    async def get_cached_result(self, query: str, intent: str = "legal", top_k: int = 5) -> Optional[list]:
        """获取缓存结果"""
        return await self.cache.get(query, intent, top_k)

    async def cache_result(
        self,
        query: str,
        docs: list,
        retrieval_level: str,
        intent: str = "legal",
        top_k: int = 5
    ):
        """缓存结果"""
        await self.cache.set(query, docs, retrieval_level, intent, top_k)

    async def invalidate(self, pattern: Optional[str] = None):
        """使缓存失效"""
        await self.cache.invalidate(pattern)

    async def get_stats(self) -> dict:
        """获取统计"""
        return await self.cache.get_stats()

    async def start_cleanup(self, interval_seconds: int = 600):
        """启动定期清理任务"""
        if self._use_redis:
            logger.info("Redis cache: TTL handled automatically, no cleanup task needed")
            return

        async def cleanup_loop():
            while True:
                await asyncio.sleep(interval_seconds)
                await self.cache.cleanup_expired()

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info(f"Cache cleanup task started, interval: {interval_seconds}s")

    async def stop_cleanup(self):
        """停止定期清理"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
            logger.info("Cache cleanup task stopped")

    async def close(self):
        """关闭缓存连接"""
        if self._use_redis and hasattr(self.cache, 'close'):
            await self.cache.close()


_retrieval_cache_service: Optional[RetrievalCacheService] = None


def get_retrieval_cache_service() -> RetrievalCacheService:
    global _retrieval_cache_service
    if _retrieval_cache_service is None:
        _retrieval_cache_service = RetrievalCacheService()
    return _retrieval_cache_service
