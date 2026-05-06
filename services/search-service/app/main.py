"""搜索服务主应用"""
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
    logger.info("Search service starting...")

    init_telemetry(
        service_name="search-service",
        service_version="1.0.0",
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    )

    consul = get_consul_registry()
    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        host = os.getenv("SERVICE_HOST", "localhost")
        port = int(os.getenv("SERVICE_PORT", "8011"))
        await consul.register_service(
            service_name="search-service",
            service_id=f"search-service-{port}",
            host=host,
            port=port,
            metadata={"version": "1.0.0"},
            tags=["http", "kafka"],
            health_check_url=f"http://{host}:{port}/health",
        )

    if os.getenv("ENABLE_KAFKA_PRODUCER", "false").lower() == "true":
        from .events import init_kafka_producer
        kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        await init_kafka_producer(kafka_bootstrap)
        logger.info("Search service Kafka producer initialized")

    yield

    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        port = int(os.getenv("SERVICE_PORT", "8011"))
        await consul.deregister_service(f"search-service-{port}")

    if os.getenv("ENABLE_KAFKA_PRODUCER", "false").lower() == "true":
        from .events import close_kafka_producer
        await close_kafka_producer()

    logger.info("Search service shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(title="Search Service", description="搜索服务", version="1.0.0", lifespan=lifespan)

    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)

    from .routers import search_router
    app.include_router(search_router, prefix="/api/v1/search", tags=["搜索"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "search-service"}

    @app.get("/health/ready")
    async def readiness_check():
        return {"status": "ready"}

    @app.get("/health/live")
    async def liveness_check():
        return {"status": "alive"}

    return app


app = create_app()
