"""Sitemap缓存服务

提供SitemapXML的缓存功能，减少数据库查询频率。

功能特性:
    - Redis缓存存储
    - 定时自动刷新
    - 缓存失效自动重建
    - 内存缓存降级

使用示例:
    ```python
    from app.services.sitemap_cache import get_sitemap_cache, SitemapType

    cache = get_sitemap_cache()

    # 获取缓存的sitemap
    xml_content = await cache.get_sitemap(SitemapType.NEWS)

    # 手动刷新sitemap
    await cache.refresh_sitemap(SitemapType.NEWS)

    # 获取所有sitemap统计信息
    stats = cache.get_stats()
    ```
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .cache_service import CacheService, get_cache_service

logger = logging.getLogger("sitemap")

CACHE_KEY_PREFIX = "sitemap"
CACHE_TTL = 3600  # 1小时


class SitemapType(str, Enum):
    """Sitemap类型"""

    NEWS = "news"
    FORUM = "forum"
    KNOWLEDGE = "knowledge"
    DOCUMENT = "document"
    ALL = "all"


@dataclass
class SitemapCacheEntry:
    """Sitemap缓存条目"""

    xml_content: str
    last_updated: float
    item_count: int
    cache_time: float = field(default_factory=time.time)


class SitemapCacheService:
    """Sitemap缓存服务

    提供Sitemap的缓存管理和自动刷新功能。

    Attributes:
        cache: 缓存服务实例
        refresh_interval: 自动刷新间隔（秒）
        _refresh_task: 后台刷新任务
    """

    def __init__(
        self,
        cache: Optional[CacheService] = None,
        refresh_interval: int = 1800,  # 30分钟
    ) -> None:
        self.cache = cache or get_cache_service()
        self.refresh_interval = refresh_interval
        self._refresh_task: Optional[asyncio.Task[None]] = None
        self._refresh_locks: dict[SitemapType, asyncio.Lock] = {}
        self._last_build_time: dict[SitemapType, float] = {}

        for sitemap_type in SitemapType:
            self._refresh_locks[sitemap_type] = asyncio.Lock()

    def _get_cache_key(self, sitemap_type: SitemapType) -> str:
        """获取缓存键

        Args:
            sitemap_type: Sitemap类型

        Returns:
            缓存键字符串
        """
        return f"{CACHE_KEY_PREFIX}:{sitemap_type.value}"

    async def get_sitemap(self, sitemap_type: SitemapType) -> Optional[str]:
        """获取Sitemap内容

        优先从缓存获取，如果缓存不存在或已过期则返回None。

        Args:
            sitemap_type: Sitemap类型

        Returns:
            Sitemap XML内容，如果缓存不存在则返回None
        """
        cache_key = self._get_cache_key(sitemap_type)
        cached = await self.cache.get(cache_key)

        if cached and isinstance(cached, str):
            logger.debug(f"Sitemap {sitemap_type.value} cache hit")
            return cached

        logger.debug(f"Sitemap {sitemap_type.value} cache miss")
        return None

    async def set_sitemap(
        self,
        sitemap_type: SitemapType,
        xml_content: str,
        item_count: int = 0,
    ) -> None:
        """设置Sitemap缓存

        Args:
            sitemap_type: Sitemap类型
            xml_content: Sitemap XML内容
            item_count: 链接数量
        """
        cache_key = self._get_cache_key(sitemap_type)
        await self.cache.set(cache_key, xml_content, ttl=CACHE_TTL)
        self._last_build_time[sitemap_type] = time.time()
        logger.info(
            f"Sitemap {sitemap_type.value} cached, "
            f"items={item_count}, ttl={CACHE_TTL}s"
        )

    async def invalidate(self, sitemap_type: SitemapType) -> None:
        """使Sitemap缓存失效

        Args:
            sitemap_type: Sitemap类型
        """
        cache_key = self._get_cache_key(sitemap_type)
        await self.cache.delete(cache_key)
        self._last_build_time.pop(sitemap_type, None)
        logger.info(f"Sitemap {sitemap_type.value} cache invalidated")

    async def refresh_sitemap(
        self,
        sitemap_type: SitemapType,
        builder_func=None,
    ) -> Optional[str]:
        """刷新Sitemap缓存

        如果缓存不存在或已过期，重新构建Sitemap。

        Args:
            sitemap_type: Sitemap类型
            builder_func: 可选的构建函数，接收sitemap_type返回XML内容

        Returns:
            Sitemap XML内容
        """
        async with self._refresh_locks[sitemap_type]:
            existing = await self.get_sitemap(sitemap_type)
            if existing:
                return existing

            if builder_func:
                xml_content = await builder_func(sitemap_type)
                if xml_content:
                    await self.set_sitemap(
                        sitemap_type, xml_content, item_count=0
                    )
                    return xml_content

            logger.warning(
                f"No builder function for sitemap type: {sitemap_type.value}"
            )
            return None

    async def start_auto_refresh(self) -> None:
        """启动自动刷新任务"""
        if self._refresh_task is not None:
            return

        self._refresh_task = asyncio.create_task(self._auto_refresh_loop())
        logger.info(f"Sitemap auto-refresh started, interval={self.refresh_interval}s")

    async def stop_auto_refresh(self) -> None:
        """停止自动刷新任务"""
        if self._refresh_task is None:
            return

        self._refresh_task.cancel()
        try:
            await self._refresh_task
        except asyncio.CancelledError:
            pass

        self._refresh_task = None
        logger.info("Sitemap auto-refresh stopped")

    async def _auto_refresh_loop(self) -> None:
        """自动刷新循环"""
        while True:
            try:
                await asyncio.sleep(self.refresh_interval)
                logger.debug("Running scheduled sitemap refresh")

                for sitemap_type in SitemapType:
                    if sitemap_type == SitemapType.ALL:
                        continue

                    try:
                        await self.refresh_sitemap(sitemap_type)
                    except Exception as e:
                        logger.exception(
                            f"Failed to refresh sitemap {sitemap_type.value}: {e}"
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Sitemap refresh loop error: {e}")

    def get_stats(self) -> dict[str, any]:
        """获取缓存统计信息

        Returns:
            统计信息字典
        """
        return {
            "refresh_interval": self.refresh_interval,
            "auto_refresh_active": self._refresh_task is not None,
            "last_build_times": {
                k.value: v for k, v in self._last_build_time.items()
            },
            "cache_ttl": CACHE_TTL,
        }


_sitemap_cache_service: Optional[SitemapCacheService] = None


def get_sitemap_cache() -> SitemapCacheService:
    """获取Sitemap缓存服务单例

    Returns:
        SitemapCacheService实例
    """
    global _sitemap_cache_service

    if _sitemap_cache_service is None:
        _sitemap_cache_service = SitemapCacheService()

    return _sitemap_cache_service


async def init_sitemap_cache() -> None:
    """初始化Sitemap缓存服务

    在应用启动时调用，启动自动刷新任务。
    """
    cache = get_sitemap_cache()
    await cache.start_auto_refresh()
    logger.info("Sitemap cache service initialized")
