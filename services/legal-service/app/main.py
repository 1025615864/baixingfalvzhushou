"""法律服务主应用"""
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
    logger.info("Legal service starting...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("Legal service shutting down...")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Legal Service",
        description="法律服务 - 咨询、律师、律所",
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

    from .routers import consultation_router, lawyer_router, firm_router
    app.include_router(consultation_router, prefix="/api/v1/legal/consultations", tags=["咨询"])
    app.include_router(lawyer_router, prefix="/api/v1/legal/lawyers", tags=["律师"])
    app.include_router(firm_router, prefix="/api/v1/legal/firms", tags=["律所"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "legal-service"}

    @app.get("/health/ready")
    async def readiness_check():
        return {"status": "ready"}

    return app


app = create_app()
