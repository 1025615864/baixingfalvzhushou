"""多级缓存服务

实现 L1(内存)、L2(Redis)、L3(数据库) 三级缓存架构。

L1 - 内存缓存：
  - 最快访问速度（纳秒级）
  - 单进程共享
  - 适合热点数据、配置信息
  - 使用 LRU 淘汰策略

L2 - Redis 缓存：
  - 快速访问（毫秒级）
  - 多进程/多实例共享
  - 适合会话、用户数据
  - 支持分布式锁

L3 - 数据库：
  - 持久化存储
  - 最终数据源
  - 适合冷数据
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .cache_service import cache_service

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheLevel(Enum):
    """缓存级别"""
    L1_MEMORY = "l1_memory"      # 内存缓存
    L2_REDIS = "l2_redis"        # Redis 缓存
    L3_DATABASE = "l3_database"  # 数据库


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0
    writes: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total * 100 if total > 0 else 0.0

    @property
    def l1_hit_rate(self) -> float:
        """L1 命中率"""
        total = self.l1_hits + self.l2_hits + self.l3_hits
        return self.l1_hits / total * 100 if total > 0 else 0.0

    @property
    def l2_hit_rate(self) -> float:
        """L2 命中率"""
        total = self.l1_hits + self.l2_hits + self.l3_hits
        return self.l2_hits / total * 100 if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "l1_hits": self.l1_hits,
            "l2_hits": self.l2_hits,
            "l3_hits": self.l3_hits,
            "writes": self.writes,
            "evictions": self.evictions,
            "hit_rate_percent": round(self.hit_rate, 2),
            "l1_hit_rate_percent": round(self.l1_hit_rate, 2),
            "l2_hit_rate_percent": round(self.l2_hit_rate, 2),
        }


@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""
    value: T
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def touch(self) -> None:
        """更新访问时间"""
        self.access_count += 1
        self.last_accessed = time.time()


class MemoryCache(Generic[T]):
    """L1 内存缓存实现

    使用 OrderedDict 实现 LRU 淘汰策略。
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 300,
    ):
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
        self._stats = CacheStats()

    async def get(self, key: str) -> T | None:
        """获取缓存"""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats.misses += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._stats.evictions += 1
                self._stats.misses += 1
                return None

            entry.touch()
            self._cache.move_to_end(key)
            self._stats.l1_hits += 1
            self._stats.hits += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: T,
        ttl: int | None = None,
    ) -> None:
        """设置缓存"""
        async with self._lock:
            expires_at = time.time() + (ttl or self._default_ttl)
            entry = CacheEntry(value=value, expires_at=expires_at)

            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._max_size:
                    # LRU 淘汰
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    self._stats.evictions += 1

            self._cache[key] = entry
            self._stats.writes += 1

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()

    async def keys(self) -> list[str]:
        """获取所有键"""
        async with self._lock:
            return list(self._cache.keys())

    async def size(self) -> int:
        """获取缓存大小"""
        async with self._lock:
            return len(self._cache)

    def get_stats(self) -> CacheStats:
        """获取统计信息"""
        return self._stats


class MultiLevelCache(Generic[T]):
    """多级缓存服务

    提供 L1(内存)、L2(Redis)、L3(数据库) 三级缓存。

    读取策略：
    1. 先查 L1，命中则返回
    2. L1 未命中查 L2，命中则回填 L1
    3. L2 未命中查 L3，命中则回填 L1+L2

    写入策略：
    1. 同时写入 L1 和 L2
    2. L3 作为数据源，不主动写入

    删除策略：
    1. 同时删除 L1 和 L2
    """

    def __init__(
        self,
        l1_max_size: int = 1000,
        l1_default_ttl: int = 60,
        l2_default_ttl: int = 300,
        name: str = "default",
    ):
        self._l1_cache = MemoryCache(max_size=l1_max_size, default_ttl=l1_default_ttl)
        self._name = name
        self._l2_default_ttl = l2_default_ttl
        self._stats = CacheStats()

    async def get(
        self,
        key: str,
        loader: Callable[[], Any] | None = None,
        db: AsyncSession | None = None,
        model: Any | None = None,
        ttl: int | None = None,
    ) -> T | None:
        """获取缓存数据

        Args:
            key: 缓存键
            loader: 数据加载函数（L2 未命中时使用）
            db: 数据库会话（L3 查询使用）
            model: SQLAlchemy 模型（L3 查询使用）
            ttl: 过期时间

        Returns:
            缓存数据，不存在则返回 None
        """
        # 1. 尝试 L1 内存缓存
        l1_result = await self._l1_cache.get(key)
        if l1_result is not None:
            logger.debug(f"[{self._name}] L1 cache hit: {key}")
            return l1_result

        # 2. 尝试 L2 Redis 缓存
        l2_result = await self._get_l2(key)
        if l2_result is not None:
            logger.debug(f"[{self._name}] L2 cache hit: {key}")
            # 回填 L1
            await self._l1_cache.set(key, l2_result, ttl)
            self._stats.l2_hits += 1
            self._stats.hits += 1
            return l2_result

        # 3. 尝试 L3 数据库
        if db is not None and model is not None:
            l3_result = await self._get_l3(db, model, key)
            if l3_result is not None:
                logger.debug(f"[{self._name}] L3 cache hit: {key}")
                # 回填 L1 和 L2
                await self._l1_cache.set(key, l3_result, ttl)
                await self._set_l2(key, l3_result, ttl)
                self._stats.l3_hits += 1
                self._stats.hits += 1
                return l3_result

        # 4. 使用 loader 加载数据
        if loader is not None:
            try:
                result = await loader()
                if result is not None:
                    await self._l1_cache.set(key, result, ttl)
                    await self._set_l2(key, result, ttl)
                    self._stats.writes += 1
                self._stats.misses += 1
                return result
            except Exception as e:
                logger.error(f"[{self._name}] Loader error: {e}")
                self._stats.misses += 1
                return None

        self._stats.misses += 1
        return None

    async def set(
        self,
        key: str,
        value: T,
        ttl: int | None = None,
        write_through: bool = True,
    ) -> None:
        """设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间
            write_through: 是否同时写入 L1 和 L2
        """
        if write_through:
            # 同时写入 L1 和 L2
            await asyncio.gather(
                self._l1_cache.set(key, value, ttl),
                self._set_l2(key, value, ttl),
                return_exceptions=True,
            )
        else:
            # 仅写入 L1
            await self._l1_cache.set(key, value, ttl)

        self._stats.writes += 1

    async def delete(self, key: str) -> None:
        """删除缓存"""
        await asyncio.gather(
            self._l1_cache.delete(key),
            self._delete_l2(key),
            return_exceptions=True,
        )

    async def clear(self) -> None:
        """清空缓存"""
        await asyncio.gather(
            self._l1_cache.clear(),
            self._clear_l2(),
            return_exceptions=True,
        )

    async def _get_l2(self, key: str) -> T | None:
        """从 L2 Redis 获取"""
        try:
            result = await cache_service.get_json(key)
            return result  # type: ignore[return-value]
        except Exception as e:
            logger.debug(f"[{self._name}] L2 get error: {e}")
            return None

    async def _set_l2(self, key: str, value: T, ttl: int | None = None) -> None:
        """设置 L2 Redis"""
        try:
            await cache_service.set_json(key, value, ttl or self._l2_default_ttl)
        except Exception as e:
            logger.debug(f"[{self._name}] L2 set error: {e}")

    async def _delete_l2(self, key: str) -> None:
        """删除 L2 Redis"""
        try:
            await cache_service.delete(key)
        except Exception as e:
            logger.debug(f"[{self._name}] L2 delete error: {e}")

    async def _clear_l2(self) -> None:
        """清空 L2 Redis"""
        try:
            # 清空所有匹配前缀的键
            pattern = f"{self._name}:*"
            await cache_service.clear_pattern(pattern)
        except Exception as e:
            logger.debug(f"[{self._name}] L2 clear error: {e}")

    async def _get_l3(
        self,
        db: AsyncSession,
        model: Any,
        key: str,
    ) -> T | None:
        """从 L3 数据库获取"""
        try:
            # 尝试从键中解析 ID
            parts = key.split(":")
            if parts and parts[-1].isdigit():
                item_id = int(parts[-1])
                result = await db.get(model, item_id)
                if result:
                    # 转换为字典
                    if hasattr(result, "__dict__"):
                        data = {
                            k: v for k, v in result.__dict__.items()
                            if not k.startswith("_")
                        }
                        return data  # type: ignore[return-value]
        except Exception as e:
            logger.debug(f"[{self._name}] L3 get error: {e}")
        return None

    def get_stats(self) -> CacheStats:
        """获取统计信息"""
        l1_stats = self._l1_cache.get_stats()
        return CacheStats(
            hits=self._stats.hits,
            misses=self._stats.misses,
            l1_hits=l1_stats.l1_hits,
            l2_hits=self._stats.l2_hits,
            l3_hits=self._stats.l3_hits,
            writes=self._stats.writes,
            evictions=l1_stats.evictions,
        )


class CacheManager:
    """缓存管理器

    管理多个多级缓存实例，提供统一的访问接口。
    """

    def __init__(self):
        self._caches: dict[str, MultiLevelCache[Any]] = {}
        self._global_stats = CacheStats()

    def get_cache(
        self,
        name: str,
        l1_max_size: int = 1000,
        l1_default_ttl: int = 60,
        l2_default_ttl: int = 300,
    ) -> MultiLevelCache[Any]:
        """获取或创建缓存实例

        Args:
            name: 缓存名称
            l1_max_size: L1 最大大小
            l1_default_ttl: L1 默认过期时间
            l2_default_ttl: L2 默认过期时间

        Returns:
            缓存实例
        """
        if name not in self._caches:
            self._caches[name] = MultiLevelCache(
                l1_max_size=l1_max_size,
                l1_default_ttl=l1_default_ttl,
                l2_default_ttl=l2_default_ttl,
                name=name,
            )
        return self._caches[name]

    def get_all_stats(self) -> dict[str, Any]:
        """获取所有缓存的统计信息"""
        stats = {}
        total_hits = 0
        total_misses = 0

        for name, cache in self._caches.items():
            cache_stats = cache.get_stats()
            stats[name] = cache_stats.to_dict()
            total_hits += cache_stats.hits
            total_misses += cache_stats.misses

        stats["_total"] = {
            "hits": total_hits,
            "misses": total_misses,
            "hit_rate_percent": round(
                total_hits / (total_hits + total_misses) * 100
                if (total_hits + total_misses) > 0 else 0, 2
            ),
        }

        return stats


def make_cache_key(prefix: str, *parts: Any) -> str:
    """生成缓存键

    Args:
        prefix: 前缀
        *parts: 键组成部分

    Returns:
        缓存键字符串
    """
    key_parts = [prefix]
    for part in parts:
        if isinstance(part, (dict, list)):
            # 复杂类型使用哈希
            key_str = json.dumps(part, sort_keys=True, ensure_ascii=False)
            key_parts.append(hashlib.md5(key_str.encode()).hexdigest()[:12])
        else:
            key_parts.append(str(part))
    return ":".join(key_parts)


# 全局缓存管理器
cache_manager = CacheManager()


# 预定义的缓存实例
def get_recommendation_cache() -> MultiLevelCache[Any]:
    """获取推荐缓存"""
    return cache_manager.get_cache(
        "recommendation",
        l1_max_size=500,
        l1_default_ttl=30,
        l2_default_ttl=120,
    )


def get_news_cache() -> MultiLevelCache[Any]:
    """获取新闻缓存"""
    return cache_manager.get_cache(
        "news",
        l1_max_size=1000,
        l1_default_ttl=60,
        l2_default_ttl=300,
    )


def get_knowledge_cache() -> MultiLevelCache[Any]:
    """获取知识库缓存"""
    return cache_manager.get_cache(
        "knowledge",
        l1_max_size=500,
        l1_default_ttl=120,
        l2_default_ttl=600,
    )


def get_user_cache() -> MultiLevelCache[Any]:
    """获取用户数据缓存"""
    return cache_manager.get_cache(
        "user",
        l1_max_size=2000,
        l1_default_ttl=60,
        l2_default_ttl=300,
    )


def get_config_cache() -> MultiLevelCache[Any]:
    """获取配置缓存"""
    return cache_manager.get_cache(
        "config",
        l1_max_size=100,
        l1_default_ttl=300,
        l2_default_ttl=3600,
    )