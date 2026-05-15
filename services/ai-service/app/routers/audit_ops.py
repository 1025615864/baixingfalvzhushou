"""审计日志运营API"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse

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
    prefix="/api/v1/ai-ops/audit",
    tags=["审计日志运营"],
    dependencies=[Depends(require_domain_role("ai", roles=["ai_admin"]))],
)


class AuditLogResponse(BaseModel):
    id: int
    service: str
    user_id: Optional[int]
    user_role: Optional[str]
    action: str
    resource_type: str
    resource_id: int
    changes: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


async def _get_async_db():
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/logs")
async def get_audit_logs(
    service: Optional[str] = Query(None, description="服务名称: knowledge/archive"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    action: Optional[str] = Query(None, description="操作类型: create/update/delete/publish/unpublish/submit_review"),
    resource_type: Optional[str] = Query(None, description="资源类型: knowledge/case/category"),
    resource_id: Optional[int] = Query(None, description="资源ID"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    db=Depends(_get_async_db),
    user: UserContext = Depends(require_admin)
):
    try:
        from services.common.services.audit_service import AuditService
        audit_service = AuditService(db)
        result = await audit_service.get_audit_trail(
            service=service,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )
        return result
    except ImportError:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/export")
async def export_audit_logs(
    service: Optional[str] = Query(None, description="服务名称"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    action: Optional[str] = Query(None, description="操作类型"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    resource_id: Optional[int] = Query(None, description="资源ID"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    db=Depends(_get_async_db)
):
    try:
        from services.common.services.audit_service import AuditService
        audit_service = AuditService(db)
        csv_content = await audit_service.export_audit_logs(
            service=service,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
        )
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except ImportError:
        return StreamingResponse(
            iter(["service,action,user_id,resource_type,resource_id,created_at\n"]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_empty_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )


@router.get("/history/{resource_type}/{resource_id}")
async def get_resource_history(
    resource_type: str,
    resource_id: int,
    service: Optional[str] = Query(None, description="服务名称"),
    db=Depends(_get_async_db),
    user: UserContext = Depends(require_admin)
):
    try:
        from services.common.services.audit_service import AuditService
        audit_service = AuditService(db)
        history = await audit_service.get_resource_history(
            resource_type=resource_type,
            resource_id=resource_id,
            service=service,
        )
        return {"items": history, "total": len(history)}
    except ImportError:
        return {"items": [], "total": 0}
