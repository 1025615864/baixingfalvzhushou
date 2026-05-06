"""审计日志路由"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.ops.audit_service import AuditService
from app.middleware.ops_auth import require_ops_role

router = APIRouter(prefix="/api/v1/community/ops/audit", tags=["审计日志"])


@router.get("/logs")
async def query_audit_logs(
    operator_id: Optional[int] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    period: int = Query(7, ge=1, le=90),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("community_director"))
):
    service = AuditService(db)
    logs, total = await service.query_logs(
        operator_id=operator_id,
        action=action,
        target_type=target_type,
        period_days=period,
        page=page,
        page_size=page_size
    )
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": log.id,
                    "operator_id": log.operator_id,
                    "operator_role": log.operator_role,
                    "action": log.action,
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "detail": log.detail,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/logs/summary")
async def get_audit_summary(
    period: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("community_director", "data_analyst"))
):
    service = AuditService(db)
    summary = await service.get_audit_summary(period_days=period)
    return {"success": True, "data": summary}
