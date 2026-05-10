"""支付通道服务主应用"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .database import engine, AsyncSessionLocal, Base
from .routers import order_router, callback_router, refund_router
from .services.channels import init_adapters

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
    """应用生命周期管理"""
    logger.info("Payment channel service starting...")

    init_telemetry(
        service_name="payment-channel-service",
        service_version="1.0.0",
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    )

    consul = get_consul_registry()
    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        host = os.getenv("SERVICE_HOST", "localhost")
        port = int(os.getenv("SERVICE_PORT", "8002"))
        await consul.register_service(
            service_name="payment-channel-service",
            service_id=f"payment-channel-service-{port}",
            host=host,
            port=port,
            metadata={"version": "1.0.0"},
            tags=["http"],
            health_check_url=f"http://{host}:{port}/health",
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    init_adapters(settings)

    yield

    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        port = int(os.getenv("SERVICE_PORT", "8002"))
        await consul.deregister_service(f"payment-channel-service-{port}")

    logger.info("Payment channel service shutting down...")
    await engine.dispose()


def create_app() -> FastAPI:
    """创建应用实例"""
    app = FastAPI(
        title="Payment Channel Service",
        description="支付通道服务 - 支付订单、回调处理、通道适配",
        version="1.0.0",
        lifespan=lifespan,
    )

    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)

    app.include_router(order_router, prefix="/api/v1/payment", tags=["支付订单"])
    app.include_router(callback_router, prefix="/api/v1/payment/callbacks", tags=["支付回调"])
    app.include_router(refund_router, prefix="/api/v1/payment", tags=["退款管理"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "payment-channel-service"}

    @app.get("/health/ready")
    async def readiness_check():
        return {"status": "ready"}

    @app.get("/health/live")
    async def liveness_check():
        return {"status": "alive"}

    return app


app = create_app()
