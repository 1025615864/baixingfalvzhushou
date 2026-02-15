"""缓存优化工具

实现缓存预热、穿透保护、雪崩保护。
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Optional

from app.services.cache_service import cache_service


class CacheOptimizer:
    """缓存优化器"""

    def __init__(self) -> None:
        self.cache_stats: dict[str, dict[str, Any]] = {}

    async def get_with_fallback(
        self,
        key: str,
        fallback_func: callable,
        ttl: int = 3600,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """获取缓存，如果不存在则使用回退函数

        Args:
            key: 缓存键
            fallback_func: 回退函数
            ttl: 过期时间（秒）
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            缓存值或回退函数结果
        """
        # 尝试从缓存获取
        cached = await cache_service.get(key)
        if cached is not None:
            # 更新统计
            if key not in self.cache_stats:
                self.cache_stats[key] = {
                    "hits": 0,
                    "misses": 0,
                    "total": 0,
                }
            self.cache_stats[key]["hits"] += 1
            self.cache_stats[key]["total"] += 1

            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return cached

        # 缓存未命中，执行回退函数
        result = await fallback_func(*args, **kwargs)

        # 存入缓存
        try:
            await cache_service.set(key, json.dumps(result), ttl)
        except Exception:
            pass

        # 更新统计
        if key not in self.cache_stats:
            self.cache_stats[key] = {
                "hits": 0,
                "misses": 0,
                "total": 0,
            }
        self.cache_stats[key]["misses"] += 1
        self.cache_stats[key]["total"] += 1

        return result

    async def get_cache_stats(self) -> dict[str, dict[str, Any]]:
        """获取缓存统计

        Returns:
            缓存统计信息
        """
        total_hits = sum(s["hits"] for s in self.cache_stats.values())
        total_misses = sum(s["misses"] for s in self.cache_stats.values())
        total_requests = total_hits + total_misses

        return {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_requests": total_requests,
            "hit_rate": total_hits / total_requests if total_requests > 0 else 0.0,
            "miss_rate": total_misses / total_requests if total_requests > 0 else 0.0,
            "key_stats": dict(self.cache_stats),
        }

    async def warm_up_cache(
        self,
        warm_up_func: callable,
        keys: list[str],
        ttl: int = 3600
    ) -> dict[str, Any]:
        """缓存预热

        Args:
            warm_up_func: 预热函数
            keys: 缓存键列表
            ttl: 过期时间（秒）

        Returns:
            预热结果
        """
        results = {}

        for key in keys:
            try:
                value = await warm_up_func(key)
                await cache_service.set(key, json.dumps(value), ttl)
                results[key] = {"status": "success", "value": value}
            except Exception as e:
                results[key] = {"status": "error", "error": str(e)}

        return results


class CacheProtection:
    """缓存保护（防止穿透和雪崩）"""

    def __init__(self) -> None:
        self.null_cache_ttl = 60  # 空值缓存60秒
        self.lock_timeout = 10  # 锁超时10秒

    async def get_with_protection(
        self,
        key: str,
        fallback_func: callable,
        ttl: int = 3600,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """获取缓存（带保护）

        Args:
            key: 缓存键
            fallback_func: 回退函数
            ttl: 过期时间（秒）
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            缓存值或回退函数结果
        """
        # 尝试从缓存获取
        cached = await cache_service.get(key)
        if cached is not None:
            if cached == "NULL":  # 空值缓存
                return None
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return cached

        # 使用分布式锁防止缓存雪崩
        lock_key = f"lock:{key}"
        lock_acquired = await cache_service.set(
            lock_key,
            "1",
            ex=self.lock_timeout,
            nx=True
        )

        if lock_acquired:
            # 获取锁成功，执行回退函数
            try:
                result = await fallback_func(*args, **kwargs)

                # 存入缓存
                if result is None:
                    # 空值缓存（防止缓存穿透）
                    await cache_service.set(key, "NULL", self.null_cache_ttl)
                else:
                    await cache_service.set(key, json.dumps(result), ttl)

                return result
            finally:
                # 释放锁
                await cache_service.delete(lock_key)
        else:
            # 未获取到锁，等待并重试
            await asyncio.sleep(0.1)
            return await self.get_with_protection(
                key, fallback_func, ttl, *args, **kwargs
            )


# 全局缓存优化器
cache_optimizer = CacheOptimizer()
cache_protection = CacheProtection()


async def optimize_cache_hit_rate() -> dict[str, Any]:
    """优化缓存命中率

    Returns:
        优化建议
    """
    stats = await cache_optimizer.get_cache_stats()
    hit_rate = stats["hit_rate"]

    suggestions = []

    if hit_rate < 0.5:
        suggestions.append({
            "issue": "缓存命中率过低",
            "current_rate": f"{hit_rate:.2%}",
            "target_rate": ">80%",
            "suggestion": "增加缓存预热，优化缓存键设计",
        })

    if hit_rate < 0.8:
        suggestions.append({
            "issue": "缓存命中率偏低",
            "current_rate": f"{hit_rate:.2%}",
            "target_rate": ">90%",
            "suggestion": "检查缓存失效策略，考虑增加TTL",
        })

    return {
        "current_hit_rate": f"{hit_rate:.2%}",
        "suggestions": suggestions,
    }


# 缓存优化最佳实践
CACHE_OPTIMIZATION_BEST_PRACTICES = {
    "cache_warming": {
        "description": "缓存预热",
        "when": "系统启动或缓存失效时",
        "how": "提前加载热点数据到缓存",
        "benefit": "减少冷启动时间",
    },
    "cache_protection": {
        "description": "缓存保护",
        "when": "防止缓存穿透和雪崩",
        "how": "使用空值缓存和分布式锁",
        "benefit": "提高系统稳定性",
    },
    "cache_ttl": {
        "description": "缓存TTL",
        "when": "设置缓存过期时间",
        "how": "根据数据更新频率设置",
        "benefit": "平衡性能和数据新鲜度",
    },
    "cache_key": {
        "description": "缓存键设计",
        "when": "设计缓存键",
        "how": "使用有意义的键名，避免冲突",
        "benefit": "提高缓存可维护性",
    },
}
