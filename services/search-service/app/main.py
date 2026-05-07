"""搜索服务主入口"""
from fastapi import FastAPI
from app.routers import search_router
from app.config.settings import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="搜索服务 - 跨服务聚合搜索",
)

app.include_router(search_router, prefix="/api/v1/search", tags=["search"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
