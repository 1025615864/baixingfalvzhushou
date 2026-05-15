"""审计日志查询路由 (仅超级管理员可访问)"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models.audit_log import AuditLog
from ..utils.deps import get_current_user, require_super_admin
from ..models.user import User

router = APIRouter(prefix="/admin/audit-logs", tags=["审计日志"])


@router.get("")
async def query_audit_logs(
    user_id: Optional[int] = Query(None, description="按用户ID筛选"),
    user_role: Optional[str] = Query(None, description="按角色筛选"),
    action: Optional[str] = Query(None, description="按操作类型筛选 (create/update/delete等)"),
    resource_type: Optional[str] = Query(None, description="按资源类型筛选"),
    path: Optional[str] = Query(None, description="按路径关键词筛选"),
    ip_address: Optional[str] = Query(None, description="按IP筛选"),
    is_sensitive: Optional[bool] = Query(None, description="仅敏感操作"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    """查询审计日志 (仅超级管理员)"""
    query = db.query(AuditLog)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if user_role:
        query = query.filter(AuditLog.user_role == user_role)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if path:
        query = query.filter(AuditLog.path.like(f"%{path}%"))
    if ip_address:
        query = query.filter(AuditLog.ip_address == ip_address)
    if is_sensitive is not None:
        query = query.filter(AuditLog.is_sensitive == is_sensitive)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    total = query.count()
    items = query.order_by(desc(AuditLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/summary")
async def audit_summary(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    """审计日志汇总统计"""
    since = datetime.now() - timedelta(days=days)

    total_logs = db.query(AuditLog).filter(AuditLog.created_at >= since).count()
    sensitive_logs = db.query(AuditLog).filter(
        AuditLog.created_at >= since, AuditLog.is_sensitive == True
    ).count()
    error_logs = db.query(AuditLog).filter(
        AuditLog.created_at >= since, AuditLog.error_message.isnot(None)
    ).count()

    from sqlalchemy import func
    action_counts = db.query(
        AuditLog.action, func.count(AuditLog.id)
    ).filter(AuditLog.created_at >= since).group_by(AuditLog.action).all()

    top_users = db.query(
        AuditLog.user_name, func.count(AuditLog.id)
    ).filter(
        AuditLog.created_at >= since, AuditLog.user_name.isnot(None)
    ).group_by(AuditLog.user_name).order_by(desc(func.count(AuditLog.id))).limit(10).all()

    return {
        "period_days": days,
        "total_logs": total_logs,
        "sensitive_logs": sensitive_logs,
        "error_logs": error_logs,
        "action_distribution": [{"action": a, "count": c} for a, c in action_counts],
        "top_users": [{"username": u, "action_count": c} for u, c in top_users],
    }
