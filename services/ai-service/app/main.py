"""AI服务主应用"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .database import engine, Base
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


def get_cors_config() -> dict:
    return settings.get_cors_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI service starting...")

    init_telemetry(
        service_name="ai-service",
        service_version="1.0.0",
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    )

    consul = get_consul_registry()
    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        host = os.getenv("SERVICE_HOST", "localhost")
        port = int(os.getenv("SERVICE_PORT", "8005"))
        await consul.register_service(
            service_name="ai-service",
            service_id=f"ai-service-{port}",
            host=host,
            port=port,
            metadata={"version": "1.0.0"},
            tags=["http", "ai"],
            health_check_url=f"http://{host}:{port}/health",
        )

    if os.getenv("ENABLE_KAFKA_PRODUCER", "false").lower() == "true":
        from .events import init_kafka_producer
        kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        await init_kafka_producer(kafka_bootstrap)
        logger.info("AI service Kafka producer initialized")

    kafka_consumer = None
    if os.getenv("ENABLE_KAFKA_CONSUMER", "false").lower() == "true":
        from .events.consumer import user_event_consumer
        import asyncio
        asyncio.create_task(user_event_consumer.start())
        kafka_consumer = user_event_consumer
        logger.info("AI service Kafka consumer started")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from .database import import_audit_log_model
    AuditLog = import_audit_log_model()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("预加载向量模型...")
    try:
        from app.services.knowledge_vector_store import knowledge_vector_store
        knowledge_vector_store.get_or_create_collection()
        knowledge_vector_store.count()
        logger.info("知识库向量模型预加载完成")
    except Exception as e:
        logger.warning(f"知识库向量模型预加载失败: {e}")

    try:
        from app.services.archive_vector_store import archive_vector_store
        archive_vector_store.get_or_create_collection()
        archive_vector_store.count()
        logger.info("档案库向量模型预加载完成")
    except Exception as e:
        logger.warning(f"档案库向量模型预加载失败: {e}")

    yield

    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        port = int(os.getenv("SERVICE_PORT", "8005"))
        await consul.deregister_service(f"ai-service-{port}")

    logger.info("AI service shutting down...")

    if kafka_consumer:
        await kafka_consumer.close()
        logger.info("AI service Kafka consumer stopped")

    if os.getenv("ENABLE_KAFKA_PRODUCER", "false").lower() == "true":
        from .events import close_kafka_producer
        await close_kafka_producer()

    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Service",
        description="AI服务 - 法律助手Agent、RAG、模型路由",
        version="1.0.0",
        lifespan=lifespan,
    )

    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)

    from .routers import chat_router, agent_router, config_router, metrics_router, websocket_router, health_router
    from .routers.ai_ops import router as ai_ops_router
    from .routers.audit_ops import router as audit_ops_router
    app.include_router(chat_router, prefix="/api/v1/ai", tags=["AI对话"])
    app.include_router(ai_ops_router, tags=["AI质量运营"])
    app.include_router(agent_router, prefix="/api/v1/ai/admin/agents", tags=["Agent管理"])
    app.include_router(config_router, prefix="/api/v1/ai/admin/config", tags=["配置管理"])
    app.include_router(metrics_router, prefix="/api/v1/ai", tags=["监控指标"])
    app.include_router(health_router, prefix="/api/v1/health", tags=["健康检查"])
    app.include_router(websocket_router, tags=["WebSocket"])
    app.include_router(audit_ops_router, tags=["审计日志运营"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "ai-service"}

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
