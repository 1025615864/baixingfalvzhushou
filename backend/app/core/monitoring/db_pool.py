"""数据库连接池监控增强版

支持:
- Prometheus 指标导出
- 连接池状态监控
- 慢查询追踪
- 告警阈值
"""
import logging
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from collections import deque
from functools import wraps

from prometheus_client import Counter, Gauge, Histogram, Info

from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Prometheus 指标
DB_POOL_SIZE = Gauge(
    "bxzs_db_pool_size",
    "数据库连接池大小",
    ["pool_type"]  # checkout, overflow, total
)

DB_POOL_CHECKOUTS = Counter(
    "bxzs_db_pool_checkouts_total",
    "数据库连接池检出次数",
    ["pool_type"]  # normal, overflow, timeout
)

DB_POOL_CHECKOUT_DURATION = Histogram(
    "bxzs_db_pool_checkout_duration_seconds",
    "数据库连接检出耗时",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

DB_POOL_CONNECTIONS = Gauge(
    "bxzs_db_pool_connections",
    "数据库连接池当前连接数",
    ["state"]  # checked_out, overflow, idle, total
)

DB_QUERY_DURATION = Histogram(
    "bxzs_db_query_duration_seconds",
    "数据库查询耗时",
    ["query_type"],  # select, insert, update, delete, other
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

DB_QUERIES_TOTAL = Counter(
    "bxzs_db_queries_total",
    "数据库查询总数",
    ["query_type", "status"]  # success, error, slow
)

DB_POOL_INFO = Info(
    "bxzs_db_pool",
    "数据库连接池信息"
)


class DBPoolMonitor:
    """数据库连接池监控器（增强版）

    功能:
    - Prometheus 指标导出
    - 连接池状态监控
    - 慢查询追踪
    - 告警阈值
    """

    # 告警阈值
    SLOW_QUERY_THRESHOLD = 1.0  # 1秒
    POOL_UTILIZATION_WARN = 0.8  # 80%
    POOL_UTILIZATION_CRITICAL = 0.95  # 95%
    CONNECTION_TIMEOUT_THRESHOLD = 5.0  # 5秒

    def __init__(self, max_history: int = 1000, slow_query_threshold: float = 1.0):
        self.max_history = max_history
        self.slow_query_threshold = slow_query_threshold
        self.start_time = time.time()
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "slow_queries": 0,
            "total_query_time": 0.0,
            "connection_checkouts": 0,
            "connection_checkout_timeouts": 0,
            "total_connection_time": 0.0,
        }
        self.query_history: deque[Dict[str, Any]] = deque(maxlen=max_history)
        self._lock = __import__("threading").Lock()

        # 注册连接池信息
        DB_POOL_INFO.info({
            "pool_size": str(settings.database_url.split("@")[-1].split("/")[0] if "@" in settings.database_url else "unknown"),
        })

    def record_query(
        self,
        query_time: float,
        success: bool,
        query: Optional[str] = None,
        query_type: str = "other"
    ):
        """记录查询信息"""
        with self._lock:
            self.stats["total_queries"] += 1
            self.stats["total_query_time"] += query_time

            if success:
                self.stats["successful_queries"] += 1
                status = "success"
            else:
                self.stats["failed_queries"] += 1
                status = "error"

            is_slow = query_time > self.slow_query_threshold
            if is_slow:
                self.stats["slow_queries"] += 1
                status = "slow"
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "duration": query_time,
                    "success": success,
                    "query": query[:500] if query else None,
                    "query_type": query_type,
                }
                self.query_history.append(entry)

            # Prometheus 指标
            DB_QUERY_DURATION.labels(query_type=query_type).observe(query_time)
            DB_QUERIES_TOTAL.labels(query_type=query_type, status=status).inc()

            if is_slow:
                query_preview = query[:100] if query else "N/A"
                logger.warning(f"慢查询检测: {query_time:.3f}s - {query_type} - {query_preview}")

    def record_connection_checkout(
        self,
        checkout_time: float,
        success: bool,
        timeout: bool = False
    ):
        """记录连接检出"""
        with self._lock:
            self.stats["connection_checkouts"] += 1
            self.stats["total_connection_time"] += checkout_time

            if timeout:
                self.stats["connection_checkout_timeouts"] += 1
                DB_POOL_CHECKOUTS.labels(pool_type="timeout").inc()
            elif success:
                DB_POOL_CHECKOUTS.labels(pool_type="normal").inc()
            else:
                DB_POOL_CHECKOUTS.labels(pool_type="overflow").inc()

            DB_POOL_CHECKOUT_DURATION.observe(checkout_time)

            if timeout:
                logger.warning(f"连接检出超时: {checkout_time:.3f}s")
            elif checkout_time > self.CONNECTION_TIMEOUT_THRESHOLD:
                logger.warning(f"连接检出耗时过长: {checkout_time:.3f}s")

    def update_pool_metrics(self, pool):
        """更新连接池指标"""
        try:
            size = 0
            checked_out = 0
            overflow = 0

            if hasattr(pool, "size"):
                size = pool.size()

            if hasattr(pool, "checked_out"):
                checked_out = pool.checked_out()

            if hasattr(pool, "overflow"):
                overflow = pool.overflow()

            if size > 0:
                DB_POOL_SIZE.labels(pool_type="total").set(size)
                idle = size - checked_out

                DB_POOL_CONNECTIONS.labels(state="checked_out").set(checked_out)
                DB_POOL_CONNECTIONS.labels(state="overflow").set(overflow)
                DB_POOL_CONNECTIONS.labels(state="idle").set(max(0, idle))

                utilization = checked_out / size
                if utilization > self.POOL_UTILIZATION_CRITICAL:
                    logger.critical(f"连接池利用率过高: {utilization:.1%} ({checked_out}/{size})")
                elif utilization > self.POOL_UTILIZATION_WARN:
                    logger.warning(f"连接池利用率较高: {utilization:.1%} ({checked_out}/{size})")
        except Exception as e:
            logger.debug(f"更新连接池指标失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            avg_query_time = 0.0
            avg_connection_time = 0.0
            if self.stats["successful_queries"] > 0:
                avg_query_time = self.stats["total_query_time"] / self.stats["successful_queries"]
            if self.stats["connection_checkouts"] > 0:
                avg_connection_time = self.stats["total_connection_time"] / self.stats["connection_checkouts"]

            uptime = time.time() - self.start_time
            qps = self.stats["total_queries"] / uptime if uptime > 0 else 0

            return {
                "uptime_seconds": uptime,
                "queries": {
                    "total": self.stats["total_queries"],
                    "successful": self.stats["successful_queries"],
                    "failed": self.stats["failed_queries"],
                    "slow": self.stats["slow_queries"],
                    "avg_time": avg_query_time,
                    "qps": qps,
                },
                "connections": {
                    "checkouts": self.stats["connection_checkouts"],
                    "timeouts": self.stats["connection_checkout_timeouts"],
                    "avg_checkout_time": avg_connection_time,
                },
                "thresholds": {
                    "slow_query": self.slow_query_threshold,
                    "pool_warn": f"{self.POOL_UTILIZATION_WARN:.0%}",
                    "pool_critical": f"{self.POOL_UTILIZATION_CRITICAL:.0%}",
                },
                "slow_query_history_size": len(self.query_history),
            }

    def get_recent_slow_queries(self, limit: int = 10) -> list[Dict[str, Any]]:
        """获取最近的慢查询"""
        with self._lock:
            return list(self.query_history)[-limit:]

    def reset(self):
        """重置统计信息"""
        with self._lock:
            self.stats = {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "slow_queries": 0,
                "total_query_time": 0.0,
                "connection_checkouts": 0,
                "connection_checkout_timeouts": 0,
                "total_connection_time": 0.0,
            }
            self.query_history.clear()
            self.start_time = time.time()


def monitored_query(query_type: str = "other"):
    """查询监控装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            success = True
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.perf_counter() - start
                db_pool_monitor.record_query(duration, success, func.__name__, query_type)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.perf_counter() - start
                db_pool_monitor.record_query(duration, success, func.__name__, query_type)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# 全局监控器实例
db_pool_monitor = DBPoolMonitor()
