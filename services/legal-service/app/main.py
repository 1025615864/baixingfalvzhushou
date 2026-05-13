"""法律服务主应用"""
import logging
import os
import time
import asyncio
from contextlib import asynccontextmanager
from concurrent import futures
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
import redis.asyncio as redis
import grpc

from .config.settings import get_settings
from .utils.logging_config import setup_logging
from .errors import (
    LegalException,
    legal_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)

settings = get_settings()
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

try:
    from services.common.security import get_cors_config
except ImportError:
    def get_cors_config():
        return {
            "allow_origins": os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

try:
    from services.common.tracing import init_telemetry
except ImportError:
    def init_telemetry(*args, **kwargs):
        pass

try:
    from services.common.discovery import get_consul_registry
except ImportError:
    def get_consul_registry(*args, **kwargs):
        return None

try:
    from services.common.proto import legal_pb2_grpc
except ImportError:
    legal_pb2_grpc = None

_redis_client: redis.Redis = None
_redis_for_rate_limit: redis.Redis = None
_start_time = time.time()
_grpc_server = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis_client, _redis_for_rate_limit, _grpc_server
    logger.info("Legal service starting...")

    init_telemetry(
        service_name="legal-service",
        service_version="1.0.0",
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    )
    logger.info("OpenTelemetry initialized")

    if os.getenv("REDIS_URL"):
        try:
            _redis_client = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True
            )
            await _redis_client.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            _redis_client = None

    if os.getenv("REDIS_URL"):
        try:
            _redis_for_rate_limit = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True
            )
        except Exception:
            logger.error("限流Redis连接初始化失败")
            _redis_for_rate_limit = None

    from .middleware.rate_limit import rate_limiter
    rate_limiter._client = _redis_for_rate_limit

    consul = get_consul_registry()
    if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"}:
        host = os.getenv("SERVICE_HOST", "localhost")
        port = int(os.getenv("SERVICE_PORT", "8004"))
        await consul.register_service(
            service_name="legal-service",
            service_id=f"legal-service-{port}",
            host=host,
            port=port,
            metadata={"version": "1.0.0"},
            tags=["http", "grpc"],
            health_check_url=f"http://{host}:{port}/health",
        )
        logger.info(f"Consul service registered: legal-service-{port}")

    from .database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    from .events.producer import event_bus
    if event_bus and hasattr(event_bus, '_enabled') and event_bus._enabled:
        await event_bus.start()
        logger.info("Kafka event bus started")

    from .events.consumer import user_event_consumer
    if user_event_consumer and hasattr(user_event_consumer, '_enabled') and user_event_consumer._enabled:
        asyncio.create_task(user_event_consumer.start())
        logger.info("Kafka user event consumer started")

    grpc_port = int(os.getenv("GRPC_PORT", settings.grpc_port))
    _grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    from .database import AsyncSessionLocal
    from .grpc_server import SyncLegalServiceServicer
    if legal_pb2_grpc:
        servicer = SyncLegalServiceServicer(AsyncSessionLocal, _redis_client)
        legal_pb2_grpc.add_LegalServiceServicer_to_server(servicer, _grpc_server)
        _grpc_server.add_insecure_port(f"[::]:{grpc_port}")
        _grpc_server.start()
        logger.info(f"gRPC server started on port {grpc_port}")
    else:
        logger.warning("legal_pb2_grpc not available, gRPC server not started")

    from .services.appointment_scheduler import get_scheduler
    scheduler = get_scheduler(AsyncSessionLocal)
    await scheduler.start(interval_seconds=60)
    logger.info("Appointment timeout scheduler started")

    yield

    from .services.outbox_service import OutboxPublisher
    from .database import AsyncSessionLocal

    async def flush_outbox():
        if event_bus and hasattr(event_bus, '_enabled') and event_bus._enabled and event_bus._producer:
            outbox_pub = OutboxPublisher(AsyncSessionLocal, event_bus._producer)
            await outbox_pub.publish_pending_events()
            logger.info("Outbox events flushed before shutdown")

    async def log_shutdown(step: str, action):
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        logger.info(f"[{timestamp}] Shutting down: {step}")
        try:
            result = action()
            if asyncio.iscoroutine(result):
                await result
            logger.info(f"[{timestamp}] Shut down completed: {step}")
        except Exception as e:
            logger.error(f"[{timestamp}] Error shutting down {step}: {e}")

    SHUTDOWN_ORDER = [
        ("gRPC Server", lambda: _grpc_server.stop(grace=5) if _grpc_server else None),
        ("Appointment Scheduler", lambda: scheduler.stop() if 'scheduler' in dir() else None),
        ("Kafka Consumer (user events)", lambda: user_event_consumer.close() if user_event_consumer and hasattr(user_event_consumer, '_enabled') and user_event_consumer._enabled else None),
        ("Outbox Publisher (flush remaining events)", flush_outbox),
        ("Kafka Producer (event bus)", lambda: event_bus.close() if event_bus and hasattr(event_bus, '_enabled') and event_bus._enabled else None),
        ("Rate Limiter", lambda: rate_limiter.close()),
        ("Redis (rate limit)", lambda: _redis_for_rate_limit.close() if _redis_for_rate_limit and _redis_for_rate_limit != _redis_client else None),
        ("Redis (main)", lambda: _redis_client.close() if _redis_client else None),
        ("Consul Service Discovery", lambda: consul.deregister_service(f"legal-service-{os.getenv('SERVICE_PORT', '8004')}") if consul and os.getenv("CONSUL_ENABLED", "").lower() in {"1", "true", "yes"} else None),
        ("Database", lambda: engine.dispose()),
    ]

    for name, action in SHUTDOWN_ORDER:
        await log_shutdown(name, action)

    logger.info("Legal service shutdown completed")


def create_app() -> FastAPI:

    app = FastAPI(
        title="Legal Service",
        description="法律服务 - 咨询、律师、律所",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_exception_handler(LegalException, legal_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)

    from .middleware.idempotency import IdempotencyMiddleware
    if _redis_client:
        app.add_middleware(IdempotencyMiddleware, redis_client=_redis_client)

    from .routers import consultation_router, lawyer_router, firm_router, review_router, appointment_router, schedule_router, admin_router, cache_admin_router, document_router
    from .routers.invitation import router as invitation_router
    from .routers.firm_admin import router as firm_admin_router
    from .routers.metrics import router as metrics_router

    app.include_router(consultation_router, prefix="/api/v1/legal/consultations", tags=["咨询"])
    app.include_router(lawyer_router, prefix="/api/v1/legal/lawyers", tags=["律师"])
    app.include_router(firm_router, prefix="/api/v1/legal/firms", tags=["律所"])
    app.include_router(invitation_router, prefix="/api/v1/legal/invitations", tags=["邀请"])
    app.include_router(firm_admin_router, prefix="/api/v1/legal/admin", tags=["律所管理"])
    app.include_router(review_router, prefix="/api/v1/legal/reviews", tags=["评价"])
    app.include_router(appointment_router, prefix="/api/v1/legal/appointments", tags=["预约"])
    app.include_router(schedule_router, prefix="/api/v1/legal/schedules", tags=["排班"])
    app.include_router(admin_router, prefix="/api/v1/legal/admin", tags=["管理"])
    app.include_router(cache_admin_router, prefix="/api/v1/legal/cache", tags=["缓存管理"])
    app.include_router(metrics_router, prefix="/api/v1/legal/metrics", tags=["监控"])
    app.include_router(document_router, prefix="/api/v1/legal/documents", tags=["文书"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "legal-service"}

    @app.get("/health/ready")
    async def readiness_check(request: Request):
        from .database import get_db
        checks = {}

        try:
            async for db_session in get_db():
                await db_session.execute(text("SELECT 1"))
                checks["database"] = "ok"
                break
        except Exception as e:
            logger.error(f"Database readiness check failed: {e}")
            checks["database"] = "fail"

        try:
            if _redis_client:
                await _redis_client.ping()
                checks["redis"] = "ok"
            else:
                checks["redis"] = "skipped"
        except Exception as e:
            logger.warning(f"Redis readiness check failed: {e}")
            checks["redis"] = "fail"

        from .events.producer import event_bus
        if event_bus and hasattr(event_bus, '_enabled') and event_bus._enabled:
            checks["kafka"] = "ok" if event_bus._started else "fail"
        else:
            checks["kafka"] = "skipped"

        all_ok = all(v == "ok" for v in checks.values())
        return JSONResponse(
            status_code=200 if all_ok else 503,
            content={
                "status": "ready" if all_ok else "not_ready",
                "checks": checks
            }
        )

    @app.get("/health/live")
    async def liveness_check():
        return {
            "status": "alive",
            "uptime": round(time.time() - _start_time, 2)
        }

    return app


app = create_app()