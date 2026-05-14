"""新闻服务主应用"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import get_settings
from .database import engine, Base
from sqlalchemy import text
from .routers import news_router, comment_router, subscription_router, admin_router, agent_router

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
    logger.info("News service starting...")

    init_telemetry(
        service_name="news-service",
        service_version="1.0.0",
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    )

    consul = get_consul_registry()
    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        host = os.getenv("SERVICE_HOST", "localhost")
        port = int(os.getenv("SERVICE_PORT", "8006"))
        await consul.register_service(
            service_name="news-service",
            service_id=f"news-service-{port}",
            host=host,
            port=port,
            metadata={"version": "1.0.0"},
            tags=["http", "kafka"],
            health_check_url=f"http://{host}:{port}/health",
        )

    if os.getenv("KAFKA_ENABLED", "false").lower() == "true":
        from .events import init_kafka_producer
        kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        await init_kafka_producer(kafka_bootstrap)
        logger.info("News service Kafka producer initialized")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        port = int(os.getenv("SERVICE_PORT", "8006"))
        await consul.deregister_service(f"news-service-{port}")

    if os.getenv("KAFKA_ENABLED", "false").lower() == "true":
        from .events import close_kafka_producer
        await close_kafka_producer()

    from .services.news_agent_service import news_agent_service
    await news_agent_service.close()

    logger.info("News service shutting down...")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="News Service", description="新闻服务", version="1.0.0", lifespan=lifespan)

    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)

    app.include_router(news_router, prefix="/api/v1/news", tags=["新闻"])
    app.include_router(comment_router, prefix="/api/v1/news/comments", tags=["评论"])
    app.include_router(subscription_router, prefix="/api/v1/news/subscriptions", tags=["订阅"])
    app.include_router(admin_router, prefix="/api/v1/news/admin", tags=["新闻管理"])
    app.include_router(agent_router, prefix="/api/v1/news/agent", tags=["新闻运营助手"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "news-service"}

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
