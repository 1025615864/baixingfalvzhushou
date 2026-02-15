"""SQL查询性能监控模块

提供SQLAlchemy查询事件的自动监听和性能分析。
"""
from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.ext.asyncio import AsyncEngine

from app.services.slow_query_analyzer import slow_query_analyzer  # type: ignore[import-untyped]

logger = logging.getLogger("sql.performance")


class QueryMonitor:
    """SQL查询监控器"""
    
    def __init__(
        self,
        slow_threshold_ms: float = 100.0,
        log_slow_queries: bool = True,
        collect_stats: bool = True,
    ) -> None:
        self.slow_threshold_ms = slow_threshold_ms
        self.log_slow_queries = log_slow_queries
        self.collect_stats = collect_stats
        self._enabled = False
        self._stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "total_time_ms": 0.0,
        }
    
    def enable(self, engine: Engine | AsyncEngine) -> None:
        """启用查询监控（支持同步和异步引擎）"""
        if self._enabled:
            return
        
        # 获取同步引擎（如果是异步引擎，使用其 sync_engine）
        if isinstance(engine, AsyncEngine):
            sync_engine = engine.sync_engine
            logger.debug("Using sync_engine from AsyncEngine for query monitoring")
        else:
            sync_engine = engine
        
        # 监听查询开始
        @event.listens_for(sync_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn: Connection,
            cursor: Any,
            statement: str,
            parameters: tuple[Any, ...],
            context: Any,
            executemany: bool,
        ) -> None:
            context._query_start_time = time.perf_counter()  # type: ignore[attr-defined]
            context._query_statement = statement  # type: ignore[attr-defined]
            context._query_params = parameters  # type: ignore[attr-defined]
        
        # 监听查询结束
        @event.listens_for(sync_engine, "after_cursor_execute")
        def after_cursor_execute(
            conn: Connection,
            cursor: Any,
            statement: str,
            parameters: tuple[Any, ...],
            context: Any,
            executemany: bool,
        ) -> None:
            if not hasattr(context, "_query_start_time"):
                return
            
            elapsed = (time.perf_counter() - context._query_start_time) * 1000  # type: ignore[attr-defined]
            
            self._record_query(
                statement=statement,
                parameters=parameters,
                duration_ms=elapsed,
            )
        
        self._enabled = True
        logger.info(f"Query monitoring enabled with threshold {self.slow_threshold_ms}ms")
    
    def _record_query(
        self,
        statement: str,
        parameters: tuple[Any, ...],
        duration_ms: float,
    ) -> None:
        """记录查询"""
        self._stats["total_queries"] += 1
        self._stats["total_time_ms"] += duration_ms
        
        is_slow = duration_ms > self.slow_threshold_ms
        
        if is_slow:
            self._stats["slow_queries"] += 1
            
            # 记录到分析器
            if self.collect_stats:
                slow_query_analyzer.record_query(
                    sql=statement,
                    duration_ms=duration_ms,
                    params={"count": len(parameters)} if parameters else None,
                )
            
            # 记录日志
            if self.log_slow_queries:
                logger.warning(
                    f"SLOW QUERY ({duration_ms:.2f}ms): {statement[:200]}..."
                )
    
    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        stats = self._stats.copy()
        if stats["total_queries"] > 0:
            stats["avg_time_ms"] = stats["total_time_ms"] / stats["total_queries"]
            stats["slow_ratio"] = stats["slow_queries"] / stats["total_queries"]
        else:
            stats["avg_time_ms"] = 0.0
            stats["slow_ratio"] = 0.0
        return stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "total_time_ms": 0.0,
        }


# 全局查询监控器实例
query_monitor = QueryMonitor(slow_threshold_ms=100.0)


def enable_query_monitoring(engine: Engine) -> None:
    """启用SQL查询监控"""
    query_monitor.enable(engine)


def get_query_stats() -> dict[str, Any]:
    """获取查询统计信息"""
    return query_monitor.get_stats()


def reset_query_stats() -> None:
    """重置查询统计"""
    query_monitor.reset_stats()