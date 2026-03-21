"""社区服务主应用"""
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
    logger.info("Community service starting...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Community Service", description="社区服务", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    from .routers import post_router, comment_router
    app.include_router(post_router, prefix="/api/v1/community/posts", tags=["帖子"])
    app.include_router(comment_router, prefix="/api/v1/community/comments", tags=["评论"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "community-service"}

    return app


app = create_app()
