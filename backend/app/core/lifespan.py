"""应用生命周期管理模块"""
from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI

from ..config import get_settings
from ..database import init_db
from ..services.cache_service import cache_service
from ..services.prometheus_metrics import prometheus_metrics
from ..utils.periodic_task_runner import PeriodicLockedRunner
from .sentry_config import init_sentry
from .metrics_config import start_metrics_server, update_system_info

logger = logging.getLogger(__name__)
settings = get_settings()

# AI 模块懒加载
try:
    from ..routers import ai
except Exception:
    ai = None
    logger.info("AI路由未启用")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    _ = app

    # 初始化 Sentry
    init_sentry(settings)

    # 初始化 Prometheus 指标服务器
    prometheus_port = int(getattr(settings, 'prometheus_port', 8001) or 8001)
    prometheus_enabled = bool(
        getattr(settings, 'prometheus_enabled', False) or
        __import__('os').getenv('PROMETHEUS_ENABLED', '').lower() == 'true'
    )
    if prometheus_enabled:
        start_metrics_server(port=prometheus_port)
        logger.info(f"Prometheus metrics server enabled on port {prometheus_port}")

    # 更新系统信息指标
    update_system_info(
        version=getattr(settings, 'VERSION', '1.0.0'),
        environment=getattr(settings, 'ENVIRONMENT', 'development'),
        python_version=".".join(map(str, __import__('sys').version_info[:3]))
    )

    # 初始化数据库
    await init_db()
    
    # 启用SQL查询性能监控
    from .monitoring.query_monitor import enable_query_monitoring
    from ..database.engine import engine
    enable_query_monitoring(engine)

    # 设置任务调度
    stop_event = asyncio.Event()
    runner = PeriodicLockedRunner(
        stop_event=stop_event,
        lock_client=cache_service,
        logger=logger
    )

    # 连接 Redis
    redis_connected = False
    if settings.redis_url:
        redis_connected = bool(await cache_service.connect(settings.redis_url))

    # 生产环境必须连接 Redis
    if (not settings.debug) and (not redis_connected):
        raise RuntimeError(
            "Redis must be available when DEBUG is False. "
            "Please set REDIS_URL and ensure Redis is reachable."
        )

    # 启动任务调度器
    from ..services.task_scheduler import get_task_scheduler
    task_scheduler = get_task_scheduler(runner)
    tasks = await task_scheduler.start_all(redis_connected, settings.debug, settings)

    # 启动积分系统定时任务
    points_scheduled_tasks = None
    if redis_connected:
        try:
            from ..services.points.scheduled_tasks import get_points_scheduled_tasks
            points_scheduled_tasks = get_points_scheduled_tasks()
            points_scheduled_tasks.start_scheduler(check_interval=60)
            logger.info("积分系统定时任务已启动")
        except Exception as e:
            logger.warning(f"积分系统定时任务启动失败: {e}")

    logger.info("数据库初始化完成")
    if ai is not None:
        logger.info("AI助手模块已启用")
    else:
        logger.info("AI助手模块未启用")

    # 初始化 MCP 工具系统
    try:
        from ..services.mcp import get_mcp_manager
        mcp_manager = get_mcp_manager()
        mcp_manager.initialize()
        logger.info("MCP工具系统已初始化")
    except Exception as e:
        logger.warning(f"MCP工具系统初始化失败: {e}")

    # 初始化系统监控
    try:
        from ..services.system_monitor import get_system_monitor
        monitor = get_system_monitor()
        logger.info("系统监控已初始化")
    except Exception as e:
        logger.warning(f"系统监控初始化失败: {e}")

    yield

    # 关闭阶段
    stop_event.set()
    for t in tasks:
        if t is None:
            continue
        _ = t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    await task_scheduler.stop_all()

    if points_scheduled_tasks:
        try:
            points_scheduled_tasks.stop_scheduler()
        except Exception:
            pass

    await cache_service.disconnect()
    logger.info("应用关闭")