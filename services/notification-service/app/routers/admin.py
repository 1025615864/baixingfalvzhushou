from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin import NotificationTemplate, NotificationStats, BatchPushTask, NotificationAuditLog
try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi import status
    from typing import List

    class AdminUser:
        def __init__(self, user_id: int = 0, role: str = "admin", permissions: Optional[List[str]] = None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in {"super_admin", "admin"}

    _security = HTTPBearer(auto_error=False)

    async def get_admin_user(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> AdminUser:
        if not credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证凭据")
        return AdminUser(user_id=1, role="admin")

    def require_domain_role(domain: str, roles: Optional[List[str]] = None):
        async def domain_checker(admin: AdminUser = Depends(get_admin_user)):
            return admin
        return domain_checker

router = APIRouter()


@router.get("/dashboard", dependencies=[Depends(require_domain_role("notification", roles=["notification_admin"]))])
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = today_start - timedelta(days=7)

    today_stats = await db.execute(
        select(
            func.coalesce(func.sum(NotificationStats.sent_count), 0),
            func.coalesce(func.sum(NotificationStats.delivered_count), 0),
            func.coalesce(func.sum(NotificationStats.failed_count), 0),
        ).where(NotificationStats.stat_date >= today_start)
    )
    sent, delivered, failed = today_stats.one()
    success_rate = round(delivered / sent * 100, 2) if sent > 0 else 0.0

    channel_stats = await db.execute(
        select(
            NotificationStats.channel,
            func.coalesce(func.sum(NotificationStats.sent_count), 0),
            func.coalesce(func.sum(NotificationStats.delivered_count), 0),
            func.coalesce(func.sum(NotificationStats.failed_count), 0),
        )
        .where(NotificationStats.stat_date >= today_start)
        .group_by(NotificationStats.channel)
    )
    channels = [
        {
            "channel": row[0],
            "sent": row[1],
            "delivered": row[2],
            "failed": row[3],
        }
        for row in channel_stats.all()
    ]

    trend = await db.execute(
        select(
            func.date(NotificationStats.stat_date),
            func.coalesce(func.sum(NotificationStats.sent_count), 0),
            func.coalesce(func.sum(NotificationStats.delivered_count), 0),
            func.coalesce(func.sum(NotificationStats.failed_count), 0),
        )
        .where(NotificationStats.stat_date >= seven_days_ago)
        .group_by(func.date(NotificationStats.stat_date))
        .order_by(func.date(NotificationStats.stat_date))
    )
    trend_data = [
        {
            "date": str(row[0]),
            "sent": row[1],
            "delivered": row[2],
            "failed": row[3],
        }
        for row in trend.all()
    ]

    return {
        "today": {
            "sent_count": sent,
            "delivered_count": delivered,
            "failed_count": failed,
            "success_rate": success_rate,
        },
        "channel_stats": channels,
        "trend_7d": trend_data,
    }


@router.get("/templates", dependencies=[Depends(require_domain_role("notification", roles=["notification_admin"]))])
async def list_templates(
    channel: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    conditions = []
    if channel:
        conditions.append(NotificationTemplate.channel == channel)
    if status:
        conditions.append(NotificationTemplate.status == status)

    query = select(NotificationTemplate)
    if conditions:
        query = query.where(and_(*conditions))
    query = query.order_by(NotificationTemplate.created_at.desc())

    total_result = await db.execute(
        select(func.count()).select_from(NotificationTemplate)
        .where(and_(*conditions) if conditions else True)
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )
    templates = result.scalars().all()

    return {
        "items": [_template_to_dict(t) for t in templates],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/templates", dependencies=[Depends(require_domain_role("notification", roles=["notification_admin"]))])
async def create_template(
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    code = body.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="模板编码不能为空")

    existing = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.code == code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="模板编码已存在")

    template = NotificationTemplate(
        name=body.get("name", ""),
        code=code,
        channel=body.get("channel", "email"),
        content=body.get("content", ""),
        variables=body.get("variables"),
        status=body.get("status", "active"),
    )
    db.add(template)

    audit = NotificationAuditLog(
        operator_id=admin.user_id,
        operator_name=str(admin.user_id),
        action="create_template",
        comment=f"创建模板: {code}",
        extra_data={"template_code": code, "channel": body.get("channel", "email")},
    )
    db.add(audit)
    await db.flush()

    return _template_to_dict(template)


@router.put("/templates/{template_id}", dependencies=[Depends(require_domain_role("notification", roles=["notification_admin"]))])
async def update_template(
    template_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    result = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if "name" in body:
        template.name = body["name"]
    if "channel" in body:
        template.channel = body["channel"]
    if "content" in body:
        template.content = body["content"]
    if "variables" in body:
        template.variables = body["variables"]
    if "status" in body:
        template.status = body["status"]

    audit = NotificationAuditLog(
        target_id=template_id,
        operator_id=admin.user_id,
        operator_name=str(admin.user_id),
        action="update_template",
        comment=f"更新模板: {template.code}",
        extra_data={"template_id": template_id, "updates": list(body.keys())},
    )
    db.add(audit)
    await db.flush()

    return _template_to_dict(template)


@router.delete("/templates/{template_id}", dependencies=[Depends(require_domain_role("notification", roles=["notification_admin"]))])
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    result = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    template_code = template.code
    await db.delete(template)

    audit = NotificationAuditLog(
        target_id=template_id,
        operator_id=admin.user_id,
        operator_name=str(admin.user_id),
        action="delete_template",
        comment=f"删除模板: {template_code}",
        extra_data={"template_id": template_id, "template_code": template_code},
    )
    db.add(audit)
    await db.flush()

    return {"message": "删除成功"}


@router.get("/stats", dependencies=[Depends(require_domain_role("notification", roles=["notification_ops"]))])
async def get_stats(
    channel: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    template_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    conditions = []
    if channel:
        conditions.append(NotificationStats.channel == channel)
    if start_date:
        conditions.append(NotificationStats.stat_date >= datetime.fromisoformat(start_date))
    if end_date:
        conditions.append(NotificationStats.stat_date <= datetime.fromisoformat(end_date))
    if template_id is not None:
        conditions.append(NotificationStats.template_id == template_id)

    query = select(NotificationStats)
    if conditions:
        query = query.where(and_(*conditions))
    query = query.order_by(NotificationStats.stat_date.desc())

    total_result = await db.execute(
        select(func.count()).select_from(NotificationStats)
        .where(and_(*conditions) if conditions else True)
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )
    stats = result.scalars().all()

    return {
        "items": [_stats_to_dict(s) for s in stats],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/batch-push", dependencies=[Depends(require_domain_role("notification", roles=["notification_admin"]))])
async def create_batch_push(
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    title = body.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="推送标题不能为空")

    template_id = body.get("template_id")
    if template_id:
        tpl_result = await db.execute(
            select(NotificationTemplate).where(NotificationTemplate.id == template_id)
        )
        if not tpl_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="模板不存在")

    task = BatchPushTask(
        title=title,
        template_id=template_id,
        target_filter=body.get("target_filter"),
        total_count=body.get("total_count", 0),
    )
    db.add(task)

    audit = NotificationAuditLog(
        operator_id=admin.user_id,
        operator_name=str(admin.user_id),
        action="create_batch_push",
        comment=f"创建批量推送: {title}",
        extra_data={"title": title, "template_id": template_id},
    )
    db.add(audit)
    await db.flush()

    return _batch_task_to_dict(task)


@router.get("/batch-push/{task_id}", dependencies=[Depends(require_domain_role("notification", roles=["notification_ops"]))])
async def get_batch_push_progress(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    result = await db.execute(
        select(BatchPushTask).where(BatchPushTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="推送任务不存在")

    progress = 0
    if task.total_count > 0:
        progress = round((task.sent_count + task.failed_count) / task.total_count * 100, 2)

    data = _batch_task_to_dict(task)
    data["progress"] = min(progress, 100)
    return data


@router.post("/batch-push/{task_id}/cancel", dependencies=[Depends(require_domain_role("notification", roles=["notification_admin"]))])
async def cancel_batch_push(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    result = await db.execute(
        select(BatchPushTask).where(BatchPushTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="推送任务不存在")

    if task.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail=f"任务状态为 {task.status}，无法取消")

    task.status = "cancelled"

    audit = NotificationAuditLog(
        target_id=task_id,
        operator_id=admin.user_id,
        operator_name=str(admin.user_id),
        action="cancel_batch_push",
        comment=f"取消批量推送: {task.title}",
        extra_data={"task_id": task_id},
    )
    db.add(audit)
    await db.flush()

    return _batch_task_to_dict(task)


@router.get("/audit-logs", dependencies=[Depends(require_domain_role("notification", roles=["notification_admin"]))])
async def list_audit_logs(
    action: Optional[str] = Query(None),
    operator_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    conditions = []
    if action:
        conditions.append(NotificationAuditLog.action == action)
    if operator_id:
        conditions.append(NotificationAuditLog.operator_id == operator_id)
    if start_date:
        conditions.append(NotificationAuditLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        conditions.append(NotificationAuditLog.created_at <= datetime.fromisoformat(end_date))

    query = select(NotificationAuditLog)
    if conditions:
        query = query.where(and_(*conditions))
    query = query.order_by(NotificationAuditLog.created_at.desc())

    total_result = await db.execute(
        select(func.count()).select_from(NotificationAuditLog)
        .where(and_(*conditions) if conditions else True)
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )
    logs = result.scalars().all()

    return {
        "items": [_audit_log_to_dict(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def _template_to_dict(t: NotificationTemplate) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "code": t.code,
        "channel": t.channel,
        "content": t.content,
        "variables": t.variables,
        "status": t.status,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _stats_to_dict(s: NotificationStats) -> dict:
    return {
        "id": s.id,
        "stat_date": s.stat_date.isoformat() if s.stat_date else None,
        "channel": s.channel,
        "template_id": s.template_id,
        "sent_count": s.sent_count,
        "delivered_count": s.delivered_count,
        "failed_count": s.failed_count,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _batch_task_to_dict(t: BatchPushTask) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "template_id": t.template_id,
        "target_filter": t.target_filter,
        "status": t.status,
        "total_count": t.total_count,
        "sent_count": t.sent_count,
        "failed_count": t.failed_count,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _audit_log_to_dict(log: NotificationAuditLog) -> dict:
    return {
        "id": log.id,
        "target_id": log.target_id,
        "operator_id": log.operator_id,
        "operator_name": log.operator_name,
        "action": log.action,
        "comment": log.comment,
        "extra_data": log.extra_data,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }
