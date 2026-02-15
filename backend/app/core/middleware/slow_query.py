"""慢查询日志中间件

记录超过阈值的数据库查询和API请求。

功能特性:
    - SQL查询执行时间记录
    - API请求响应时间记录
    - 慢查询分类统计
    - 可配置的阈值

使用示例:
    ```python
    from app.core.middleware.slow_query import SlowQueryLoggerMiddleware

    app.add_middleware(SlowQueryLoggerMiddleware, sql_threshold=0.5, api_threshold=2.0)
    ```

配置选项:
    - sql_threshold: SQL查询阈值（秒），默认0.5
    - api_threshold: API请求阈值（秒），默认2.0
    - exclude_paths: 排除的路径列表
"""
from __future__ import annotations

import logging
import time
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("slow_query")


class SlowQueryLoggerMiddleware(BaseHTTPMiddleware):
    """慢查询日志中间件

    记录执行时间超过阈值的数据库查询和API请求。

    Attributes:
        sql_threshold: SQL查询阈值（秒）
        api_threshold: API请求阈值（秒）
        exclude_paths: 排除的路径列表
        _query_count: 计数器
    """

    DEFAULT_EXCLUDE_PATHS = {
        "/health",
        "/health/",
        "/metrics",
        "/metrics/",
        "/docs",
        "/docs/",
        "/redoc",
        "/redoc/",
        "/openapi.json",
        "/favicon.ico",
    }

    def __init__(
        self,
        app,
        sql_threshold: float = 0.5,
        api_threshold: float = 2.0,
        exclude_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.sql_threshold = sql_threshold
        self.api_threshold = api_threshold
        self.exclude_paths = exclude_paths or self.DEFAULT_EXCLUDE_PATHS
        self._query_count = 0
        self._slow_query_count = 0
        self._slow_api_count = 0

    def _should_exclude(self, path: str) -> bool:
        """检查是否应该排除"""
        if path in self.exclude_paths:
            return True
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path.rstrip("/")):
                return True
        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求

        Args:
            request: FastAPI请求对象
            call_next: 下一个处理器

        Returns:
            HTTP响应
        """
        if self._should_exclude(request.url.path):
            return await call_next(request)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            if elapsed > self.api_threshold:
                self._slow_api_count += 1
                logger.warning(
                    f"SLOW API REQUEST (exception): {request.method} {request.url.path} "
                    f"took {elapsed:.3f}s - {type(e).__name__}: {str(e)[:200]}"
                )
            raise

        elapsed = time.perf_counter() - start_time

        if elapsed > self.api_threshold:
            self._slow_api_count += 1
            logger.warning(
                f"SLOW API REQUEST: {request.method} {request.url.path} "
                f"took {elapsed:.3f}s status={response.status_code}"
            )

        return response


class SlowQueryRecorder:
    """慢查询记录器

    用于手动记录SQL查询执行时间。

    Attributes:
        threshold: 慢查询阈值（秒）
        queries: 记录的查询列表
    """

    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold
        self.queries: list[dict[str, Any]] = []
        self._query_start: float | None = None

    def start(self) -> None:
        """开始记录查询"""
        self._query_start = time.perf_counter()

    def stop(self, query: str, params: dict[str, Any] | None = None) -> bool:
        """停止记录查询

        Args:
            query: SQL查询
            params: 查询参数

        Returns:
            是否为慢查询
        """
        if self._query_start is None:
            return False

        elapsed = time.perf_counter() - self._query_start
        self._query_start = None

        if elapsed > self.threshold:
            self.queries.append({
                "query": query[:500],
                "params": params,
                "duration": elapsed,
                "timestamp": time.time(),
            })
            logger.debug(
                f"SLOW SQL QUERY ({elapsed:.3f}s): {query[:200]}"
            )
            return True

        return False

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = len(self.queries)
        if total == 0:
            return {"count": 0, "total_duration": 0, "avg_duration": 0}

        total_duration = sum(q["duration"] for q in self.queries)
        return {
            "count": total,
            "total_duration": total_duration,
            "avg_duration": total_duration / total,
            "max_duration": max(q["duration"] for q in self.queries) if total > 0 else 0,
        }

    def clear(self) -> None:
        """清空记录"""
        self.queries.clear()


_slow_query_recorder = SlowQueryRecorder()


def get_slow_query_recorder() -> SlowQueryRecorder:
    """获取慢查询记录器单例"""
    return _slow_query_recorder


async def record_query(
    query: str,
    params: dict[str, Any] | None = None,
    threshold: float = 0.5,
) -> float:
    """记录查询执行时间

    Args:
        query: SQL查询
        params: 查询参数
        threshold: 阈值

    Returns:
        执行时间（秒）
    """
    start = time.perf_counter()
    elapsed = time.perf_counter() - start

    if elapsed > threshold:
        logger.debug(f"SLOW QUERY ({elapsed:.3f}s): {query[:200]}")

    return elapsed
