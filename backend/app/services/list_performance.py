"""列表性能优化服务

提供 News/Forum/Notifications 列表性能优化功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class ListCacheManager:
    """列表缓存管理器"""

    def __init__(self):
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_ttl = 300

    def get_cache_key(self, list_type: str, user_id: int |
                      None, params: dict[str, Any]) -> str:
        """生成缓存键

        Args:
            list_type: 列表类型
            user_id: 用户ID
            params: 参数

        Returns:
            缓存键
        """
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{list_type}:{user_id}:{hash(param_str)}"

    def get(self, cache_key: str) -> dict[str, Any] | None:
        """获取缓存

        Args:
            cache_key: 缓存键

        Returns:
            缓存数据
        """
        if cache_key not in self._cache:
            return None

        cached = self._cache[cache_key]
        if cached["expires_at"] < datetime.now(timezone.utc).timestamp():
            del self._cache[cache_key]
            return None

        cached["hit"] = True
        return cached["data"]

    def set(
        self,
        cache_key: str,
        data: list[Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """设置缓存

        Args:
            cache_key: 缓存键
            data: 数据
            metadata: 元数据

        Returns:
            缓存结果
        """
        self._cache[cache_key] = {
            "data": data, "metadata": metadata, "created_at": datetime.now(
                timezone.utc).isoformat(), "expires_at": datetime.now(
                timezone.utc).timestamp() + self._cache_ttl, "hit": False, }

        return {
            "cached": True,
            "cache_key": cache_key,
        }

    def invalidate(self, list_type: str) -> int:
        """使缓存失效

        Args:
            list_type: 列表类型

        Returns:
            失效数量
        """
        keys_to_delete = [k for k in self._cache if k.startswith(list_type)]
        count = len(keys_to_delete)
        for key in keys_to_delete:
            del self._cache[key]

        return count

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计

        Returns:
            统计信息
        """
        total = len(self._cache)
        hits = sum(1 for c in self._cache.values() if c.get("hit", False))

        return {
            "total_keys": total,
            "hit_count": hits,
            "hit_rate": round(hits / max(total, 1) * 100, 2),
        }


class QueryOptimizer:
    """查询优化器"""

    def __init__(self):
        self._metrics: dict[str, list[dict[str, Any]]] = {}

    def optimize_query(
        self,
        query_type: str,
        original_params: dict[str, Any],
    ) -> dict[str, Any]:
        """优化查询

        Args:
            query_type: 查询类型
            original_params: 原始参数

        Returns:
            优化后的查询参数
        """
        optimized = original_params.copy()

        if "page" not in optimized:
            optimized["page"] = 1
        if "page_size" not in optimized:
            optimized["page_size"] = 20

        optimized["page_size"] = min(max(optimized["page_size"], 1), 100)

        if optimized.get("page") > 1 and optimized.get("page_size") == 100:
            optimized["page_size"] = 50

        return optimized

    def record_query_time(
        self,
        query_type: str,
        duration_ms: float,
        result_count: int,
    ) -> None:
        """记录查询时间

        Args:
            query_type: 查询类型
            duration_ms: 耗时毫秒
            result_count: 结果数量
        """
        if query_type not in self._metrics:
            self._metrics[query_type] = []

        self._metrics[query_type].append({
            "duration_ms": duration_ms,
            "result_count": result_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        if len(self._metrics[query_type]) > 1000:
            self._metrics[query_type] = self._metrics[query_type][-1000:]

    def get_query_stats(self, query_type: str) -> dict[str, Any]:
        """获取查询统计

        Args:
            query_type: 查询类型

        Returns:
            统计信息
        """
        metrics = self._metrics.get(query_type, [])
        if not metrics:
            return {
                "query_type": query_type,
                "count": 0,
                "avg_duration_ms": 0,
                "p95_duration_ms": 0,
            }

        durations = [m["duration_ms"] for m in metrics]
        durations.sort()

        p95_idx = int(len(durations) * 0.95)

        return {
            "query_type": query_type,
            "count": len(metrics),
            "avg_duration_ms": round(
                sum(durations) /
                len(durations),
                2),
            "p95_duration_ms": round(
                durations[p95_idx],
                2) if durations else 0,
            "max_duration_ms": round(
                max(durations),
                2) if durations else 0,
        }


class ListPerformanceService:
    """列表性能服务"""

    def __init__(self):
        self._cache = ListCacheManager()
        self._optimizer = QueryOptimizer()

    async def get_optimized_list(
        self,
        list_type: str,
        user_id: int | None,
        params: dict[str, Any],
        fetch_func,
    ) -> dict[str, Any]:
        """获取优化后的列表

        Args:
            list_type: 列表类型
            user_id: 用户ID
            params: 参数
            fetch_func: 获取函数

        Returns:
            列表数据
        """
        optimized_params = self._optimizer.optimize_query(list_type, params)
        cache_key = self._cache.get_cache_key(
            list_type, user_id, optimized_params)

        cached_data = self._cache.get(cache_key)
        if cached_data is not None:
            # cached_data is just the raw list data from .get()
            # But wait, ListCacheManager.get returns cached["data"].
            # To reconstruct the full response structure including metadata if needed,
            # we might need more from the cache if we want to return it.
            # However, this method returns dict[str, Any].
            # If cached_data is a list (e.g. news items), we can wrap it.

            return {
                "data": cached_data,
                "from_cache": True,
            }

        start_time = datetime.now(timezone.utc).timestamp()
        data = await fetch_func(optimized_params)
        duration_ms = (
            datetime.now(
                timezone.utc).timestamp() - start_time) * 1000

        self._optimizer.record_query_time(
            query_type=list_type,
            duration_ms=duration_ms,
            result_count=len(data) if isinstance(data, list) else 0,
        )

        self._cache.set(cache_key, data, {"duration_ms": duration_ms})

        return {
            "data": data,
            "from_cache": False,
            "performance": {
                "duration_ms": round(duration_ms, 2),
                "optimized_params": optimized_params,
            },
        }

    async def invalidate_cache(self, list_type: str) -> dict[str, Any]:
        """使缓存失效

        Args:
            list_type: 列表类型

        Returns:
            失效结果
        """
        count = self._cache.invalidate(list_type)
        return {
            "list_type": list_type,
            "invalidated": count,
        }

    async def get_performance_stats(self) -> dict[str, Any]:
        """获取性能统计

        Returns:
            统计信息
        """
        cache_stats = self._cache.get_stats()

        query_types = ["news", "forum", "notifications"]
        query_stats = {}
        for qt in query_types:
            query_stats[qt] = self._optimizer.get_query_stats(qt)

        return {
            "cache": cache_stats,
            "queries": query_stats,
        }


# 单例实例
list_performance_service = ListPerformanceService()


async def get_optimized_list(
    list_type: str,
    user_id: int | None,
    params: dict[str, Any],
    fetch_func,
) -> dict[str, Any]:
    """便捷函数：获取优化后的列表

    Args:
        list_type: 列表类型
        user_id: 用户ID
        params: 参数
        fetch_func: 获取函数

    Returns:
        列表数据
    """
    return await list_performance_service.get_optimized_list(
        list_type=list_type,
        user_id=user_id,
        params=params,
        fetch_func=fetch_func,
    )
