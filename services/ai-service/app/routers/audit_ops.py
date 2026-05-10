"""审计日志运营API"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.dependencies.auth import require_admin, UserContext

router = APIRouter(prefix="/api/v1/ai-ops/audit", tags=["审计日志运营"])


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
