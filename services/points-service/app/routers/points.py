from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.points_service import PointsService

router = APIRouter()


@router.get("/balance")
async def get_balance(
    user_id: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
):
    from app.models import PointsUser
    from sqlalchemy import select
    result = await db.execute(select(PointsUser).where(PointsUser.user_id == user_id))
    points_user = result.scalar_one_or_none()
    if not points_user:
        return {"balance": 0, "continuous_days": 0, "total_earned": 0, "total_spent": 0}
    return {
        "balance": points_user.balance,
        "continuous_days": 0,
        "total_earned": points_user.total_earned,
        "total_spent": points_user.total_spent,
    }


@router.get("/history")
async def get_history(
    user_id: int = Query(default=1),
    action_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    svc = PointsService(db)
    source = action_type
    page = (offset // limit) + 1
    result = await svc.get_points_history(
        user_id=user_id, source=source, page=page, page_size=limit,
    )
    items = [_history_to_dict(h) for h in result["items"]]
    return {
        "history": items,
        "total": result["total"],
        "limit": limit,
        "offset": offset,
    }


@router.get("/products")
async def get_products(
    product_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = PointsService(db)
    result = await svc.list_mall_items(page=page, page_size=page_size)
    items = [_mall_item_to_dict(i) for i in result["items"]]
    if product_type:
        items = [i for i in items if i.get("product_type") == product_type]
    return {"products": items, "total": result["total"]}


@router.post("/redeem")
async def redeem_product(
    body: dict,
    user_id: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
):
    item_id = body.get("item_id") or body.get("product_id")
    if not item_id:
        raise HTTPException(status_code=400, detail="缺少 item_id 或 product_id")
    try:
        item_id = int(item_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="无效的 item_id")

    svc = PointsService(db)
    try:
        order = await svc.exchange_item(user_id=user_id, item_id=item_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return {
        "success": True,
        "order": {
            "id": order.id,
            "item_id": order.item_id,
            "points_cost": order.points_cost,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        },
    }


@router.get("/orders")
async def get_exchange_orders(
    user_id: int = Query(default=1),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = PointsService(db)
    result = await svc.get_exchange_orders(user_id=user_id, page_size=limit)
    items = [_exchange_order_to_dict(o) for o in result["items"]]
    if status:
        items = [i for i in items if i.get("status") == status]
    return {"orders": items, "total": result["total"]}


@router.post("/check-in")
async def check_in(
    user_id: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
):
    svc = PointsService(db)
    try:
        result = await svc.daily_check_in(user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return {
        "message": "签到成功",
        "points_earned": result["points_awarded"],
        "continuous_days": result["current_streak"],
        "total_points": 0,
    }


@router.get("/check-in/status")
async def get_check_in_status(
    user_id: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
):
    svc = PointsService(db)
    result = await svc.get_check_in_status(user_id=user_id)
    return result


@router.get("/daily-stats")
async def get_daily_stats(
    user_id: int = Query(default=1),
    db: AsyncSession = Depends(get_db),
):
    svc = PointsService(db)
    result = await svc.get_points_history(user_id=user_id, page=1, page_size=100)
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    today_items = [h for h in result["items"] if h.created_at and h.created_at.isoformat().startswith(today)]
    action_counts: dict[str, int] = {}
    for item in today_items:
        action = item.source
        action_counts[action] = action_counts.get(action, 0) + 1
    stats = [{"action": k, "count": v} for k, v in action_counts.items()]
    return {"stats": stats}


@router.get("/rules")
async def get_rules():
    return {"rules": [
        {"action": "sign_in", "points": 10, "daily_limit": 1, "description": "每日签到"},
        {"action": "post_create", "points": 5, "daily_limit": 3, "description": "发帖交流"},
        {"action": "comment_create", "points": 2, "daily_limit": 10, "description": "回复评论"},
        {"action": "like", "points": 1, "daily_limit": 20, "description": "点赞互动"},
        {"action": "share", "points": 3, "daily_limit": 5, "description": "分享内容"},
        {"action": "consultation_complete", "points": 50, "daily_limit": 3, "description": "完成法律咨询"},
        {"action": "document_upload", "points": 10, "daily_limit": 5, "description": "上传法律文档"},
        {"action": "profile_complete", "points": 30, "daily_limit": 1, "description": "完善个人资料"},
        {"action": "invite_friend", "points": 100, "daily_limit": 5, "description": "邀请好友注册"},
        {"action": "bonus", "points": 0, "daily_limit": 1, "description": "活动奖励"},
    ]}


@router.get("/leaderboard")
async def get_leaderboard(
    top_k: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    from app.models import PointsUser
    from sqlalchemy import select, desc
    result = await db.execute(
        select(PointsUser).order_by(desc(PointsUser.total_earned)).limit(top_k)
    )
    users = result.scalars().all()
    leaderboard = [
        {"user_id": str(u.user_id), "username": f"用户{u.user_id}", "total_points": u.total_earned, "rank": idx + 1}
        for idx, u in enumerate(users)
    ]
    return {"leaderboard": leaderboard}


def _history_to_dict(h) -> dict:
    return {
        "id": h.id,
        "user_id": h.user_id,
        "action": h.source,
        "points": h.change,
        "balance_after": h.balance_after,
        "description": h.description,
        "created_at": h.created_at.isoformat() if h.created_at else None,
    }


def _mall_item_to_dict(i) -> dict:
    return {
        "id": str(i.id),
        "name": i.name,
        "description": getattr(i, "description", ""),
        "points_required": i.points_cost,
        "product_type": getattr(i, "item_type", "virtual"),
        "stock": i.stock,
        "status": i.status,
    }


def _exchange_order_to_dict(o) -> dict:
    return {
        "id": str(o.id),
        "item_id": o.item_id,
        "points_spent": o.points_cost,
        "status": o.status,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }
