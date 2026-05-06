"""健康检查与依赖服务状态路由"""
import asyncio
import time
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config.settings import get_settings

router = APIRouter(tags=["健康检查"])

logger = logging.getLogger(__name__)


@dataclass
class ServiceStatus:
    name: str
    healthy: bool
    latency_ms: int
    message: str
    last_check: str


class VectorStoreHealth(BaseModel):
    knowledge_collection: str
    knowledge_count: int
    archive_collection: str
    archive_count: int
    healthy: bool


class DependencyServiceHealth(BaseModel):
    llm_provider: ServiceStatus
    user_service: ServiceStatus
    backend_rag: ServiceStatus


class OverallHealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    vector_store: VectorStoreHealth
    dependencies: DependencyServiceHealth


async def check_llm_provider() -> ServiceStatus:
    """检查LLM服务可用性"""
    start = time.time()
    try:
        from app.services.llm_client import get_resilient_llm_client
        client = get_resilient_llm_client()

        if hasattr(client, 'circuit_breaker'):
            state = client.circuit_breaker.state
            if state.value == "open":
                return ServiceStatus(
                    name="llm_provider",
                    healthy=False,
                    latency_ms=int((time.time() - start) * 1000),
                    message=f"Circuit breaker OPEN",
                    last_check=datetime.now().isoformat()
                )

        return ServiceStatus(
            name="llm_provider",
            healthy=True,
            latency_ms=int((time.time() - start) * 1000),
            message="Available",
            last_check=datetime.now().isoformat()
        )
    except Exception as e:
        return ServiceStatus(
            name="llm_provider",
            healthy=False,
            latency_ms=int((time.time() - start) * 1000),
            message=f"Error: {str(e)}",
            last_check=datetime.now().isoformat()
        )


async def check_user_service() -> ServiceStatus:
    """检查用户服务可用性"""
    start = time.time()
    try:
        import httpx
        settings = get_settings()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.user_service_url}/health",
                timeout=5.0
            )

            if response.status_code == 200:
                return ServiceStatus(
                    name="user_service",
                    healthy=True,
                    latency_ms=int((time.time() - start) * 1000),
                    message="Available",
                    last_check=datetime.now().isoformat()
                )
            else:
                return ServiceStatus(
                    name="user_service",
                    healthy=False,
                    latency_ms=int((time.time() - start) * 1000),
                    message=f"Status: {response.status_code}",
                    last_check=datetime.now().isoformat()
                )
    except httpx.TimeoutException:
        return ServiceStatus(
            name="user_service",
            healthy=False,
            latency_ms=int((time.time() - start) * 1000),
            message="Timeout",
            last_check=datetime.now().isoformat()
        )
    except Exception as e:
        return ServiceStatus(
            name="user_service",
            healthy=False,
            latency_ms=int((time.time() - start) * 1000),
            message=f"Error: {str(e)}",
            last_check=datetime.now().isoformat()
        )


async def check_backend_rag() -> ServiceStatus:
    """检查Backend RAG可用性"""
    start = time.time()
    try:
        import httpx
        settings = get_settings()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.backend_url}/health",
                timeout=5.0
            )

            if response.status_code == 200:
                return ServiceStatus(
                    name="backend_rag",
                    healthy=True,
                    latency_ms=int((time.time() - start) * 1000),
                    message="Available",
                    last_check=datetime.now().isoformat()
                )
            else:
                return ServiceStatus(
                    name="backend_rag",
                    healthy=False,
                    latency_ms=int((time.time() - start) * 1000),
                    message=f"Status: {response.status_code}",
                    last_check=datetime.now().isoformat()
                )
    except httpx.TimeoutException:
        return ServiceStatus(
            name="backend_rag",
            healthy=False,
            latency_ms=int((time.time() - start) * 1000),
            message="Timeout",
            last_check=datetime.now().isoformat()
        )
    except Exception as e:
        return ServiceStatus(
            name="backend_rag",
            healthy=False,
            latency_ms=int((time.time() - start) * 1000),
            message=f"Error: {str(e)}",
            last_check=datetime.now().isoformat()
        )


async def check_vector_stores() -> VectorStoreHealth:
    """检查向量库状态"""
    try:
        from app.services.knowledge_vector_store import get_collection_count as get_knowledge_count
        from app.services.archive_vector_store import get_collection_count as get_archive_count

        knowledge_count = 0
        archive_count = 0

        try:
            knowledge_count = get_knowledge_count()
        except Exception:
            pass

        try:
            archive_count = get_archive_count()
        except Exception:
            pass

        return VectorStoreHealth(
            knowledge_collection="knowledge_laws",
            knowledge_count=knowledge_count,
            archive_collection="archive_cases",
            archive_count=archive_count,
            healthy=True
        )
    except Exception as e:
        return VectorStoreHealth(
            knowledge_collection="knowledge_laws",
            knowledge_count=0,
            archive_collection="archive_cases",
            archive_count=0,
            healthy=False
        )


@router.get("/", response_model=OverallHealthResponse)
async def get_health():
    """获取完整健康状态"""
    settings = get_settings()

    vector_store = await check_vector_stores()

    llm_status = await check_llm_provider()
    user_status = await check_user_service()
    backend_status = await check_backend_rag()

    all_healthy = (
        vector_store.healthy and
        llm_status.healthy and
        user_status.healthy and
        backend_status.healthy
    )

    return OverallHealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        vector_store=vector_store,
        dependencies=DependencyServiceHealth(
            llm_provider=llm_status,
            user_service=user_status,
            backend_rag=backend_status
        )
    )


@router.get("/live")
async def liveness_check():
    """存活检查"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


@router.get("/ready")
async def readiness_check():
    """就绪检查 - 检查所有依赖（标准化格式）"""
    from fastapi.responses import JSONResponse
    from datetime import datetime

    checks = {}
    vector_store = await check_vector_stores()

    checks["database"] = "ok" if vector_store.healthy else "fail"

    try:
        from app.services.knowledge_vector_store import knowledge_vector_store
        checks["knowledge_vector"] = "ok" if knowledge_vector_store else "fail"
    except Exception:
        checks["knowledge_vector"] = "skipped"

    try:
        from app.services.archive_vector_store import archive_vector_store
        checks["archive_vector"] = "ok" if archive_vector_store else "fail"
    except Exception:
        checks["archive_vector"] = "skipped"

    checks["llm_provider"] = "ok" if (await check_llm_provider()).healthy else "fail"

    all_ok = all(v in ("ok", "skipped") for v in checks.values())

    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={
            "status": "ready" if all_ok else "degraded",
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
        }
    )


@router.get("/dependencies")
async def get_dependency_status():
    """获取依赖服务状态"""
    llm = await check_llm_provider()
    user = await check_user_service()
    backend = await check_backend_rag()

    return {
        "llm_provider": {
            "healthy": llm.healthy,
            "latency_ms": llm.latency_ms,
            "message": llm.message
        },
        "user_service": {
            "healthy": user.healthy,
            "latency_ms": user.latency_ms,
            "message": user.message
        },
        "backend_rag": {
            "healthy": backend.healthy,
            "latency_ms": backend.latency_ms,
            "message": backend.message
        }
    }
