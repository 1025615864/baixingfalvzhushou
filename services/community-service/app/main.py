"""社区服务主应用"""
import logging
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
import redis.asyncio as redis

from .config.settings import get_settings
from .utils.logging_config import setup_logging

settings = get_settings()
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

try:
    from services.common.security import get_cors_config
except ImportError:
    def get_cors_config():
        return {
            "allow_origins": os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

try:
    from services.common.tracing import init_telemetry
except ImportError:
    def init_telemetry(*args, **kwargs):
        pass

try:
    from services.common.discovery import get_consul_registry
except ImportError:
    def get_consul_registry(*args, **kwargs):
        return None

_redis_client: redis.Redis = None
_redis_for_rate_limit: redis.Redis = None
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis_client, _redis_for_rate_limit
    logger.info("Community service starting...")

    init_telemetry(
        service_name="community-service",
        service_version="1.0.0",
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    )
    logger.info("OpenTelemetry initialized")

    if os.getenv("REDIS_URL"):
        try:
            _redis_client = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True
            )
            await _redis_client.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            _redis_client = None

    if os.getenv("REDIS_URL"):
        try:
            _redis_for_rate_limit = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True
            )
        except Exception:
            logger.error("限流Redis连接失败")
            _redis_for_rate_limit = None

    from .middleware.rate_limit import rate_limiter
    rate_limiter._client = _redis_for_rate_limit

    consul = get_consul_registry()
    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        host = os.getenv("SERVICE_HOST", "localhost")
        port = int(os.getenv("SERVICE_PORT", "8007"))
        await consul.register_service(
            service_name="community-service",
            service_id=f"community-service-{port}",
            host=host,
            port=port,
            metadata={"version": "1.0.0"},
            tags=["http"],
            health_check_url=f"http://{host}:{port}/health",
        )
        logger.info(f"Consul service registered: community-service-{port}")

    from .database import engine, Base
    from .models import Post, Comment, PostLike, PostFavorite, PostTag, Report, Topic, BestAnswer

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    from .events.producer import event_bus
    if event_bus and hasattr(event_bus, '_enabled') and event_bus._enabled:
        await event_bus.start()
        logger.info("Kafka event bus started")

    from .events.consumer import user_event_consumer
    if user_event_consumer and hasattr(user_event_consumer, '_enabled') and user_event_consumer._enabled:
        import asyncio
        asyncio.create_task(user_event_consumer.start())
        logger.info("Kafka user event consumer started")

    from .scheduler import hot_score_scheduler
    from .database import AsyncSessionLocal
    hot_score_scheduler.set_db_session_factory(AsyncSessionLocal)
    hot_score_scheduler.start()
    logger.info("Hot score scheduler started")

    yield

    if _redis_client:
        await _redis_client.close()
        logger.info("Redis connection closed")

    if _redis_for_rate_limit and _redis_for_rate_limit != _redis_client:
        await _redis_for_rate_limit.close()

    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        port = int(os.getenv("SERVICE_PORT", "8007"))
        await consul.deregister_service(f"community-service-{port}")
        logger.info(f"Consul service deregistered: community-service-{port}")

    if event_bus and hasattr(event_bus, '_enabled') and event_bus._enabled:
        await event_bus.close()
        logger.info("Kafka event bus closed")

    from .events.consumer import user_event_consumer
    if user_event_consumer and hasattr(user_event_consumer, '_enabled') and user_event_consumer._enabled:
        await user_event_consumer.close()
        logger.info("Kafka user event consumer closed")

    from .scheduler import hot_score_scheduler
    hot_score_scheduler.stop()

    await rate_limiter.close()
    await engine.dispose()
    logger.info("Community service stopped")


def create_app() -> FastAPI:
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    from .errors import (
        CommunityException,
        community_exception_handler,
        validation_exception_handler,
        http_exception_handler,
        generic_exception_handler,
    )

    app = FastAPI(
        title="Community Service",
        description="社区服务 - 法律问答社区",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_exception_handler(CommunityException, community_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)

    from .routers import (
        post_router, comment_router, hot_router,
        admin_router, report_router, favorite_router, topic_router, agent_router
    )
    from .routers.metrics import router as metrics_router
    from .routers.moderation import router as moderation_router
    from .routers.dashboard import router as dashboard_router
    from .routers.ops import (
        ops_auth_router, audit_log_router, content_ops_router,
        user_ops_router, topic_ops_router, analytics_ops_router,
        config_ops_router, announcement_router
    )

    app.include_router(post_router, prefix="/api/v1/community/posts", tags=["帖子"])
    app.include_router(comment_router, prefix="/api/v1/community/comments", tags=["评论"])
    app.include_router(hot_router, prefix="/api/v1/community/hot", tags=["热门内容"])
    app.include_router(admin_router, prefix="/api/v1/community/admin", tags=["管理后台"])
    app.include_router(report_router, prefix="/api/v1/community/reports", tags=["举报"])
    app.include_router(favorite_router, prefix="/api/v1/community/favorites", tags=["收藏"])
    app.include_router(topic_router, prefix="/api/v1/community/topics", tags=["话题"])
    app.include_router(metrics_router)
    app.include_router(moderation_router, prefix="/api/v1/community/admin/moderation", tags=["审核管理"])
    app.include_router(dashboard_router, prefix="/api/v1/community/admin/dashboard", tags=["数据看板"])
    app.include_router(ops_auth_router, prefix="/api/v1/community/ops", tags=["运营认证"])
    app.include_router(audit_log_router, prefix="/api/v1/community/ops/audit", tags=["审计日志"])
    app.include_router(content_ops_router, prefix="/api/v1/community/ops/content", tags=["内容审核"])
    app.include_router(user_ops_router, prefix="/api/v1/community/ops/users", tags=["用户运营"])
    app.include_router(topic_ops_router, prefix="/api/v1/community/ops/topics", tags=["话题运营"])
    app.include_router(analytics_ops_router, prefix="/api/v1/community/ops/analytics", tags=["运营分析"])
    app.include_router(config_ops_router, prefix="/api/v1/community/ops/config", tags=["运营配置"])
    app.include_router(announcement_router, prefix="/api/v1/community/ops/announcements", tags=["社区公告"])
    app.include_router(agent_router, prefix="/api/v1/community/agent", tags=["AI运营助手"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "community-service"}

    @app.get("/health/ready")
    async def readiness_check(request: Request):
        from .database import get_db
        checks = {}

        try:
            async for db_session in get_db():
                await db_session.execute(text("SELECT 1"))
                checks["database"] = "ok"
                break
        except Exception as e:
            logger.error(f"Database readiness check failed: {e}")
            checks["database"] = "fail"

        try:
            if _redis_client:
                await _redis_client.ping()
                checks["redis"] = "ok"
            else:
                checks["redis"] = "skipped"
        except Exception as e:
            logger.warning(f"Redis readiness check failed: {e}")
            checks["redis"] = "fail"

        from .events.producer import event_bus
        if event_bus and hasattr(event_bus, '_enabled') and event_bus._enabled:
            checks["kafka"] = "ok" if event_bus._started else "fail"
        else:
            checks["kafka"] = "skipped"

        all_ok = all(v == "ok" for v in checks.values())
        return JSONResponse(
            status_code=200 if all_ok else 503,
            content={
                "status": "ready" if all_ok else "not_ready",
                "checks": checks
            }
        )

    @app.get("/health/live")
    async def liveness_check():
        return {
            "status": "alive",
            "uptime": round(time.time() - _start_time, 2)
        }

    return app


app = create_app()
