"""档案库服务 - FastAPI应用"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.routers import stats_router, archive_router, case_categories_router, search_router, vector_ops_router, vector_search_router, batch_router, recommendations_router
from shared.discovery import get_registration
from shared.tracing import setup_tracing, instrument_fastapi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

tracer = None
consul_registration = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global tracer, consul_registration

    try:
        tracer = setup_tracing(service_name=settings.service_name)
        logger.info(f"Tracing initialized for service: {settings.service_name}")
    except Exception as e:
        logger.warning(f"Failed to initialize tracing: {e}")

    try:
        instrument_fastapi(app)
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI: {e}")

    consul_registration = get_registration(
        service_name=settings.service_name,
        service_port=settings.service_port,
        service_host=settings.service_host,
    )
    if consul_registration:
        consul_registration.register()

    yield

    if consul_registration:
        consul_registration.deregister()


app = FastAPI(
    title="档案库服务",
    description="案例档案管理服务",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    **settings.get_cors_config()
)

app.include_router(stats_router)
app.include_router(archive_router)
app.include_router(case_categories_router)
app.include_router(search_router)
app.include_router(vector_ops_router)
app.include_router(vector_search_router)
app.include_router(batch_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name}


@app.get("/health/ready")
async def readiness_check():
    return {"status": "ready", "service": settings.service_name}


@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "version": "1.0.0",
        "description": "案例档案管理服务"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.service_host, port=settings.service_port)
