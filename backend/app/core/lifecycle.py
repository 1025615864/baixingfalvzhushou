"""应用启动配置模块

提供应用生命周期管理的配置类。

功能:
    - 数据库初始化配置
    - Redis连接配置
    - 定时任务配置
    - 监控服务配置

使用示例:
    ```python
    from app.core.lifecycle import AppLifecycle, LifecycleConfig

    config = LifecycleConfig(
        redis_required=True,
        enable_ai=True,
        enable_mcp=True,
    )

    lifecycle = AppLifecycle(config)
    ```
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from ..config import Settings
from ..database import init_db
from ..services.cache_service import cache_service
from ..utils.periodic_task_runner import PeriodicLockedRunner

logger = logging.getLogger("lifecycle")


@dataclass
class LifecycleConfig:
    """生命周期配置"""

    redis_required: bool = True
    enable_ai: bool = True
    enable_mcp: bool = True
    enable_monitoring: bool = True
    enable_points_scheduler: bool = True
    debug: bool = False


class AppLifecycle:
    """应用生命周期管理器

    封装应用启动和关闭逻辑。

    Attributes:
        config: 生命周期配置
        stop_event: 停止事件
        runner: 周期任务运行器
        tasks: 运行中的任务列表
    """

    def __init__(self, config: LifecycleConfig | None = None) -> None:
        self.config = config or LifecycleConfig()
        self.stop_event: asyncio.Event | None = None
        self.runner: PeriodicLockedRunner | None = None
        self.tasks: list[asyncio.Task[Any]] = []
        self.task_scheduler: Any = None
        self.points_scheduled_tasks: Any = None

    async def initialize(self) -> None:
        """初始化应用组件"""
        await init_db()
        logger.info("数据库初始化完成")

        self.stop_event = asyncio.Event()
        self.runner = PeriodicLockedRunner(
            stop_event=self.stop_event,
            lock_client=cache_service,
            logger=logger,
        )

    async def connect_redis(self, redis_url: str) -> bool:
        """连接Redis

        Args:
            redis_url: Redis连接URL

        Returns:
            是否连接成功
        """
        if not redis_url:
            if self.config.redis_required and not self.config.debug:
                raise RuntimeError(
                    "Redis必须可用。请设置REDIS_URL并确保Redis可访问。"
                )
            return False

        redis_connected = bool(await cache_service.connect(redis_url))

        if self.config.redis_required and not redis_connected and not self.config.debug:
            raise RuntimeError(
                "Redis必须可用。请设置REDIS_URL并确保Redis可访问。"
            )

        return redis_connected

    async def start_tasks(self, redis_connected: bool, settings: Settings) -> None:
        """启动定时任务

        Args:
            redis_connected: Redis是否已连接
            settings: 应用配置
        """
        from ..services.task_scheduler import get_task_scheduler
        self.task_scheduler = get_task_scheduler(self.runner)
        self.tasks = await self.task_scheduler.start_all(
            redis_connected, self.config.debug, settings
        )

    async def start_points_scheduler(self) -> None:
        """启动积分定时任务（已迁移到points-service）"""
        # 积分定时任务已由 points-service 独立处理
        pass

    async def initialize_ai(self) -> None:
        """初始化AI模块"""
        if not self.config.enable_ai:
            return

        try:
            from ..routers import ai
            if ai is not None:
                logger.info("AI助手模块已启用")
            else:
                logger.info("AI助手模块未启用")
        except Exception as e:
            logger.warning(f"AI模块初始化失败: {e}")

    async def initialize_mcp(self) -> None:
        """初始化MCP工具系统"""
        if not self.config.enable_mcp:
            return

        try:
            from ..services.mcp import get_mcp_manager
            mcp_manager = get_mcp_manager()
            mcp_manager.initialize()
            logger.info("MCP工具系统已初始化")
        except Exception as e:
            logger.warning(f"MCP工具系统初始化失败: {e}")

    async def initialize_monitoring(self) -> None:
        """初始化系统监控"""
        if not self.config.enable_monitoring:
            return

        try:
            from ..services.system_monitor import get_system_monitor
            monitor = get_system_monitor()
            logger.info("系统监控已初始化")
        except Exception as e:
            logger.warning(f"系统监控初始化失败: {e}")

    async def startup(self, settings: Settings) -> None:
        """应用启动

        Args:
            settings: 应用配置
        """
        await self.initialize()

        redis_connected = await self.connect_redis(settings.redis_url)

        await self.start_tasks(redis_connected, settings)
        await self.start_points_scheduler()
        await self.initialize_ai()
        await self.initialize_mcp()
        await self.initialize_monitoring()

    async def shutdown(self) -> None:
        """应用关闭"""
        if self.stop_event:
            self.stop_event.set()

        for t in self.tasks:
            if t is None:
                continue
            _ = t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        if self.task_scheduler:
            await self.task_scheduler.stop_all()

        if self.points_scheduled_tasks:
            try:
                self.points_scheduled_tasks.stop_scheduler()
            except Exception:
                pass

        await cache_service.disconnect()
        logger.info("应用已关闭")


_lifecycle_manager: AppLifecycle | None = None


def get_lifecycle_manager() -> AppLifecycle:
    """获取生命周期管理器单例"""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = AppLifecycle()
    return _lifecycle_manager


async def lifespan_startup(settings: Settings) -> None:
    """便捷函数：启动应用"""
    manager = get_lifecycle_manager()
    await manager.startup(settings)


async def lifespan_shutdown() -> None:
    """便捷函数：关闭应用"""
    manager = get_lifecycle_manager()
    await manager.shutdown()
