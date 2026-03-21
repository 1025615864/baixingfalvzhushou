"""搜索服务主应用"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Search service starting...")
    yield
    logger.info("Search service shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(title="Search Service", description="搜索服务", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    from .routers import search_router
    app.include_router(search_router, prefix="/api/v1/search", tags=["搜索"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "search-service"}

    return app


app = create_app()
