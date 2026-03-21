"""新闻服务主应用"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import get_settings
from .database import engine, Base
from .routers import news_router, comment_router, subscription_router

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("News service starting...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("News service shutting down...")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="News Service", description="新闻服务", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    app.include_router(news_router, prefix="/api/v1/news", tags=["新闻"])
    app.include_router(comment_router, prefix="/api/v1/news/comments", tags=["评论"])
    app.include_router(subscription_router, prefix="/api/v1/news/subscriptions", tags=["订阅"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "news-service"}

    return app


app = create_app()
