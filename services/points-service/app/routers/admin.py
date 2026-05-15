from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db

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

    async def get_admin_user(request: Request = None):
        if request:
            user_id = int(request.headers.get("X-Admin-User-Id", "0"))
            role = request.headers.get("X-Admin-Role", "admin")
            permissions = request.headers.get("X-Admin-Permissions", "").split(",")
            return AdminUser(user_id=user_id, role=role, permissions=permissions)
        return AdminUser()

    def require_domain_role(domain: str, roles=None):
        async def _checker(admin: AdminUser = Depends(get_admin_user)):
            if admin.is_super_admin:
                return admin
            if roles and admin.role not in roles:
                raise HTTPException(status_code=403, detail=f"需要角色: {', '.join(roles)}")
            return admin
        return _checker

from ..models import PointsUser, PointsHistory, PointsExchangeOrder, PointsAuditLog

admin_router = APIRouter(dependencies=[Depends(require_domain_role("points", roles=["points_admin"]))])


class AdjustPointsRequest(BaseModel):
    amount: int
    comment: Optional[str] = None


class UpdateRuleRequest(BaseModel):
    points: Optional[int] = None
    daily_limit: Optional[int] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


DEFAULT_RULES = [
    {"id": 1, "action": "sign_in", "points": 10, "daily_limit": 1, "description": "每日签到", "enabled": True},
    {"id": 2, "action": "post_create", "points": 5, "daily_limit": 3, "description": "发帖交流", "enabled": True},
    {"id": 3, "action": "comment_create", "points": 2, "daily_limit": 10, "description": "回复评论", "enabled": True},
    {"id": 4, "action": "like", "points": 1, "daily_limit": 20, "description": "点赞互动", "enabled": True},
    {"id": 5, "action": "share", "points": 3, "daily_limit": 5, "description": "分享内容", "enabled": True},
    {"id": 6, "action": "consultation_complete", "points": 50, "daily_limit": 3, "description": "完成法律咨询", "enabled": True},
    {"id": 7, "action": "document_upload", "points": 10, "daily_limit": 5, "description": "上传法律文档", "enabled": True},
    {"id": 8, "action": "profile_complete", "points": 30, "daily_limit": 1, "description": "完善个人资料", "enabled": True},
    {"id": 9, "action": "invite_friend", "points": 100, "daily_limit": 5, "description": "邀请好友注册", "enabled": True},
    {"id": 10, "action": "bonus", "points": 0, "daily_limit": 1, "description": "活动奖励", "enabled": True},
]


@admin_router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users_result = await db.execute(select(func.count(PointsUser.id)))
    total_users = total_users_result.scalar() or 0

    total_points_result = await db.execute(select(func.coalesce(func.sum(PointsUser.balance), 0)))
    total_points = total_points_result.scalar() or 0

    today_earned_result = await db.execute(
        select(func.coalesce(func.sum(PointsHistory.change), 0)).where(
            PointsHistory.change > 0,
            PointsHistory.created_at >= today_start,
        )
    )
    today_earned = today_earned_result.scalar() or 0

    today_spent_result = await db.execute(
        select(func.coalesce(func.sum(PointsHistory.change), 0)).where(
            PointsHistory.change < 0,
            PointsHistory.created_at >= today_start,
        )
    )
    today_spent = abs(today_spent_result.scalar() or 0)

    pending_orders_result = await db.execute(
        select(func.count(PointsExchangeOrder.id)).where(PointsExchangeOrder.status == "pending")
    )
    pending_orders = pending_orders_result.scalar() or 0

    completed_orders_result = await db.execute(
        select(func.count(PointsExchangeOrder.id)).where(PointsExchangeOrder.status == "completed")
    )
    completed_orders = completed_orders_result.scalar() or 0

    return {
        "total_users": total_users,
        "total_points": total_points,
        "today_earned": today_earned,
        "today_spent": today_spent,
        "exchange_stats": {
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
        },
    }


@admin_router.get("/stats")
async def stats(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    query = select(
        func.date_trunc("day", PointsHistory.created_at).label("day"),
        func.sum(func.cast(PointsHistory.change > 0, type_=Integer)).label("earned_count"),
        func.coalesce(func.sum(
            func.case((PointsHistory.change > 0, PointsHistory.change), else_=0)
        ), 0).label("earned_amount"),
        func.sum(func.cast(PointsHistory.change < 0, type_=Integer)).label("spent_count"),
        func.coalesce(func.sum(
            func.case((PointsHistory.change < 0, PointsHistory.change), else_=0)
        ), 0).label("spent_amount"),
    ).group_by("day").order_by("day")

    if start_date:
        query = query.where(PointsHistory.created_at >= datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc))
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
        query = query.where(PointsHistory.created_at < end_dt)

    result = await db.execute(query)
    rows = result.all()

    daily_stats = []
    for row in rows:
        daily_stats.append({
            "date": row.day.strftime("%Y-%m-%d") if row.day else None,
            "earned_count": row.earned_count or 0,
            "earned_amount": row.earned_amount or 0,
            "spent_count": row.spent_count or 0,
            "spent_amount": abs(row.spent_amount or 0),
        })

    return {"daily_stats": daily_stats}


@admin_router.get("/users/{user_id}")
async def user_detail(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PointsUser).where(PointsUser.user_id == user_id))
    points_user = result.scalar_one_or_none()

    if not points_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    recent_history_result = await db.execute(
        select(PointsHistory)
        .where(PointsHistory.user_id == user_id)
        .order_by(PointsHistory.created_at.desc())
        .limit(20)
    )
    recent_history = recent_history_result.scalars().all()

    return {
        "user_id": points_user.user_id,
        "balance": points_user.balance,
        "total_earned": points_user.total_earned,
        "total_spent": points_user.total_spent,
        "created_at": points_user.created_at.isoformat() if points_user.created_at else None,
        "updated_at": points_user.updated_at.isoformat() if points_user.updated_at else None,
        "recent_history": [
            {
                "id": h.id,
                "action": h.source,
                "change": h.change,
                "balance_after": h.balance_after,
                "description": h.description,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in recent_history
        ],
    }


@admin_router.post("/users/{user_id}/adjust")
async def adjust_points(
    user_id: int,
    body: AdjustPointsRequest,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    if body.amount == 0:
        raise HTTPException(status_code=400, detail="调整数量不能为0")

    result = await db.execute(select(PointsUser).where(PointsUser.user_id == user_id))
    points_user = result.scalar_one_or_none()

    if not points_user:
        points_user = PointsUser(user_id=user_id, balance=0, total_earned=0, total_spent=0)
        db.add(points_user)
        await db.flush()

    old_balance = points_user.balance
    new_balance = old_balance + body.amount

    if new_balance < 0:
        raise HTTPException(status_code=400, detail="调整后余额不能为负数")

    points_user.balance = new_balance
    if body.amount > 0:
        points_user.total_earned += body.amount
    else:
        points_user.total_spent += abs(body.amount)

    history = PointsHistory(
        user_id=user_id,
        change=body.amount,
        balance_after=new_balance,
        source="admin_adjust",
        description=body.comment or f"管理员调整积分: {body.amount:+d}",
    )
    db.add(history)

    audit_log = PointsAuditLog(
        target_user_id=user_id,
        operator_id=admin.user_id,
        operator_name=f"admin_{admin.user_id}",
        action="adjust_points",
        change_amount=body.amount,
        balance_after=new_balance,
        comment=body.comment,
        extra_data={"old_balance": old_balance},
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(points_user)

    return {
        "success": True,
        "user_id": user_id,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "change": body.amount,
    }


@admin_router.get("/exchange-orders")
async def list_exchange_orders(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(PointsExchangeOrder).order_by(PointsExchangeOrder.created_at.desc())

    if status:
        query = query.where(PointsExchangeOrder.status == status)

    count_result = await db.execute(select(func.count(PointsExchangeOrder.id)))
    total = count_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()

    return {
        "orders": [
            {
                "id": o.id,
                "user_id": o.user_id,
                "item_id": o.item_id,
                "points_cost": o.points_cost,
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "completed_at": o.completed_at.isoformat() if o.completed_at else None,
            }
            for o in orders
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@admin_router.post("/exchange-orders/{order_id}/approve")
async def approve_exchange_order(
    order_id: int,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PointsExchangeOrder).where(PointsExchangeOrder.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status != "pending":
        raise HTTPException(status_code=400, detail=f"订单状态为 {order.status}，无法审批")

    order.status = "completed"
    order.completed_at = datetime.now(timezone.utc)

    audit_log = PointsAuditLog(
        target_user_id=order.user_id,
        operator_id=admin.user_id,
        operator_name=f"admin_{admin.user_id}",
        action="approve_order",
        change_amount=-order.points_cost,
        balance_after=0,
        comment=f"审批通过订单 #{order_id}",
        extra_data={"order_id": order_id, "item_id": order.item_id},
    )
    db.add(audit_log)

    await db.commit()

    return {"success": True, "order_id": order_id, "status": "completed"}


@admin_router.post("/exchange-orders/{order_id}/reject")
async def reject_exchange_order(
    order_id: int,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PointsExchangeOrder).where(PointsExchangeOrder.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status != "pending":
        raise HTTPException(status_code=400, detail=f"订单状态为 {order.status}，无法拒绝")

    order.status = "rejected"

    user_result = await db.execute(select(PointsUser).where(PointsUser.user_id == order.user_id))
    points_user = user_result.scalar_one_or_none()

    if points_user:
        points_user.balance += order.points_cost
        points_user.total_spent -= order.points_cost

        refund_history = PointsHistory(
            user_id=order.user_id,
            change=order.points_cost,
            balance_after=points_user.balance,
            source="order_reject_refund",
            description=f"订单 #{order_id} 被拒绝，退还积分",
        )
        db.add(refund_history)

    audit_log = PointsAuditLog(
        target_user_id=order.user_id,
        operator_id=admin.user_id,
        operator_name=f"admin_{admin.user_id}",
        action="reject_order",
        change_amount=order.points_cost,
        balance_after=points_user.balance if points_user else 0,
        comment=f"拒绝订单 #{order_id}，退还积分",
        extra_data={"order_id": order_id, "item_id": order.item_id},
    )
    db.add(audit_log)

    await db.commit()

    return {"success": True, "order_id": order_id, "status": "rejected"}


@admin_router.get("/audit-logs")
async def list_audit_logs(
    target_user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(PointsAuditLog).order_by(PointsAuditLog.created_at.desc())

    if target_user_id:
        query = query.where(PointsAuditLog.target_user_id == target_user_id)
    if action:
        query = query.where(PointsAuditLog.action == action)

    count_query = select(func.count(PointsAuditLog.id))
    if target_user_id:
        count_query = count_query.where(PointsAuditLog.target_user_id == target_user_id)
    if action:
        count_query = count_query.where(PointsAuditLog.action == action)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": log.id,
                "target_user_id": log.target_user_id,
                "operator_id": log.operator_id,
                "operator_name": log.operator_name,
                "action": log.action,
                "change_amount": log.change_amount,
                "balance_after": log.balance_after,
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


@admin_router.get("/rules")
async def list_rules():
    return {"rules": DEFAULT_RULES}


@admin_router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    body: UpdateRuleRequest,
    admin: AdminUser = Depends(get_admin_user),
):
    rule = next((r for r in DEFAULT_RULES if r["id"] == rule_id), None)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    if body.points is not None:
        rule["points"] = body.points
    if body.daily_limit is not None:
        rule["daily_limit"] = body.daily_limit
    if body.description is not None:
        rule["description"] = body.description
    if body.enabled is not None:
        rule["enabled"] = body.enabled

    return {"success": True, "rule": rule}
