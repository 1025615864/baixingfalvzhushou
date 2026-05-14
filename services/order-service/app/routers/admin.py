"""订单服务 - 管理员路由"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import select, func, cast, Date, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.admin import RefundAudit, OrderStats
from app.services.order_service import order_service

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    from fastapi import Request

    class AdminUser:
        def __init__(self, user_id: int = 0, role: str = "admin", permissions=None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in {"super_admin", "admin"}

    async def get_admin_user():
        return AdminUser()

    def require_domain_role(domain: str, roles=None):
        async def domain_checker(admin: AdminUser = Depends(get_admin_user)):
            if not admin.is_super_admin and roles and admin.role not in roles:
                raise HTTPException(status_code=403, detail=f"需要角色: {', '.join(roles)}")
            return admin
        return domain_checker


admin_router = APIRouter()


@admin_router.get("/dashboard", dependencies=[Depends(require_domain_role("order", roles=["order_admin"]))])
async def dashboard(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    total_stmt = select(func.count(Order.id))
    total_result = await db.execute(total_stmt)
    total_orders = total_result.scalar_one()

    today_stmt = select(func.count(Order.id)).where(Order.created_at >= today_start)
    today_result = await db.execute(today_stmt)
    today_orders = today_result.scalar_one()

    week_stmt = select(func.count(Order.id)).where(Order.created_at >= week_start)
    week_result = await db.execute(week_stmt)
    week_orders = week_result.scalar_one()

    pending_refund_stmt = select(func.count(Order.id)).where(
        Order.status == OrderStatus.REFUNDED
    )
    pending_refund_result = await db.execute(pending_refund_stmt)
    pending_refunds = pending_refund_result.scalar_one()

    anomaly_stmt = select(func.count(Order.id)).where(
        Order.status.in_([OrderStatus.FAILED, OrderStatus.CANCELLED])
    )
    anomaly_result = await db.execute(anomaly_stmt)
    anomaly_orders = anomaly_result.scalar_one()

    trend = []
    for i in range(6, -1, -1):
        day = today_start - timedelta(days=i)
        day_end = day + timedelta(days=1)
        day_stmt = select(func.count(Order.id)).where(
            and_(Order.created_at >= day, Order.created_at < day_end)
        )
        day_result = await db.execute(day_stmt)
        day_count = day_result.scalar_one()

        revenue_stmt = select(func.coalesce(func.sum(Order.actual_amount), 0)).where(
            and_(
                Order.created_at >= day,
                Order.created_at < day_end,
                Order.status.in_([OrderStatus.PAID, OrderStatus.COMPLETED]),
            )
        )
        revenue_result = await db.execute(revenue_stmt)
        day_revenue = float(revenue_result.scalar_one())

        trend.append({
            "date": day.strftime("%Y-%m-%d"),
            "order_count": day_count,
            "revenue": day_revenue,
        })

    return {
        "total_orders": total_orders,
        "today_orders": today_orders,
        "week_orders": week_orders,
        "pending_refunds": pending_refunds,
        "anomaly_orders": anomaly_orders,
        "trend": trend,
    }


@admin_router.get("/orders", dependencies=[Depends(require_domain_role("order", roles=["order_ops"]))])
async def list_orders(
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    filters = []

    if status:
        try:
            order_status = OrderStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的订单状态: {status}")
        filters.append(Order.status == order_status)

    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            filters.append(Order.created_at >= sd)
        except ValueError:
            raise HTTPException(status_code=400, detail="start_date 格式错误，需 YYYY-MM-DD")

    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            ) + timedelta(days=1)
            filters.append(Order.created_at < ed)
        except ValueError:
            raise HTTPException(status_code=400, detail="end_date 格式错误，需 YYYY-MM-DD")

    if min_amount is not None:
        filters.append(Order.actual_amount >= min_amount)

    if max_amount is not None:
        filters.append(Order.actual_amount <= max_amount)

    count_stmt = select(func.count(Order.id)).where(*filters)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = (
        select(Order)
        .where(*filters)
        .order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    orders = result.scalars().all()

    return {
        "items": [_order_to_dict(o) for o in orders],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@admin_router.get("/orders/{order_id}", dependencies=[Depends(require_domain_role("order", roles=["order_ops"]))])
async def get_order_detail(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    order = await order_service.get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    audit_stmt = (
        select(RefundAudit)
        .where(RefundAudit.order_id == order_id)
        .order_by(RefundAudit.created_at.desc())
    )
    audit_result = await db.execute(audit_stmt)
    audits = audit_result.scalars().all()

    order_dict = _order_to_dict(order)
    order_dict["refund_audits"] = [
        {
            "id": a.id,
            "auditor_id": a.auditor_id,
            "auditor_name": a.auditor_name,
            "action": a.action,
            "comment": a.comment,
            "extra_data": a.extra_data,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in audits
    ]

    return order_dict


@admin_router.get("/refunds/pending")
async def pending_refunds(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    filters = [Order.status == OrderStatus.REFUNDED]

    count_stmt = select(func.count(Order.id)).where(*filters)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = (
        select(Order)
        .where(*filters)
        .order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    orders = result.scalars().all()

    return {
        "items": [_order_to_dict(o) for o in orders],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@admin_router.post("/refunds/{order_id}/audit")
async def audit_refund(
    order_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    action = body.get("action")
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action 必须为 approve 或 reject")

    comment = body.get("comment")
    extra_data = body.get("extra_data")

    order = await order_service.get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status != OrderStatus.REFUNDED:
        raise HTTPException(status_code=400, detail="订单状态不是退款状态，无法审核")

    audit = RefundAudit(
        order_id=order_id,
        auditor_id=admin.user_id,
        auditor_name=getattr(admin, "username", str(admin.user_id)),
        action=action,
        comment=comment,
        extra_data=extra_data,
    )
    db.add(audit)

    if action == "approve":
        order.status = OrderStatus.REFUNDED
        order.refund_reason = order.refund_reason or "管理员审核通过退款"
        order.updated_at = datetime.now(timezone.utc)
    elif action == "reject":
        order.status = OrderStatus.PAID
        order.refund_reason = f"退款被拒绝: {comment or '无备注'}"
        order.updated_at = datetime.now(timezone.utc)

    await db.flush()

    return {
        "success": True,
        "order_id": order_id,
        "action": action,
        "auditor_id": admin.user_id,
    }


@admin_router.get("/stats")
async def order_stats(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    group_by: Optional[str] = Query("date", description="date 或 status"),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    now = datetime.now(timezone.utc)
    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="start_date 格式错误")
    else:
        sd = now - timedelta(days=30)

    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            ) + timedelta(days=1)
        except ValueError:
            raise HTTPException(status_code=400, detail="end_date 格式错误")
    else:
        ed = now + timedelta(days=1)

    base_filter = [Order.created_at >= sd, Order.created_at < ed]

    total_stmt = select(func.count(Order.id)).where(*base_filter)
    total_result = await db.execute(total_stmt)
    total_orders = total_result.scalar_one()

    revenue_stmt = select(func.coalesce(func.sum(Order.actual_amount), 0)).where(
        *base_filter,
        Order.status.in_([OrderStatus.PAID, OrderStatus.COMPLETED]),
    )
    revenue_result = await db.execute(revenue_stmt)
    total_revenue = float(revenue_result.scalar_one())

    refund_stmt = select(func.count(Order.id)).where(
        *base_filter,
        Order.status == OrderStatus.REFUNDED,
    )
    refund_result = await db.execute(refund_stmt)
    refund_count = refund_result.scalar_one()

    groups = []
    if group_by == "status":
        status_stmt = (
            select(Order.status, func.count(Order.id), func.coalesce(func.sum(Order.actual_amount), 0))
            .where(*base_filter)
            .group_by(Order.status)
        )
        status_result = await db.execute(status_stmt)
        for status_val, count, amount in status_result.all():
            groups.append({
                "status": status_val.value if hasattr(status_val, "value") else str(status_val),
                "count": count,
                "amount": float(amount),
            })
    else:
        daily_stmt = (
            select(
                cast(Order.created_at, Date).label("date"),
                func.count(Order.id),
                func.coalesce(func.sum(Order.actual_amount), 0),
            )
            .where(*base_filter)
            .group_by(cast(Order.created_at, Date))
            .order_by(cast(Order.created_at, Date))
        )
        daily_result = await db.execute(daily_stmt)
        for date_val, count, amount in daily_result.all():
            groups.append({
                "date": date_val.isoformat(),
                "count": count,
                "amount": float(amount),
            })

    return {
        "start_date": sd.strftime("%Y-%m-%d"),
        "end_date": (ed - timedelta(days=1)).strftime("%Y-%m-%d"),
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "refund_count": refund_count,
        "groups": groups,
    }


@admin_router.get("/audit-logs")
async def audit_logs(
    order_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    filters = []

    if order_id is not None:
        filters.append(RefundAudit.order_id == order_id)

    if action:
        if action not in ("approve", "reject"):
            raise HTTPException(status_code=400, detail="action 必须为 approve 或 reject")
        filters.append(RefundAudit.action == action)

    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            filters.append(RefundAudit.created_at >= sd)
        except ValueError:
            raise HTTPException(status_code=400, detail="start_date 格式错误")

    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            ) + timedelta(days=1)
            filters.append(RefundAudit.created_at < ed)
        except ValueError:
            raise HTTPException(status_code=400, detail="end_date 格式错误")

    count_stmt = select(func.count(RefundAudit.id)).where(*filters)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = (
        select(RefundAudit)
        .where(*filters)
        .order_by(RefundAudit.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": log.id,
                "order_id": log.order_id,
                "auditor_id": log.auditor_id,
                "auditor_name": log.auditor_name,
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


def _order_to_dict(order) -> dict:
    return {
        "id": order.id,
        "order_no": order.order_no,
        "user_id": order.user_id,
        "order_type": order.order_type.value if hasattr(order.order_type, "value") else str(order.order_type),
        "title": order.title,
        "description": order.description,
        "amount": float(order.amount) if order.amount else 0,
        "discount_amount": float(order.discount_amount) if order.discount_amount else 0,
        "actual_amount": float(order.actual_amount) if order.actual_amount else 0,
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "payment_method": order.payment_method.value if order.payment_method and hasattr(order.payment_method, "value") else order.payment_method,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None,
        "completed_at": order.completed_at.isoformat() if order.completed_at else None,
        "refund_reason": order.refund_reason,
    }
