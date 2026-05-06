"""推荐服务主应用"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import get_settings

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Recommendation service starting...")

    init_telemetry(
        service_name="recommendation-service",
        service_version="1.0.0",
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    )

    consul = get_consul_registry()
    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        host = os.getenv("SERVICE_HOST", "localhost")
        port = int(os.getenv("SERVICE_PORT", "8010"))
        await consul.register_service(
            service_name="recommendation-service",
            service_id=f"recommendation-service-{port}",
            host=host,
            port=port,
            metadata={"version": "1.0.0"},
            tags=["http"],
            health_check_url=f"http://{host}:{port}/health",
        )

    yield

    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        port = int(os.getenv("SERVICE_PORT", "8010"))
        await consul.deregister_service(f"recommendation-service-{port}")

    logger.info("Recommendation service shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(title="Recommendation Service", description="推荐服务", version="1.0.0", lifespan=lifespan)

    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)

    from .routers import recommendation_router
    app.include_router(recommendation_router, prefix="/api/v1/recommendations", tags=["推荐"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "recommendation-service"}

    @app.get("/health/ready")
    async def readiness_check():
        return {"status": "ready"}

    @app.get("/health/live")
    async def liveness_check():
        return {"status": "alive"}

    return app


app = create_app()
