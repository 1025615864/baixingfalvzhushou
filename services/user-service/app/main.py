"""用户服务主应用"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from .config.settings import get_settings
from .database import engine, AsyncSessionLocal, Base
from .routers import user_router, auth_router, profile_router

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("User service starting...")

    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # 关闭时
    logger.info("User service shutting down...")
    await engine.dispose()


def create_app() -> FastAPI:
    """创建应用实例"""
    app = FastAPI(
        title="User Service",
        description="用户服务 - 用户账号、认证、用户画像",
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
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证"])
    app.include_router(user_router, prefix="/api/v1/users", tags=["用户"])
    app.include_router(profile_router, prefix="/api/v1/profiles", tags=["用户画像"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "user-service"}

    @app.get("/health/ready")
    async def readiness_check():
        # TODO: 检查数据库连接
        return {"status": "ready"}

    return app


app = create_app()


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session
