"""通知服务主应用"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Notification service starting...")
    yield
    logger.info("Notification service shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(title="Notification Service", description="通知服务", version="1.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    from .routers import notification_router
    app.include_router(notification_router, prefix="/api/v1/notifications", tags=["通知"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "notification-service"}

    return app


app = create_app()
