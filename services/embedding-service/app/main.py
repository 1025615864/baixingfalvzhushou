import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config.settings import get_settings
from app.services.embedding_service import get_embedding_service

settings = get_settings()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    device: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting embedding service...")
    service = get_embedding_service()
    yield
    logger.info("Shutting down embedding service...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Embedding Service",
        description="共享Embedding模型微服务",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.routers import embedding_router, admin_router
    app.include_router(embedding_router, prefix="/api/v1/embeddings", tags=["Embedding"])
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        service = get_embedding_service()
        return HealthResponse(
            status="healthy",
            model_loaded=service.is_model_loaded(),
            model_name=service.model_name,
            device=service.device,
        )

    @app.get("/health/ready")
    async def readiness_check():
        service = get_embedding_service()
        if not service.is_model_loaded():
            return {"status": "not_ready", "reason": "model not loaded"}
        return {"status": "ready"}

    @app.get("/health/live")
    async def liveness_check():
        return {"status": "alive"}

    @app.get("/")
    async def root():
        service = get_embedding_service()
        return {
            "service": "embedding-service",
            "version": "1.0.0",
            "model": service.model_name,
            "dimension": service.embedding_dim,
            "device": service.device,
            "model_loaded": service.is_model_loaded(),
        }

    return app


app = create_app()
