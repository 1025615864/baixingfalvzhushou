"""用户服务主应用"""
import logging
import os
import asyncio
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from .config.settings import get_settings
from .database import engine, AsyncSessionLocal, Base
from .routers import user_router, auth_router, profile_router, ai_session_router, membership_router, password_reset_router, account_router, data_export_router, email_verification_router, device_router
from .utils.security import setup_secure_logging

try:
    from services.common.security import get_cors_config
except ImportError:
    def get_cors_config():
        return {
            "allow_origins": ["*"],
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

settings = get_settings()
logger = logging.getLogger(__name__)

grpc_server = None
grpc_server_task = None


async def start_grpc_server():
    """启动gRPC服务器"""
    global grpc_server, grpc_server_task
    if os.getenv("ENABLE_GRPC_SERVER", "false").lower() == "true":
        from .grpc_server import serve_grpc
        grpc_port = int(os.getenv("GRPC_PORT", "50051"))
        grpc_server_task = asyncio.create_task(serve_grpc(grpc_port))
        logger.info(f"gRPC server task started on port {grpc_port}")


async def stop_grpc_server():
    """停止gRPC服务器"""
    global grpc_server, grpc_server_task
    if grpc_server_task:
        grpc_server_task.cancel()
        try:
            await grpc_server_task
        except asyncio.CancelledError:
            pass
        logger.info("gRPC server stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    setup_secure_logging()
    logger.info("User service starting...")

    init_telemetry(
        service_name="user-service",
        service_version="1.0.0",
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    )

    consul = get_consul_registry()
    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        host = os.getenv("SERVICE_HOST", "localhost")
        port = int(os.getenv("SERVICE_PORT", "8001"))
        await consul.register_service(
            service_name="user-service",
            service_id=f"user-service-{port}",
            host=host,
            port=port,
            metadata={"version": "1.0.0"},
            tags=["http", "grpc"],
            health_check_url=f"http://{host}:{port}/health",
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if os.getenv("ENABLE_GRPC_CLIENT", "false").lower() == "true":
        from .clients import init_grpc_clients
        use_tls = os.getenv("GRPC_USE_TLS", "false").lower() == "true"
        init_grpc_clients(use_tls=use_tls)
        logger.info(f"gRPC clients initialized (TLS: {use_tls})")

    if os.getenv("ENABLE_KAFKA_PRODUCER", "false").lower() == "true":
        from .events import init_kafka_producer
        kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        await init_kafka_producer(kafka_bootstrap)
        logger.info("Kafka producer initialized")

    kafka_consumer = None
    if os.getenv("ENABLE_KAFKA_CONSUMER", "false").lower() == "true":
        from .events.consumer import user_event_consumer
        asyncio.create_task(user_event_consumer.start())
        kafka_consumer = user_event_consumer
        logger.info("Kafka consumer started")

    outbox_publisher = None
    if os.getenv("ENABLE_OUTBOX", "true").lower() in {"1", "true", "yes"}:
        from .events.outbox_publisher import outbox_publisher as publisher
        await publisher.start()
        outbox_publisher = publisher
        logger.info("Outbox publisher started")

    membership_task = None
    if os.getenv("ENABLE_MEMBERSHIP_EXPIRY_CHECK", "true").lower() in {"1", "true", "yes"}:
        from .tasks.membership_task import membership_expiry_task
        await membership_expiry_task.start()
        membership_task = membership_expiry_task
        logger.info("Membership expiry task started")

    await start_grpc_server()

    yield

    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        port = int(os.getenv("SERVICE_PORT", "8001"))
        await consul.deregister_service(f"user-service-{port}")

    logger.info("User service shutting down...")

    await stop_grpc_server()

    if membership_task:
        await membership_task.stop()
        logger.info("Membership expiry task stopped")

    if outbox_publisher:
        await outbox_publisher.stop()
        logger.info("Outbox publisher stopped")

    if kafka_consumer:
        await kafka_consumer.close()
        logger.info("Kafka consumer stopped")

    if os.getenv("ENABLE_GRPC_CLIENT", "false").lower() == "true":
        from .clients import close_grpc_clients
        close_grpc_clients()

    if os.getenv("ENABLE_KAFKA_PRODUCER", "false").lower() == "true":
        from .events import close_kafka_producer
        await close_kafka_producer()

    await engine.dispose()


def create_app() -> FastAPI:
    """创建应用实例"""
    from .errors.exception_handlers import register_exception_handlers

    app = FastAPI(
        title="User Service",
        description="用户服务 - 用户账号、认证、用户画像",
        version="1.0.0",
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证"])
    app.include_router(user_router, prefix="/api/v1/users", tags=["用户"])
    app.include_router(profile_router, prefix="/api/v1/profiles", tags=["用户画像"])
    app.include_router(membership_router, prefix="/api/v1/membership", tags=["会员"])
    app.include_router(account_router, prefix="/api/v1/account", tags=["账号"])
    app.include_router(data_export_router, prefix="/api/v1/account", tags=["数据导出"])
    app.include_router(email_verification_router, prefix="/api/v1/auth", tags=["邮箱验证"])
    app.include_router(ai_session_router, prefix="/api/v1", tags=["AI会话"])
    app.include_router(device_router, prefix="/api/v1/devices", tags=["设备管理"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "user-service"}

    @app.get("/health/ready")
    async def readiness_check():
        from fastapi.responses import JSONResponse
        from sqlalchemy import text

        checks = {}
        all_ok = True

        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = "fail"
            all_ok = False
            logger.error(f"Database health check failed: {e}")

        try:
            from .services.redis_service import redis_service
            if redis_service.is_connected:
                await redis_service.redis.ping()
            checks["redis"] = "ok" if redis_service.is_connected else "degraded"
        except Exception as e:
            checks["redis"] = "fail"
            all_ok = False
            logger.error(f"Redis health check failed: {e}")

        status_code = 200 if all_ok else 503
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ready" if all_ok else "degraded",
                "checks": checks,
            }
        )

    @app.get("/health/live")
    async def liveness_check():
        return {"status": "alive"}

    return app


app = create_app()


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session
