"""Redis 缓存策略优化工具

提供热点数据预热、缓存击穿防护和缓存过期策略。
"""
import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

# 热点数据配置
HOT_KEYS: dict[str, dict[str, Any]] = {
    "news_list": {
        "expire": 300,  # 5分钟
        "preload": True,
        "refresh_interval": 60,  # 1分钟刷新一次
    },
    "lawyer_list": {
        "expire": 600,  # 10分钟
        "preload": True,
        "refresh_interval": 120,
    },
    "config_global": {
        "expire": 3600,  # 1小时
        "preload": True,
        "refresh_interval": 300,
    },
}

# 缓存击穿防护锁
_lock_cache: dict[str, tuple[str, float]] = {}


class CacheBreachProtection:
    """缓存击穿防护"""

    @staticmethod
    async def acquire_lock(
        lock_key: str,
        lock_value: str,
        expire: int = 10,
    ) -> bool:
        """获取分布式锁（防止缓存击穿）"""
        success = await cache_service.setnx(lock_key, lock_value, expire)
        if success:
            logger.debug(f"Lock acquired: {lock_key}")
        return success

    @staticmethod
    async def release_lock(lock_key: str, lock_value: str) -> bool:
        """释放分布式锁"""
        success = await cache_service.release_lock(lock_key, lock_value)
        if success:
            logger.debug(f"Lock released: {lock_key}")
        return success

    @staticmethod
    async def execute_with_lock(
        lock_key: str,
        lock_value: str,
        expire: int = 10,
        retry_times: int = 3,
        retry_interval: float = 0.1,
    ) -> Callable[[Callable[[], Awaitable[Any]]], Awaitable[Any]]:
        """使用锁执行操作的装饰器

        Usage:
            async with CacheBreachProtection.execute_with_lock("my_lock", "token"):
                # 获取缓存或从数据库加载
                result = await get_data_from_db()
                await cache_service.set_json("key", result, expire)
        """
        async def decorator(func: Callable[[], Awaitable[Any]]) -> Any:
            for i in range(retry_times):
                if await CacheBreachProtection.acquire_lock(lock_key, lock_value, expire):
                    try:
                        return await func()
                    finally:
                        await CacheBreachProtection.release_lock(lock_key, lock_value)
                else:
                    if i < retry_times - 1:
                        await asyncio.sleep(retry_interval)
            raise RuntimeError(
                f"Failed to acquire lock after {retry_times} retries")
        return decorator


class CachePreloader:
    """缓存预热器"""

    def __init__(self):
        self._preloading: set[str] = set()
        self._refresh_tasks: dict[str, asyncio.Task[None]] = {}

    async def preload(
        self,
        key: str,
        loader: Callable[[], Awaitable[Any]],
        expire: int = 300,
    ) -> Any:
        """预热缓存

        Args:
            key: 缓存键
            loader: 数据加载函数
            expire: 过期时间（秒）
        """
        # 检查是否已有缓存
        cached = await cache_service.get_json(key)
        if cached is not None:
            return cached

        # 检查是否正在预热
        if key in self._preloading:
            # 等待预热完成
            for _ in range(50):  # 最多等待5秒
                await asyncio.sleep(0.1)
                cached = await cache_service.get_json(key)
                if cached is not None:
                    return cached
            raise RuntimeError(f"Preload timeout for key: {key}")

        # 开始预热
        self._preloading.add(key)
        try:
            logger.info(f"Preloading cache: {key}")
            result = await loader()
            if result is not None:
                await cache_service.set_json(key, result, expire)
            return result
        finally:
            self._preloading.discard(key)

    async def preload_hot_keys(
        self,
        keys: list[str],
        loader: Callable[[str], Awaitable[Any]],
        expire: int = 300,
    ) -> dict[str, Any]:
        """批量预热热点数据

        Args:
            keys: 缓存键列表
            loader: 数据加载函数（接收 key）
            expire: 过期时间（秒）
        """
        results: dict[str, Any] = {}

        async def load_and_cache(key: str) -> tuple[str, Any]:
            result = await loader(key)
            if result is not None:
                await cache_service.set_json(key, result, expire)
            return key, result

        tasks = [load_and_cache(key) for key in keys]
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for item in completed:
            if isinstance(item, tuple):
                results[item[0]] = item[1]

        logger.info(f"Preloaded {len(results)} hot keys")
        return results

    async def start_background_refresh(
        self,
        key: str,
        loader: Callable[[], Awaitable[Any]],
        interval: int = 60,
        expire: int = 300,
    ) -> None:
        """启动后台定时刷新

        Args:
            key: 缓存键
            loader: 数据加载函数
            interval: 刷新间隔（秒）
            expire: 缓存过期时间
        """
        if key in self._refresh_tasks:
            logger.warning(f"Refresh task already exists for key: {key}")
            return

        async def refresh_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    result = await loader()
                    if result is not None:
                        await cache_service.set_json(key, result, expire)
                        logger.debug(f"Background refresh: {key}")
                except asyncio.CancelledError:
                    logger.info(f"Background refresh stopped: {key}")
                    break
                except Exception as e:
                    logger.error(f"Background refresh error: {e}")

        task = asyncio.create_task(refresh_loop())
        self._refresh_tasks[key] = task
        logger.info(f"Started background refresh for key: {key}")

    async def stop_background_refresh(self, key: str) -> None:
        """停止后台定时刷新"""
        task = self._refresh_tasks.get(key)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._refresh_tasks[key]
            logger.info(f"Stopped background refresh: {key}")


class CacheStrategy:
    """缓存策略管理器"""

    def __init__(self):
        self.preloader = CachePreloader()
        self._stats: dict[str, dict[str, Any]] = {}

    async def get_or_load(
        self,
        key: str,
        loader: Callable[[], Awaitable[Any]],
        expire: int = 300,
        use_lock: bool = True,
    ) -> Any:
        """获取缓存或加载数据（带击穿防护）

        Args:
            key: 缓存键
            loader: 数据加载函数
            expire: 过期时间
            use_lock: 是否使用锁防护
        """
        start_time = time.time()

        # 尝试从缓存获取
        cached = await cache_service.get_json(key)
        if cached is not None:
            self._record_hit(key, start_time)
            return cached

        # 缓存未命中
        self._record_miss(key, start_time)

        if not use_lock:
            return await self.preloader.preload(key, loader, expire)

        # 使用锁防护
        lock_key = f"lock:{key}"
        lock_value = f"{time.time()}:{id(loader)}"

        try:
            if await CacheBreachProtection.acquire_lock(lock_key, lock_value, 10):
                try:
                    # 双重检查
                    cached = await cache_service.get_json(key)
                    if cached is not None:
                        return cached

                    return await self.preloader.preload(key, loader, expire)
                finally:
                    await CacheBreachProtection.release_lock(lock_key, lock_value)
            else:
                # 锁获取失败，等待后重试
                await asyncio.sleep(0.05)
                return await self.get_or_load(key, loader, expire, use_lock=False)
        except Exception as e:
            logger.error(f"Cache get_or_load error: {e}")
            return await loader()

    async def invalidate_pattern(self, pattern: str) -> int:
        """按模式失效缓存

        Args:
            pattern: 匹配模式（如 "user:*"）

        Returns:
            失效的键数量
        """
        count = await cache_service.clear_pattern(pattern)
        logger.info(f"Invalidated {count} keys matching pattern: {pattern}")
        return count

    def _record_hit(self, key: str, start_time: float) -> None:
        """记录缓存命中"""
        if key not in self._stats:
            self._stats[key] = {"hits": 0, "misses": 0, "total_time": 0.0}
        self._stats[key]["hits"] += 1
        self._stats[key]["total_time"] += time.time() - start_time

    def _record_miss(self, key: str, start_time: float) -> None:
        """记录缓存未命中"""
        if key not in self._stats:
            self._stats[key] = {"hits": 0, "misses": 0, "total_time": 0.0}
        self._stats[key]["misses"] += 1

    def get_stats(self) -> dict[str, dict[str, Any]]:
        """获取缓存统计"""
        stats = {}
        for key, data in self._stats.items():
            total = data["hits"] + data["misses"]
            hit_rate = (data["hits"] / total * 100) if total > 0 else 0
            avg_time = (data["total_time"] / total * 1000) if total > 0 else 0
            stats[key] = {
                "hits": data["hits"],
                "misses": data["misses"],
                "hit_rate": f"{hit_rate:.2f}%",
                "avg_time_ms": f"{avg_time:.2f}",
            }
        return stats


# 单例实例
cache_strategy = CacheStrategy()


def cached_with_strategy(
    key_prefix: str,
    expire: int = 300,
    use_lock: bool = True,
):
    """带策略的缓存装饰器

    Usage:
        @cached_with_strategy("user_info", expire=600, use_lock=True)
        async def get_user_info(user_id: int) -> dict:
            ...
    """
    def decorator(func: Callable[..., Awaitable[Any]]
                  ) -> Callable[..., Awaitable[Any]]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 生成缓存键
            key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"
            return await cache_strategy.get_or_load(key, lambda: func(*args, **kwargs), expire, use_lock)
        return wrapper
    return decorator


async def preload_hot_data(
    data_type: str,
    loader: Callable[[], Awaitable[list[tuple[str, Any]]]],
) -> int:
    """预热热点数据

    Args:
        data_type: 数据类型（如 "news"、"lawyer"）
        loader: 加载函数，返回 (key, value) 列表

    Returns:
        预热的数量
    """
    config = HOT_KEYS.get(data_type)
    if not config:
        logger.warning(f"Unknown hot data type: {data_type}")
        return 0

    try:
        items = await loader()
        count = 0
        for key, value in items:
            await cache_service.set_json(key, value, config["expire"])
            count += 1

        logger.info(f"Preloaded {count} {data_type} items")
        return count
    except Exception as e:
        logger.error(f"Preload hot data error: {e}")
        return 0


async def get_cache_hit_rate() -> dict[str, float]:
    """获取缓存命中率

    Returns:
        全局命中率统计
    """
    stats = cache_strategy.get_stats()
    total_hits = 0
    total_requests = 0

    for data in stats.values():
        total_hits += data.get("hits", 0)
        total_requests += data.get("hits", 0) + data.get("misses", 0)

    hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
    return {
        "hit_rate": hit_rate,
        "total_requests": total_requests,
        "total_hits": total_hits,
    }
