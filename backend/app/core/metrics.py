"""增强Prometheus指标模块

提供系统监控指标收集和导出功能。

指标分类:
    - HTTP请求指标
    - 数据库连接池指标
    - 缓存指标
    - 业务指标

使用示例:
    ```python
    from app.core.metrics import get_metrics, MetricsCollector

    collector = MetricsCollector()

    # 记录自定义指标
    collector.record_database_pool_stats(pool_stats)
    collector.record_cache_hit(hit=True)

    # 获取Prometheus格式指标
    metrics = collector.get_metrics()
    ```
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, Info

from ...database import engine
from ...services.cache_service import cache_service
from ...core.monitoring.db_pool import get_pool_monitor

info_metric = Info("app", "Application information")

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method", "endpoint"],
)

db_pool_size = Gauge(
    "db_pool_size",
    "Database connection pool size",
)

db_pool_checked_out = Gauge(
    "db_pool_checked_out",
    "Number of checked out connections",
)

db_pool_checked_in = Gauge(
    "db_pool_checked_in",
    "Number of checked in connections",
)

db_pool_overflow = Gauge(
    "db_pool_overflow",
    "Connection pool overflow",
)

db_pool_utilization_percent = Gauge(
    "db_pool_utilization_percent",
    "Database pool utilization percentage",
)

cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
)

cache_size = Gauge(
    "cache_size",
    "Current cache size",
)

active_users = Gauge(
    "active_users",
    "Number of active users",
)

database_queries_total = Counter(
    "database_queries_total",
    "Total database queries",
    ["table", "operation"],
)

api_errors_total = Counter(
    "api_errors_total",
    "Total API errors",
    ["endpoint", "error_type"],
)


@dataclass
class MetricsCollector:
    """指标收集器

    收集和导出系统指标。

    Attributes:
        _request_counts: 请求计数
        _error_counts: 错误计数
    """

    _request_counts: dict = field(default_factory=lambda: defaultdict(int))
    _error_counts: dict = field(default_factory=lambda: defaultdict(int))
    _start_time: float = field(default_factory=time.time)

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float,
    ) -> None:
        """记录HTTP请求

        Args:
            method: HTTP方法
            endpoint: 端点路径
            status: 状态码
            duration: 请求耗时（秒）
        """
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status),
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)

    def record_db_pool_stats(self) -> None:
        """记录数据库连接池统计"""
        try:
            pool_monitor = get_pool_monitor()
            stats = pool_monitor.get_stats()
            pool_health = pool_monitor.get_health_status()

            db_pool_size.set(stats.pool_size)
            db_pool_checked_out.set(stats.checked_out)
            db_pool_checked_in.set(stats.checked_in)
            db_pool_overflow.set(stats.overflow)
            db_pool_utilization_percent.set(pool_health["utilization_percent"])

        except Exception as e:
            pass

    def record_cache_stats(self) -> None:
        """记录缓存统计"""
        try:
            cache_stats = cache_service.get_stats()

            cache_hits_total.inc(cache_stats.get("hits", 0) - cache_hits_total._value.get())
            cache_misses_total.inc(cache_stats.get("misses", 0) - cache_misses_total._value.get())

            cache_size.set(cache_stats.get("memory_cache_size", 0))

        except Exception as e:
            pass

    def record_error(self, endpoint: str, error_type: str) -> None:
        """记录错误

        Args:
            endpoint: 端点路径
            error_type: 错误类型
        """
        api_errors_total.labels(
            endpoint=endpoint,
            error_type=error_type,
        ).inc()

    def record_database_query(self, table: str, operation: str) -> None:
        """记录数据库查询

        Args:
            table: 表名
            operation: 操作类型 (select, insert, update, delete)
        """
        database_queries_total.labels(
            table=table,
            operation=operation,
        ).inc()

    def set_app_info(self, version: str, environment: str) -> None:
        """设置应用信息

        Args:
            version: 应用版本
            environment: 环境 (production, staging, development)
        """
        info_metric.info({
            "version": version,
            "environment": environment,
            "python_version": "3.11+",
        })

    def get_uptime_seconds(self) -> float:
        """获取运行时间

        Returns:
            运行时间（秒）
        """
        return time.time() - self._start_time


_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """获取指标收集器单例"""
    global _metrics_collector

    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()

    return _metrics_collector


def init_app_metrics(version: str = "1.0.0", environment: str = "development") -> None:
    """初始化应用指标

    Args:
        version: 应用版本
        environment: 运行环境
    """
    collector = get_metrics_collector()
    collector.set_app_info(version, environment)


def record_request_metrics(
    method: str,
    endpoint: str,
    status: int,
    duration: float,
) -> None:
    """便捷的请求指标记录函数

    Args:
        method: HTTP方法
        endpoint: 端点路径
        status: 状态码
        duration: 请求耗时
    """
    collector = get_metrics_collector()
    collector.record_http_request(method, endpoint, status, duration)


def record_error_metrics(endpoint: str, error_type: str) -> None:
    """便捷的错误指标记录函数

    Args:
        endpoint: 端点路径
        error_type: 错误类型
    """
    collector = get_metrics_collector()
    collector.record_error(endpoint, error_type)
