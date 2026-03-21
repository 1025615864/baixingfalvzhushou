"""账务服务主应用"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .database import engine, Base
from .routers import balance_router, settlement_router

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Accounting service starting...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("Accounting service shutting down...")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Payment Accounting Service",
        description="账务服务 - 余额管理、结算、对账",
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

    app.include_router(balance_router, prefix="/api/v1/balance", tags=["余额"])
    app.include_router(settlement_router, prefix="/api/v1/settlement", tags=["结算"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "payment-accounting-service"}

    @app.get("/health/ready")
    async def readiness_check():
        return {"status": "ready"}

    return app


app = create_app()
