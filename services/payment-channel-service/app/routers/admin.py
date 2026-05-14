"""支付通道服务 - 管理员路由"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.payment import PaymentOrder
from ..models.admin import ChannelConfig, PaymentStats, PaymentAuditLog

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser
except ImportError:
    from fastapi import Request

    class AdminUser:
        def __init__(self, user_id: int = 0, role: str = "admin", permissions=None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in {"super_admin", "admin"}

    async def get_admin_user(request: Request = None):
        if request:
            user_id = int(request.headers.get("X-Admin-User-Id", "0"))
            role = request.headers.get("X-Admin-Role", "admin")
            permissions = request.headers.get("X-Admin-Permissions", "").split(",")
            return AdminUser(user_id=user_id, role=role, permissions=permissions)
        return AdminUser()


admin_router = APIRouter()


class ChannelConfigCreate(BaseModel):
    channel_code: str
    channel_name: str
    enabled: bool = True
    config_json: Optional[dict] = None
    fee_rate: float = 0
    daily_limit: Optional[float] = None


class ChannelConfigUpdate(BaseModel):
    channel_name: Optional[str] = None
    enabled: Optional[bool] = None
    config_json: Optional[dict] = None
    fee_rate: Optional[float] = None
    daily_limit: Optional[float] = None


@admin_router.get("/dashboard")
async def dashboard(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    today_count_stmt = select(func.count(PaymentOrder.id)).where(
        PaymentOrder.created_at >= today_start
    )
    today_count_result = await db.execute(today_count_stmt)
    today_transactions = today_count_result.scalar_one()

    today_amount_stmt = select(func.coalesce(func.sum(PaymentOrder.actual_amount), 0)).where(
        and_(
            PaymentOrder.created_at >= today_start,
            PaymentOrder.status.in_(["paid", "completed"]),
        )
    )
    today_amount_result = await db.execute(today_amount_stmt)
    today_amount = float(today_amount_result.scalar_one())

    today_success_stmt = select(func.count(PaymentOrder.id)).where(
        and_(
            PaymentOrder.created_at >= today_start,
            PaymentOrder.status.in_(["paid", "completed"]),
        )
    )
    today_success_result = await db.execute(today_success_stmt)
    today_success = today_success_result.scalar_one()

    today_total_stmt = select(func.count(PaymentOrder.id)).where(
        PaymentOrder.created_at >= today_start,
    )
    today_total_result = await db.execute(today_total_stmt)
    today_total = today_total_result.scalar_one()

    success_rate = round((today_success / today_total * 100) if today_total > 0 else 0, 2)

    channel_stmt = (
        select(
            PaymentOrder.payment_method,
            func.count(PaymentOrder.id).label("count"),
            func.coalesce(func.sum(PaymentOrder.actual_amount), 0).label("amount"),
        )
        .where(PaymentOrder.created_at >= today_start)
        .group_by(PaymentOrder.payment_method)
    )
    channel_result = await db.execute(channel_stmt)
    channel_stats = [
        {
            "channel_code": row.payment_method or "unknown",
            "transaction_count": row.count,
            "total_amount": float(row.amount),
        }
        for row in channel_result.all()
    ]

    trend = []
    for i in range(6, -1, -1):
        day = today_start - timedelta(days=i)
        day_end = day + timedelta(days=1)

        day_count_stmt = select(func.count(PaymentOrder.id)).where(
            and_(PaymentOrder.created_at >= day, PaymentOrder.created_at < day_end)
        )
        day_count_result = await db.execute(day_count_stmt)
        day_count = day_count_result.scalar_one()

        day_amount_stmt = select(func.coalesce(func.sum(PaymentOrder.actual_amount), 0)).where(
            and_(
                PaymentOrder.created_at >= day,
                PaymentOrder.created_at < day_end,
                PaymentOrder.status.in_(["paid", "completed"]),
            )
        )
        day_amount_result = await db.execute(day_amount_stmt)
        day_amount = float(day_amount_result.scalar_one())

        trend.append({
            "date": day.strftime("%Y-%m-%d"),
            "transaction_count": day_count,
            "total_amount": day_amount,
        })

    return {
        "today_transactions": today_transactions,
        "today_amount": today_amount,
        "today_success_rate": success_rate,
        "channel_stats": channel_stats,
        "trend": trend,
    }


@admin_router.get("/channels")
async def list_channels(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    stmt = select(ChannelConfig).order_by(ChannelConfig.id)
    result = await db.execute(stmt)
    channels = result.scalars().all()

    return {
        "items": [
            {
                "id": ch.id,
                "channel_code": ch.channel_code,
                "channel_name": ch.channel_name,
                "enabled": ch.enabled,
                "config_json": ch.config_json,
                "fee_rate": float(ch.fee_rate) if ch.fee_rate is not None else 0,
                "daily_limit": float(ch.daily_limit) if ch.daily_limit is not None else None,
                "created_at": ch.created_at.isoformat() if ch.created_at else None,
                "updated_at": ch.updated_at.isoformat() if ch.updated_at else None,
            }
            for ch in channels
        ]
    }


@admin_router.post("/channels")
async def create_channel(
    body: ChannelConfigCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    existing = await db.execute(
        select(ChannelConfig).where(ChannelConfig.channel_code == body.channel_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"渠道编码 {body.channel_code} 已存在")

    channel = ChannelConfig(
        channel_code=body.channel_code,
        channel_name=body.channel_name,
        enabled=body.enabled,
        config_json=body.config_json,
        fee_rate=body.fee_rate,
        daily_limit=body.daily_limit,
    )
    db.add(channel)

    audit = PaymentAuditLog(
        operator_id=admin.user_id,
        operator_name=getattr(admin, "username", str(admin.user_id)),
        action="create_channel",
        comment=f"创建渠道: {body.channel_code}",
        extra_data={"channel_code": body.channel_code, "channel_name": body.channel_name},
    )
    db.add(audit)

    await db.flush()

    return {
        "id": channel.id,
        "channel_code": channel.channel_code,
        "channel_name": channel.channel_name,
        "enabled": channel.enabled,
        "fee_rate": float(channel.fee_rate) if channel.fee_rate is not None else 0,
        "daily_limit": float(channel.daily_limit) if channel.daily_limit is not None else None,
    }


@admin_router.put("/channels/{channel_id}")
async def update_channel(
    channel_id: int,
    body: ChannelConfigUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    result = await db.execute(
        select(ChannelConfig).where(ChannelConfig.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="渠道配置不存在")

    changes = {}
    if body.channel_name is not None:
        channel.channel_name = body.channel_name
        changes["channel_name"] = body.channel_name
    if body.enabled is not None:
        channel.enabled = body.enabled
        changes["enabled"] = body.enabled
    if body.config_json is not None:
        channel.config_json = body.config_json
        changes["config_json"] = body.config_json
    if body.fee_rate is not None:
        channel.fee_rate = body.fee_rate
        changes["fee_rate"] = body.fee_rate
    if body.daily_limit is not None:
        channel.daily_limit = body.daily_limit
        changes["daily_limit"] = body.daily_limit

    channel.updated_at = datetime.now(timezone.utc)

    audit = PaymentAuditLog(
        target_id=channel_id,
        operator_id=admin.user_id,
        operator_name=getattr(admin, "username", str(admin.user_id)),
        action="update_channel",
        comment=f"更新渠道: {channel.channel_code}",
        extra_data=changes,
    )
    db.add(audit)

    await db.flush()

    return {
        "id": channel.id,
        "channel_code": channel.channel_code,
        "channel_name": channel.channel_name,
        "enabled": channel.enabled,
        "fee_rate": float(channel.fee_rate) if channel.fee_rate is not None else 0,
        "daily_limit": float(channel.daily_limit) if channel.daily_limit is not None else None,
    }


@admin_router.patch("/channels/{channel_id}/toggle")
async def toggle_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    result = await db.execute(
        select(ChannelConfig).where(ChannelConfig.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="渠道配置不存在")

    channel.enabled = not channel.enabled
    channel.updated_at = datetime.now(timezone.utc)

    action_text = "启用" if channel.enabled else "禁用"

    audit = PaymentAuditLog(
        target_id=channel_id,
        operator_id=admin.user_id,
        operator_name=getattr(admin, "username", str(admin.user_id)),
        action="toggle_channel",
        comment=f"{action_text}渠道: {channel.channel_code}",
        extra_data={"channel_code": channel.channel_code, "enabled": channel.enabled},
    )
    db.add(audit)

    await db.flush()

    return {
        "id": channel.id,
        "channel_code": channel.channel_code,
        "enabled": channel.enabled,
    }


@admin_router.get("/stats")
async def payment_stats(
    channel_code: Optional[str] = Query(None, description="渠道编码筛选"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    filters = []

    if channel_code:
        filters.append(PaymentStats.channel_code == channel_code)

    if start_date:
        filters.append(PaymentStats.stat_date >= start_date)

    if end_date:
        filters.append(PaymentStats.stat_date <= end_date)

    count_stmt = select(func.count(PaymentStats.id)).where(*filters)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = (
        select(PaymentStats)
        .where(*filters)
        .order_by(PaymentStats.stat_date.desc(), PaymentStats.channel_code)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    stats = result.scalars().all()

    return {
        "items": [
            {
                "id": s.id,
                "stat_date": s.stat_date,
                "channel_code": s.channel_code,
                "transaction_count": s.transaction_count,
                "total_amount": float(s.total_amount) if s.total_amount is not None else 0,
                "success_count": s.success_count,
                "success_rate": float(s.success_rate) if s.success_rate is not None else 0,
                "fee_amount": float(s.fee_amount) if s.fee_amount is not None else 0,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in stats
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@admin_router.get("/audit-logs")
async def audit_logs(
    target_id: Optional[int] = Query(None, description="操作目标ID"),
    action: Optional[str] = Query(None, description="操作动作"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    filters = []

    if target_id is not None:
        filters.append(PaymentAuditLog.target_id == target_id)

    if action:
        filters.append(PaymentAuditLog.action == action)

    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            filters.append(PaymentAuditLog.created_at >= sd)
        except ValueError:
            raise HTTPException(status_code=400, detail="start_date 格式错误，需 YYYY-MM-DD")

    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
            filters.append(PaymentAuditLog.created_at < ed)
        except ValueError:
            raise HTTPException(status_code=400, detail="end_date 格式错误，需 YYYY-MM-DD")

    count_stmt = select(func.count(PaymentAuditLog.id)).where(*filters)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = (
        select(PaymentAuditLog)
        .where(*filters)
        .order_by(PaymentAuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": log.id,
                "target_id": log.target_id,
                "operator_id": log.operator_id,
                "operator_name": log.operator_name,
                "action": log.action,
                "comment": log.comment,
                "extra_data": log.extra_data,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
