"""支付通道服务主应用"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .database import engine, AsyncSessionLocal, Base
from .routers import order_router, callback_router

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Payment channel service starting...")

    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

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

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(order_router, prefix="/api/v1/payment", tags=["支付订单"])
    app.include_router(callback_router, prefix="/api/v1/payment/callbacks", tags=["支付回调"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "payment-channel-service"}

    @app.get("/health/ready")
    async def readiness_check():
        return {"status": "ready"}

    return app


app = create_app()
