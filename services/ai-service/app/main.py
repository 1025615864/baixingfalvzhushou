"""AI服务主应用"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .database import engine, Base

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI service starting...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("AI service shutting down...")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Service",
        description="AI服务 - 法律助手Agent、RAG、模型路由",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from .routers import chat_router, agent_router, config_router
    app.include_router(chat_router, prefix="/api/v1/ai", tags=["AI对话"])
    app.include_router(agent_router, prefix="/api/v1/ai/admin/agents", tags=["Agent管理"])
    app.include_router(config_router, prefix="/api/v1/ai/admin/config", tags=["配置管理"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "ai-service"}

    @app.get("/health/ready")
    async def readiness_check():
        return {"status": "ready"}

    return app


app = create_app()
