"""增强健康检查模块

提供详细的系统健康状态检查功能。

检查项目:
    - 数据库连接状态和响应时间
    - Redis连接状态和响应时间
    - 内存使用情况
    - 磁盘空间检查
    - 连接池状态
    - AI服务配置检查

使用示例:
    ```python
    from app.core.health import get_health_checker, HealthStatus

    checker = get_health_checker()
    status = await checker.check_all()
    ```
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text

from ...database import engine, AsyncSessionLocal
from ...services.cache_service import cache_service

logger = logging.getLogger("health")


@dataclass
class HealthCheckResult:
    """健康检查结果"""

    name: str
    status: str  # healthy, degraded, unhealthy
    message: str
    latency_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthStatus:
    """整体健康状态"""

    status: str  # healthy, degraded, unhealthy
    version: str
    timestamp: float = field(default_factory=time.time)
    checks: list[HealthCheckResult] = field(default_factory=list)
    uptime_seconds: float = 0.0


class HealthChecker:
    """健康检查器

    执行系统各组件的健康检查。

    Attributes:
        db_engine: 数据库引擎
        cache_service: 缓存服务
        start_time: 服务启动时间
    """

    def __init__(
        self,
        db_engine=None,
        cache=None,
        start_time: float | None = None,
    ) -> None:
        self.db_engine = db_engine or engine
        self.cache = cache or cache_service
        self.start_time = start_time or time.time()

    async def check_database(self) -> HealthCheckResult:
        """检查数据库连接

        Returns:
            HealthCheckResult
        """
        start = time.perf_counter()

        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                result.scalar()

            latency = (time.perf_counter() - start) * 1000

            pool_status = "healthy"
            if hasattr(self.db_engine, "pool"):
                pool = self.db_engine.pool
                if hasattr(pool, "checkedout"):
                    checked_out = pool.checkedout()
                    pool_size = pool.size()
                    overflow = pool.overflow() if hasattr(pool, "overflow") else 0
                    utilization = (checked_out / (pool_size + overflow) * 100) if (pool_size + overflow) > 0 else 0

                    if utilization > 90:
                        pool_status = "degraded"
                    elif utilization > 80:
                        pool_status = "healthy"

                    details = {
                        "pool_size": pool_size,
                        "checked_out": checked_out,
                        "overflow": overflow,
                        "utilization_percent": round(utilization, 2),
                    }
                else:
                    details = {}
            else:
                details = {}

            return HealthCheckResult(
                name="database",
                status="healthy" if latency < 100 else "degraded",
                message="Database connection successful",
                latency_ms=latency,
                details={
                    **details,
                    "response_time_ms": round(latency, 2),
                },
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.error(f"Database health check failed: {e}")

            return HealthCheckResult(
                name="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)[:200]}",
                latency_ms=latency,
                details={"error": str(e)[:500]},
            )

    async def check_redis(self) -> HealthCheckResult:
        """检查Redis连接

        Returns:
            HealthCheckResult
        """
        start = time.perf_counter()

        try:
            if self.cache.is_connected and self.cache.redis:
                await self.cache.redis.ping()
                latency = (time.perf_counter() - start) * 1000

                return HealthCheckResult(
                    name="redis",
                    status="healthy" if latency < 50 else "degraded",
                    message="Redis connection successful",
                    latency_ms=latency,
                    details={
                        "connected": True,
                        "response_time_ms": round(latency, 2),
                    },
                )
            else:
                latency = (time.perf_counter() - start) * 1000
                return HealthCheckResult(
                    name="redis",
                    status="degraded",
                    message="Redis not connected, using memory cache fallback",
                    latency_ms=latency,
                    details={
                        "connected": False,
                        "fallback": "memory",
                    },
                )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.error(f"Redis health check failed: {e}")

            return HealthCheckResult(
                name="redis",
                status="unhealthy",
                message=f"Redis connection failed: {str(e)[:200]}",
                latency_ms=latency,
                details={"error": str(e)[:500]},
            )

    async def check_memory(self) -> HealthCheckResult:
        """检查内存使用情况

        Returns:
            HealthCheckResult
        """
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            system_mem = psutil.virtual_memory()

            memory_usage_percent = system_mem.percent
            process_memory_mb = mem_info.rss / 1024 / 1024

            status = "healthy"
            message = "Memory usage normal"

            if memory_usage_percent > 90:
                status = "unhealthy"
                message = "Critical memory usage"
            elif memory_usage_percent > 80:
                status = "degraded"
                message = "High memory usage"

            return HealthCheckResult(
                name="memory",
                status=status,
                message=message,
                details={
                    "process_memory_mb": round(process_memory_mb, 2),
                    "system_memory_percent": memory_usage_percent,
                    "available_mb": round(system_mem.available / 1024 / 1024, 2),
                    "total_mb": round(system_mem.total / 1024 / 1024, 2),
                },
            )

        except ImportError:
            return HealthCheckResult(
                name="memory",
                status="healthy",
                message="psutil not installed, memory check skipped",
                details={"psutil_installed": False},
            )
        except Exception as e:
            return HealthCheckResult(
                name="memory",
                status="healthy",
                message=f"Memory check error: {str(e)[:100]}",
                details={"error": str(e)[:500]},
            )

    async def check_disk(self) -> HealthCheckResult:
        """检查磁盘空间

        Returns:
            HealthCheckResult
        """
        try:
            import shutil
            disk_usage = shutil.disk_usage(".")

            used_percent = (disk_usage.used / disk_usage.total) * 100

            status = "healthy"
            message = "Disk space normal"

            if used_percent > 95:
                status = "unhealthy"
                message = "Critical disk space"
            elif used_percent > 85:
                status = "degraded"
                message = "Low disk space"

            return HealthCheckResult(
                name="disk",
                status=status,
                message=message,
                details={
                    "used_percent": round(used_percent, 2),
                    "used_gb": round(disk_usage.used / 1024 / 1024 / 1024, 2),
                    "free_gb": round(disk_usage.free / 1024 / 1024 / 1024, 2),
                    "total_gb": round(disk_usage.total / 1024 / 1024 / 1024, 2),
                },
            )

        except Exception as e:
            return HealthCheckResult(
                name="disk",
                status="healthy",
                message=f"Disk check error: {str(e)[:100]}",
                details={"error": str(e)[:500]},
            )

    async def check_ai_service(self) -> HealthCheckResult:
        """检查AI服务配置

        Returns:
            HealthCheckResult
        """
        try:
            from ...config import get_settings
            settings = get_settings()

            ai_configured = bool(settings.openai_api_key)

            return HealthCheckResult(
                name="ai_service",
                status="healthy" if ai_configured else "degraded",
                message="AI service configured" if ai_configured else "AI service not configured",
                details={
                    "openai_configured": ai_configured,
                    "anthropic_configured": bool(settings.anthropic_api_key),
                    "deepseek_configured": bool(settings.deepseek_api_key),
                },
            )

        except Exception as e:
            return HealthCheckResult(
                name="ai_service",
                status="healthy",
                message=f"AI config check error: {str(e)[:100]}",
                details={"error": str(e)[:500]},
            )

    async def check_all(self, version: str = "1.0.0") -> HealthStatus:
        """执行所有健康检查

        Args:
            version: API版本号

        Returns:
            HealthStatus整体状态
        """
        checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_memory(),
            self.check_disk(),
            self.check_ai_service(),
            return_exceptions=True,
        )

        valid_checks = []
        for check in checks:
            if isinstance(check, HealthCheckResult):
                valid_checks.append(check)
            else:
                logger.error(f"Health check error: {check}")

        overall_status = "healthy"
        for check in valid_checks:
            if check.status == "unhealthy":
                overall_status = "unhealthy"
                break
            elif check.status == "degraded" and overall_status == "healthy":
                overall_status = "degraded"

        return HealthStatus(
            status=overall_status,
            version=version,
            checks=valid_checks,
            uptime_seconds=time.time() - self.start_time,
        )


_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """获取健康检查器单例"""
    global _health_checker

    if _health_checker is None:
        _health_checker = HealthChecker()

    return _health_checker
