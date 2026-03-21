"""推荐服务主应用"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Recommendation service starting...")
    yield
    logger.info("Recommendation service shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(title="Recommendation Service", description="推荐服务", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    from .routers import recommendation_router
    app.include_router(recommendation_router, prefix="/api/v1/recommendations", tags=["推荐"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "recommendation-service"}

    return app


app = create_app()
