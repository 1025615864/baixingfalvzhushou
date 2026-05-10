"""订单服务主应用"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models.order import Base as OrderBase

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

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Order service starting...")

    init_telemetry(
        service_name="order-service",
        service_version="1.0.0",
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    )

    # 数据库初始化
    async with engine.begin() as conn:
        await conn.run_sync(OrderBase.metadata.create_all)

    consul = get_consul_registry()
    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        host = os.getenv("SERVICE_HOST", "localhost")
        port = int(os.getenv("SERVICE_PORT", "8014"))
        await consul.register_service(
            service_name="order-service",
            service_id=f"order-service-{port}",
            host=host,
            port=port,
            metadata={"version": "1.0.0"},
            tags=["http", "saga", "orders"],
            health_check_url=f"http://{host}:{port}/health",
        )

    if os.getenv("ENABLE_SAGA_PERSISTENCE", "false").lower() == "true":
        from app.sagas import init_saga_persistence
        await init_saga_persistence()
        logger.info("Order service Saga persistence initialized")

    yield

    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        port = int(os.getenv("SERVICE_PORT", "8014"))
        await consul.deregister_service(f"order-service-{port}")

    if os.getenv("ENABLE_SAGA_PERSISTENCE", "false").lower() == "true":
        from app.sagas import close_saga_persistence
        await close_saga_persistence()

    logger.info("Order service shutting down...")


def create_app() -> FastAPI:
    """创建应用实例"""
    app = FastAPI(
        title="Order Service",
        description="订单服务 - 订单管理、SAGA 分布式事务",
        version="1.0.0",
        lifespan=lifespan,
    )

    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)

    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "order-service"}

    @app.get("/health/ready")
    async def readiness_check():
        return {"status": "ready"}

    @app.get("/health/live")
    async def liveness_check():
        return {"status": "alive"}

    # 注册路由
    from app.routers.orders import router as orders_router
    from app.routers.orders import admin_router as admin_orders_router
    app.include_router(orders_router)
    app.include_router(admin_orders_router)

    return app


app = create_app()
