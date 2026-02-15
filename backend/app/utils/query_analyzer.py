"""慢查询分析工具

提供慢查询日志记录和分析功能。
"""
import logging
import time
from contextlib import contextmanager
from typing import Callable, Any, Optional
from functools import wraps

from ..structured_logger import get_logger

logger = get_logger(__name__)


class QueryAnalyzer:
    """查询分析器
    
    记录和分析数据库查询性能。
    """
    
    def __init__(self, slow_query_threshold: float = 1.0):
        """初始化查询分析器
        
        Args:
            slow_query_threshold: 慢查询阈值（秒）
        """
        self.slow_query_threshold = slow_query_threshold
        self.slow_queries = []
    
    def record_query(
        self,
        query: str,
        duration: float,
        params: Optional[dict] = None
    ) -> None:
        """记录查询
        
        Args:
            query: SQL查询语句
            duration: 执行时间（秒）
            params: 查询参数
        """
        if duration > self.slow_query_threshold:
            self.slow_queries.append({
                "query": query,
                "duration": duration,
                "params": params,
                "timestamp": time.time()
            })
            logger.warning(
                f"慢查询检测: 执行时间 {duration:.3f}s",
                extra={
                    "query": query[:200],
                    "duration": duration
                }
            )
    
    def get_slow_queries(self) -> list[dict]:
        """获取慢查询列表
        
        Returns:
            慢查询列表
        """
        return self.slow_queries
    
    def get_slow_query_stats(self) -> dict:
        """获取慢查询统计信息
        
        Returns:
            统计信息
        """
        if not self.slow_queries:
            return {
                "count": 0,
                "avg_duration": 0,
                "max_duration": 0,
                "total_duration": 0
            }
        
        durations = [q["duration"] for q in self.slow_queries]
        return {
            "count": len(self.slow_queries),
            "avg_duration": sum(durations) / len(durations),
            "max_duration": max(durations),
            "total_duration": sum(durations)
        }


# 全局查询分析器实例
query_analyzer = QueryAnalyzer()


@contextmanager
def analyze_query(query: str, params: Optional[dict] = None):
    """分析查询性能的上下文管理器
    
    Args:
        query: SQL查询语句
        params: 查询参数
    
    Yields:
        None
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        query_analyzer.record_query(query, duration, params)


def track_slow_query(threshold: float = 1.0):
    """慢查询跟踪装饰器
    
    Args:
        threshold: 慢查询阈值（秒）
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if duration > threshold:
                    logger.warning(
                        f"慢查询检测: {func.__name__} 执行时间 {duration:.3f}s",
                        extra={
                            "function": func.__name__,
                            "duration": duration
                        }
                    )
        return wrapper
    return decorator


def get_slow_query_report() -> dict:
    """获取慢查询报告
    
    Returns:
        慢查询报告
    """
    stats = query_analyzer.get_slow_query_stats()
    slow_queries = query_analyzer.get_slow_queries()
    
    return {
        "stats": stats,
        "queries": slow_queries,
        "threshold": query_analyzer.slow_query_threshold
    }
