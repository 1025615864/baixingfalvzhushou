"""通知服务主应用"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import get_settings
from .database import engine
from sqlalchemy import text

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

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Notification service starting...")

    init_telemetry(
        service_name="notification-service",
        service_version="1.0.0",
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    )

    from app.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    kafka_enabled = os.getenv("KAFKA_ENABLED", "false").lower() in {"1", "true", "yes"}
    if kafka_enabled:
        from app.events import init_kafka_consumer
        kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
        await init_kafka_consumer(kafka_bootstrap)

    consul = get_consul_registry()
    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        host = os.getenv("SERVICE_HOST", "localhost")
        port = int(os.getenv("SERVICE_PORT", "8009"))
        await consul.register_service(
            service_name="notification-service",
            service_id=f"notification-service-{port}",
            host=host,
            port=port,
            metadata={"version": "1.0.0"},
            tags=["http", "consumer"],
            health_check_url=f"http://{host}:{port}/health",
        )

    yield

    if kafka_enabled:
        from app.events import close_kafka_consumer
        await close_kafka_consumer()

    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        port = int(os.getenv("SERVICE_PORT", "8009"))
        await consul.deregister_service(f"notification-service-{port}")

    logger.info("Notification service shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(title="Notification Service", description="通知服务", version="1.0.0", lifespan=lifespan)

    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)

    from .routers import notification_router, admin_router
    app.include_router(notification_router, prefix="/api/v1/notifications", tags=["通知"])
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["管理后台"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "notification-service"}

    @app.get("/health/ready")
    async def readiness_check():
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return {"status": "ready"}
        except Exception as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(e)})

    @app.get("/health/live")
    async def liveness_check():
        return {"status": "alive"}

    return app


app = create_app()
