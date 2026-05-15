"""运营API聚合 - 代理知识库和案例库运营操作"""
import logging
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, HTTPException
import httpx

from app.dependencies.auth import require_admin, UserContext

try:
    from services.common.middleware.admin_auth import require_domain_role
except ImportError:
    from fastapi import Request
    class _AdminUser:
        def __init__(self, user_id: int = 0, role: str = "admin", permissions=None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in {"super_admin", "admin"}
    async def _get_admin_user(request: Request = None):
        if request:
            user_id = int(request.headers.get("X-Admin-User-Id", "0"))
            role = request.headers.get("X-Admin-Role", "admin")
            permissions = request.headers.get("X-Admin-Permissions", "").split(",")
            return _AdminUser(user_id=user_id, role=role, permissions=permissions)
        return _AdminUser()
    def require_domain_role(domain: str, roles=None):
        async def _checker(admin: _AdminUser = Depends(_get_admin_user)):
            if admin.is_super_admin:
                return admin
            if roles and admin.role not in roles:
                raise HTTPException(status_code=403, detail=f"需要角色: {', '.join(roles)}")
            return admin
        return _checker

router = APIRouter(
    prefix="/api/v1/ai-ops",
    tags=["运营API聚合"],
    dependencies=[Depends(require_domain_role("ai", roles=["ai_admin", "ai_ops"]))],
)
logger = logging.getLogger(__name__)


class KnowledgeStats(BaseModel):
    total: int
    published: int
    draft: int
    archived: int
    categories: int


class ArchiveStats(BaseModel):
    total: int
    published: int
    draft: int
    archived: int
    guiding_cases: int
    categories: int


class ServiceHealth(BaseModel):
    service: str
    status: str
    latency_ms: Optional[float] = None


async def proxy_to_service(service_url: str, path: str, method: str = "GET", json_data: Optional[dict] = None):
    """代理请求到目标服务"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{service_url}{path}"
        try:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=json_data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail=f"Service at {service_url} is unavailable")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Service request timeout")


@router.get("/knowledge/list")
async def list_knowledge(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    user: UserContext = Depends(require_admin)
):
    """获取知识列表"""
    import os
    base_url = os.getenv("KNOWLEDGE_SERVICE_URL", "http://localhost:8081")
    params = f"?page={page}&page_size={page_size}"
    if status:
        params += f"&status={status}"
    if category:
        params += f"&category={category}"

    return await proxy_to_service(base_url, f"/api/v1/knowledge{params}")


@router.get("/knowledge/{knowledge_id}")
async def get_knowledge(knowledge_id: int):
    """获取知识详情"""
    import os
    base_url = os.getenv("KNOWLEDGE_SERVICE_URL", "http://localhost:8081")
    return await proxy_to_service(base_url, f"/api/v1/knowledge/{knowledge_id}")


@router.get("/knowledge/stats", response_model=KnowledgeStats)
async def get_knowledge_stats():
    """获取知识统计"""
    import os
    base_url = os.getenv("KNOWLEDGE_SERVICE_URL", "http://localhost:8081")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/api/v1/knowledge/stats")
            if response.status_code == 200:
                return response.json()
    except Exception:
        logger.exception("Failed to fetch knowledge stats from service")

    return KnowledgeStats(total=0, published=0, draft=0, archived=0, categories=0)


@router.get("/archive/list")
async def list_archive(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    court_level: Optional[str] = None,
    case_type: Optional[str] = None,
    cause_of_action: Optional[str] = None,
    user: UserContext = Depends(require_admin)
):
    """获取案例列表"""
    import os
    base_url = os.getenv("ARCHIVE_SERVICE_URL", "http://localhost:8082")
    params = f"?page={page}&page_size={page_size}"
    if status:
        params += f"&status={status}"
    if court_level:
        params += f"&court_level={court_level}"
    if case_type:
        params += f"&case_type={case_type}"
    if cause_of_action:
        params += f"&cause_of_action={cause_of_action}"

    return await proxy_to_service(base_url, f"/api/v1/archive{params}")


@router.get("/archive/{case_id}")
async def get_archive(case_id: int):
    """获取案例详情"""
    import os
    base_url = os.getenv("ARCHIVE_SERVICE_URL", "http://localhost:8082")
    return await proxy_to_service(base_url, f"/api/v1/archive/{case_id}")


@router.get("/archive/stats", response_model=ArchiveStats)
async def get_archive_stats():
    """获取案例统计"""
    import os
    base_url = os.getenv("ARCHIVE_SERVICE_URL", "http://localhost:8082")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/api/v1/archive/stats")
            if response.status_code == 200:
                return response.json()
    except Exception:
        logger.exception("Failed to fetch archive stats from service")

    return ArchiveStats(total=0, published=0, draft=0, archived=0, guiding_cases=0, categories=0)


@router.get("/services/health")
async def get_services_health(user: UserContext = Depends(require_admin)):
    """获取所有服务健康状态"""
    import os
    import time

    knowledge_url = os.getenv("KNOWLEDGE_SERVICE_URL", "http://localhost:8081")
    archive_url = os.getenv("ARCHIVE_SERVICE_URL", "http://localhost:8013")
    ai_url = os.getenv("AI_SERVICE_URL", "http://localhost:8005")

    services = [
        {"name": "knowledge", "url": knowledge_url},
        {"name": "archive", "url": archive_url},
        {"name": "ai", "url": ai_url},
    ]

    results = []
    for svc in services:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{svc['url']}/health/ready")
                latency = (time.time() - start) * 1000
                results.append(ServiceHealth(
                    service=svc["name"],
                    status="healthy" if response.status_code == 200 else "unhealthy",
                    latency_ms=round(latency, 2)
                ))
        except Exception as e:
            latency = (time.time() - start) * 1000
            results.append(ServiceHealth(
                service=svc["name"],
                status="unavailable",
                latency_ms=round(latency, 2)
            ))

    return {"services": results}
