"""审计日志运营API"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin, UserContext
from services.common.services.audit_service import AuditService

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
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_admin)
):
    """查询审计日志，支持分页和筛选"""
    audit_service = AuditService(db)

    result = audit_service.get_audit_trail(
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


@router.get("/export")
async def export_audit_logs(
    service: Optional[str] = Query(None, description="服务名称"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    action: Optional[str] = Query(None, description="操作类型"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    resource_id: Optional[int] = Query(None, description="资源ID"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(get_db)
):
    """导出审计日志为CSV格式"""
    audit_service = AuditService(db)

    csv_content = audit_service.export_audit_logs(
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


@router.get("/history/{resource_type}/{resource_id}")
async def get_resource_history(
    resource_type: str,
    resource_id: int,
    service: Optional[str] = Query(None, description="服务名称"),
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_admin)
):
    """获取特定资源的操作历史"""
    audit_service = AuditService(db)

    history = audit_service.get_resource_history(
        resource_type=resource_type,
        resource_id=resource_id,
        service=service,
    )

    return {"items": history, "total": len(history)}