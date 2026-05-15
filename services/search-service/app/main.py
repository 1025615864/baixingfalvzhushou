from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import search_router, agent_router
from app.routers.admin import admin_router
from app.config.settings import settings
from app.services.cache_service import cache_service
from app.services.client_service import client_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    await cache_service.close()
    await client_service.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="搜索服务 - 跨服务聚合搜索",
    lifespan=lifespan,
)

origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, prefix="/api/v1/search", tags=["search"])
app.include_router(admin_router, prefix="/api/admin", tags=["搜索管理"])
app.include_router(agent_router, prefix="/api/agent", tags=["AI运营助手"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/health/live")
async def liveness_check():
    return {"status": "alive", "service": settings.APP_NAME}


@app.get("/health/ready")
async def readiness_check():
    checks = {
        "service": True,
        "cache": cache_service.is_available,
    }
    ready = all(checks.values())
    return {
        "status": "ready" if ready else "degraded",
        "service": settings.APP_NAME,
        "checks": checks,
    }
