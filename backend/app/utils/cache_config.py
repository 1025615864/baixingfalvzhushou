"""缓存配置工具

提供缓存过期时间配置、缓存键生成规则、缓存命中率统计等功能。
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class CachePreset(Enum):
    """预定义缓存配置"""
    # 推荐服务
    RECOMMENDATION_LAWYER = ("recommendation:lawyer", 120, 600)      # 2 分钟 L1, 10 分钟 L2
    RECOMMENDATION_POST = ("recommendation:post", 60, 300)           # 1 分钟 L1, 5 分钟 L2
    RECOMMENDATION_NEWS = ("recommendation:news", 60, 300)           # 1 分钟 L1, 5 分钟 L2
    RECOMMENDATION_KNOWLEDGE = ("recommendation:knowledge", 120, 600)  # 2 分钟 L1, 10 分钟 L2

    # 新闻服务
    NEWS_LIST = ("news:list", 60, 300)                               # 1 分钟 L1, 5 分钟 L2
    NEWS_DETAIL = ("news:detail", 120, 600)                          # 2 分钟 L1, 10 分钟 L2
    NEWS_HOT = ("news:hot", 30, 120)                                 # 30 秒 L1, 2 分钟 L2
    NEWS_CATEGORY = ("news:category", 60, 300)                       # 1 分钟 L1, 5 分钟 L2

    # 知识库服务
    KNOWLEDGE_LIST = ("knowledge:list", 120, 600)                    # 2 分钟 L1, 10 分钟 L2
    KNOWLEDGE_DETAIL = ("knowledge:detail", 300, 1800)               # 5 分钟 L1, 30 分钟 L2
    KNOWLEDGE_CATEGORY = ("knowledge:category", 300, 1800)           # 5 分钟 L1, 30 分钟 L2
    KNOWLEDGE_SEARCH = ("knowledge:search", 60, 300)                 # 1 分钟 L1, 5 分钟 L2

    # 用户服务
    USER_PROFILE = ("user:profile", 60, 300)                         # 1 分钟 L1, 5 分钟 L2
    USER_BALANCE = ("user:balance", 30, 120)                         # 30 秒 L1, 2 分钟 L2
    USER_HISTORY = ("user:history", 120, 600)                        # 2 分钟 L1, 10 分钟 L2

    # 配置服务
    CONFIG_GLOBAL = ("config:global", 300, 3600)                     # 5 分钟 L1, 1 小时 L2
    CONFIG_FEATURE = ("config:feature", 300, 3600)                   # 5 分钟 L1, 1 小时 L2

    # 论坛服务
    FORUM_POST_LIST = ("forum:post:list", 60, 300)                   # 1 分钟 L1, 5 分钟 L2
    FORUM_POST_DETAIL = ("forum:post:detail", 120, 600)              # 2 分钟 L1, 10 分钟 L2
    FORUM_HOT = ("forum:hot", 30, 120)                               # 30 秒 L1, 2 分钟 L2

    # 律师服务
    LAWYER_LIST = ("lawyer:list", 120, 600)                          # 2 分钟 L1, 10 分钟 L2
    LAWYER_DETAIL = ("lawyer:detail", 300, 1800)                     # 5 分钟 L1, 30 分钟 L2
    LAWYER_SCHEDULE = ("lawyer:schedule", 60, 300)                   # 1 分钟 L1, 5 分钟 L2

    @property
    def prefix(self) -> str:
        """获取缓存键前缀"""
        return self.value[0]

    @property
    def l1_ttl(self) -> int:
        """获取 L1 缓存过期时间（秒）"""
        return self.value[1]

    @property
    def l2_ttl(self) -> int:
        """获取 L2 缓存过期时间（秒）"""
        return self.value[2]


@dataclass
class CacheConfig:
    """缓存配置类"""
    prefix: str
    l1_ttl: int = 60       # L1 缓存过期时间（秒）
    l2_ttl: int = 300      # L2 缓存过期时间（秒）
    l1_max_size: int = 1000  # L1 最大条目数
    enabled: bool = True   # 是否启用缓存
    serialize: bool = True  # 是否序列化值

    def make_key(self, *parts: Any) -> str:
        """生成缓存键"""
        return make_cache_key(self.prefix, *parts)


@dataclass
class CacheMetric:
    """缓存度量指标"""
    hits: int = 0
    misses: int = 0
    writes: int = 0
    deletes: int = 0
    evictions: int = 0
    errors: int = 0
    total_time_ms: float = 0.0
    call_count: int = 0

    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    @property
    def avg_time_ms(self) -> float:
        """平均响应时间（毫秒）"""
        return (self.total_time_ms / self.call_count) if self.call_count > 0 else 0.0

    def record_hit(self) -> None:
        """记录命中"""
        self.hits += 1

    def record_miss(self) -> None:
        """记录未命中"""
        self.misses += 1

    def record_write(self) -> None:
        """记录写入"""
        self.writes += 1

    def record_delete(self) -> None:
        """记录删除"""
        self.deletes += 1

    def record_eviction(self) -> None:
        """记录淘汰"""
        self.evictions += 1

    def record_error(self) -> None:
        """记录错误"""
        self.errors += 1

    def record_time(self, time_ms: float) -> None:
        """记录耗时"""
        self.total_time_ms += time_ms
        self.call_count += 1

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "writes": self.writes,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "errors": self.errors,
            "hit_rate_percent": round(self.hit_rate, 2),
            "avg_time_ms": round(self.avg_time_ms, 3),
            "total_calls": self.call_count,
        }


class CacheMetricsCollector:
    """缓存指标收集器"""

    def __init__(self):
        self._metrics: dict[str, CacheMetric] = {}
        self._start_times: dict[str, float] = {}

    def get_metric(self, cache_name: str) -> CacheMetric:
        """获取或创建指标"""
        if cache_name not in self._metrics:
            self._metrics[cache_name] = CacheMetric()
        return self._metrics[cache_name]

    def start_timer(self, cache_name: str) -> None:
        """开始计时"""
        self._start_times[cache_name] = time.time() * 1000  # 毫秒

    def stop_timer(self, cache_name: str) -> float:
        """停止计时并返回耗时"""
        start = self._start_times.pop(cache_name, None)
        if start is not None:
            elapsed = time.time() * 1000 - start
            metric = self.get_metric(cache_name)
            metric.record_time(elapsed)
            return elapsed
        return 0.0

    def record_hit(self, cache_name: str) -> None:
        """记录命中"""
        self.get_metric(cache_name).record_hit()

    def record_miss(self, cache_name: str) -> None:
        """记录未命中"""
        self.get_metric(cache_name).record_miss()

    def record_write(self, cache_name: str) -> None:
        """记录写入"""
        self.get_metric(cache_name).record_write()

    def record_delete(self, cache_name: str) -> None:
        """记录删除"""
        self.get_metric(cache_name).record_delete()

    def record_eviction(self, cache_name: str) -> None:
        """记录淘汰"""
        self.get_metric(cache_name).record_eviction()

    def record_error(self, cache_name: str) -> None:
        """记录错误"""
        self.get_metric(cache_name).record_error()

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """获取所有指标"""
        return {name: metric.to_dict() for name, metric in self._metrics.items()}

    def get_summary(self) -> dict[str, Any]:
        """获取汇总指标"""
        total_hits = sum(m.hits for m in self._metrics.values())
        total_misses = sum(m.misses for m in self._metrics.values())
        total_writes = sum(m.writes for m in self._metrics.values())
        total_errors = sum(m.errors for m in self._metrics.values())
        total_calls = sum(m.call_count for m in self._metrics.values())
        total_time = sum(m.total_time_ms for m in self._metrics.values())

        total_requests = total_hits + total_misses
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0
        overall_avg_time = (total_time / total_calls) if total_calls > 0 else 0.0

        return {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_writes": total_writes,
            "total_errors": total_errors,
            "total_calls": total_calls,
            "overall_hit_rate_percent": round(overall_hit_rate, 2),
            "overall_avg_time_ms": round(overall_avg_time, 3),
            "cache_count": len(self._metrics),
        }

    def reset(self) -> None:
        """重置所有指标"""
        self._metrics.clear()
        self._start_times.clear()


class CacheKeyGenerator:
    """缓存键生成器"""

    @staticmethod
    def generate(
        prefix: str,
        *parts: Any,
        use_hash: bool = False,
        max_length: int = 200,
    ) -> str:
        """生成缓存键

        Args:
            prefix: 键前缀
            *parts: 键组成部分
            use_hash: 是否对复杂部分使用哈希
            max_length: 最大长度

        Returns:
            生成的缓存键
        """
        key_parts = [prefix]

        for part in parts:
            if part is None:
                continue

            if isinstance(part, (dict, list)):
                if use_hash:
                    # 复杂类型使用哈希
                    key_str = json.dumps(part, sort_keys=True, ensure_ascii=False)
                    hashed = hashlib.md5(key_str.encode()).hexdigest()[:12]
                    key_parts.append(f"hash:{hashed}")
                else:
                    # 直接序列化
                    key_str = json.dumps(part, sort_keys=True, ensure_ascii=False)
                    key_parts.append(key_str.replace(":", "_"))
            elif isinstance(part, (tuple, set, frozenset)):
                if use_hash:
                    key_str = json.dumps(sorted(part), sort_keys=True, ensure_ascii=False)
                    hashed = hashlib.md5(key_str.encode()).hexdigest()[:12]
                    key_parts.append(f"hash:{hashed}")
                else:
                    key_parts.append("_".join(str(p) for p in sorted(part)))
            else:
                key_parts.append(str(part))

        key = ":".join(key_parts)

        # 截断过长的键
        if len(key) > max_length:
            # 保留前缀，对剩余部分哈希
            suffix = key[len(prefix) + 1:]
            hashed = hashlib.md5(suffix.encode()).hexdigest()[:12]
            key = f"{prefix}:hash:{hashed}"

        return key

    @staticmethod
    def generate_batch(
        prefix: str,
        items: list[Any],
        id_extractor: Callable[[Any], Any] | None = None,
    ) -> list[str]:
        """批量生成缓存键

        Args:
            prefix: 键前缀
            items: 项目列表
            id_extractor: ID 提取函数

        Returns:
            缓存键列表
        """
        keys = []
        for item in items:
            if id_extractor:
                item_id = id_extractor(item)
                keys.append(f"{prefix}:{item_id}")
            else:
                keys.append(f"{prefix}:{item}")
        return keys


class CacheInvalidationRule:
    """缓存失效规则"""

    def __init__(self):
        self._rules: dict[str, list[str]] = {}

    def add_rule(self, trigger_pattern: str, target_patterns: list[str]) -> None:
        """添加失效规则

        Args:
            trigger_pattern: 触发模式（如 "user:profile:*"）
            target_patterns: 目标模式列表（如 ["user:cache:*", "user:session:*"]）
        """
        self._rules[trigger_pattern] = target_patterns

    def get_targets(self, trigger_key: str) -> list[str]:
        """根据触发键获取需要失效的目标模式

        Args:
            trigger_key: 触发失效的键

        Returns:
            需要失效的目标模式列表
        """
        targets = []
        for trigger_pattern, target_patterns in self._rules.items():
            if self._matches(trigger_key, trigger_pattern):
                targets.extend(target_patterns)
        return targets

    def _matches(self, key: str, pattern: str) -> bool:
        """检查键是否匹配模式"""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)


# 全局指标收集器
cache_metrics_collector = CacheMetricsCollector()

# 全局键生成器
cache_key_generator = CacheKeyGenerator()

# 全局失效规则
cache_invalidation_rules = CacheInvalidationRule()


def make_cache_key(prefix: str, *parts: Any) -> str:
    """便捷函数：生成缓存键"""
    return cache_key_generator.generate(prefix, *parts)


def get_cache_metrics() -> dict[str, dict[str, Any]]:
    """便捷函数：获取所有缓存指标"""
    return cache_metrics_collector.get_all_metrics()


def get_cache_summary() -> dict[str, Any]:
    """便捷函数：获取缓存汇总"""
    return cache_metrics_collector.get_summary()


def reset_cache_metrics() -> None:
    """便捷函数：重置缓存指标"""
    cache_metrics_collector.reset()


# 预定义的失效规则
def setup_default_invalidation_rules() -> None:
    """设置默认的缓存失效规则"""
    # 用户资料更新时，失效相关缓存
    cache_invalidation_rules.add_rule(
        "user:profile:*",
        ["user:cache:*", "user:session:*"]
    )

    # 新闻更新时，失效相关缓存
    cache_invalidation_rules.add_rule(
        "news:detail:*",
        ["news:list:*", "news:hot:*"]
    )

    # 知识库更新时，失效相关缓存
    cache_invalidation_rules.add_rule(
        "knowledge:detail:*",
        ["knowledge:list:*", "knowledge:search:*", "knowledge:category:*"]
    )

    # 律师信息更新时，失效相关缓存
    cache_invalidation_rules.add_rule(
        "lawyer:detail:*",
        ["lawyer:list:*", "recommendation:lawyer:*"]
    )


# 初始化默认规则
setup_default_invalidation_rules()


# 缓存装饰器
def cached_with_config(
    config: CachePreset | CacheConfig,
    key_parts: Callable[..., tuple] | None = None,
):
    """带配置的缓存装饰器

    Usage:
        @cached_with_config(CachePreset.NEWS_DETAIL)
        async def get_news_detail(news_id: int):
            ...

        @cached_with_config(CacheConfig(prefix="custom", l1_ttl=60, l2_ttl=300))
        async def get_custom_data(data_id: int):
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            from ..services.multi_level_cache import cache_manager

            # 确定缓存配置
            if isinstance(config, CachePreset):
                prefix = config.prefix
                l1_ttl = config.l1_ttl
                l2_ttl = config.l2_ttl
            else:
                prefix = config.prefix
                l1_ttl = config.l1_ttl
                l2_ttl = config.l2_ttl

            # 生成缓存键
            if key_parts:
                parts = key_parts(*args, **kwargs)
            else:
                # 默认使用函数名和参数
                parts = (func.__name__,) + args + tuple(kwargs.items())

            cache_key = make_cache_key(prefix, *parts)
            cache_name = f"{prefix}:{func.__name__}"

            # 获取缓存
            cache = cache_manager.get_cache(
                prefix,
                l1_default_ttl=l1_ttl,
                l2_default_ttl=l2_ttl,
            )

            # 尝试获取缓存
            cache_metrics_collector.start_timer(cache_name)
            result = await cache.get(cache_key)

            if result is not None:
                cache_metrics_collector.record_hit(cache_name)
                cache_metrics_collector.stop_timer(cache_name)
                return result

            cache_metrics_collector.record_miss(cache_name)

            # 执行函数
            result = await func(*args, **kwargs)

            # 存储缓存
            if result is not None:
                await cache.set(cache_key, result, l2_ttl)
                cache_metrics_collector.record_write(cache_name)

            cache_metrics_collector.stop_timer(cache_name)
            return result

        return wrapper
    return decorator