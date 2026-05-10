"""积分路由"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ..database import get_db
from ..models import PointsUser, PointsHistory, PointsMallItem, PointsExchangeOrder
from ..services.points_service import (
    add_points as svc_add_points,
    deduct_points as svc_deduct_points,
    get_points_history as svc_get_points_history,
    daily_check_in as svc_daily_check_in,
    get_check_in_status as svc_get_check_in_status,
    list_mall_items as svc_list_mall_items,
    exchange_item as svc_exchange_item,
    get_exchange_orders as svc_get_exchange_orders,
)

router = APIRouter()


class PointsResponse(BaseModel):
    user_id: int
    balance: int
    total_earned: int
    total_spent: int

    class Config:
        from_attributes = True


class PointsHistoryItem(BaseModel):
    id: int
    change: int
    balance_after: int
    source: str
    description: str | None
    created_at: str

    class Config:
        from_attributes = True


class PointsHistoryResponse(BaseModel):
    items: List[PointsHistoryItem]
    total: int
    page: int
    page_size: int


class PointsChangeRequest(BaseModel):
    change: int
    source: str
    description: str | None = None
    reference_id: str | None = None


class AddPointsRequest(BaseModel):
    user_id: int
    points: int
    source: str
    description: str | None = None


class DeductPointsRequest(BaseModel):
    user_id: int
    points: int
    source: str
    description: str | None = None


class CheckInRequest(BaseModel):
    user_id: int


class MallItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    points_cost: int
    stock: int
    image_url: str | None
    status: str

    class Config:
        from_attributes = True


class MallItemListResponse(BaseModel):
    items: List[MallItemResponse]
    total: int
    page: int
    page_size: int


class ExchangeOrderResponse(BaseModel):
    id: int
    user_id: int
    item_id: int
    points_cost: int
    status: str
    created_at: str
    completed_at: str | None

    class Config:
        from_attributes = True


class ExchangeOrderListResponse(BaseModel):
    items: List[ExchangeOrderResponse]
    total: int
    page: int
    page_size: int


class ExchangeRequest(BaseModel):
    user_id: int


@router.get("/{user_id}", response_model=PointsResponse)
async def get_balance(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PointsUser).where(PointsUser.user_id == user_id)
    )
    points_user = result.scalar_one_or_none()

    if not points_user:
        points_user = PointsUser(user_id=user_id, balance=0, total_earned=0, total_spent=0)
        db.add(points_user)
        await db.commit()
        await db.refresh(points_user)

    return PointsResponse(
        user_id=points_user.user_id,
        balance=points_user.balance,
        total_earned=points_user.total_earned,
        total_spent=points_user.total_spent
    )


@router.get("/{user_id}/history", response_model=PointsHistoryResponse)
async def get_history(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(PointsHistory).where(PointsHistory.user_id == user_id)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(desc(PointsHistory.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    history = result.scalars().all()

    items = [
        PointsHistoryItem(
            id=h.id,
            change=h.change,
            balance_after=h.balance_after,
            source=h.source,
            description=h.description,
            created_at=h.created_at.isoformat() if h.created_at else ""
        )
        for h in history
    ]

    return PointsHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/{user_id}/change")
async def change_points(
    user_id: int,
    request: PointsChangeRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PointsUser).where(PointsUser.user_id == user_id)
    )
    points_user = result.scalar_one_or_none()

    if not points_user:
        points_user = PointsUser(user_id=user_id, balance=0, total_earned=0, total_spent=0)
        db.add(points_user)
        await db.flush()

    new_balance = points_user.balance + request.change

    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Insufficient points")

    history = PointsHistory(
        user_id=user_id,
        change=request.change,
        balance_after=new_balance,
        source=request.source,
        description=request.description,
        reference_id=request.reference_id
    )
    db.add(history)

    points_user.balance = new_balance
    if request.change > 0:
        points_user.total_earned += request.change
    else:
        points_user.total_spent += abs(request.change)

    await db.commit()

    return {
        "success": True,
        "balance": new_balance,
        "change": request.change
    }


@router.post("/add")
async def add_points_endpoint(
    request: AddPointsRequest,
    db: AsyncSession = Depends(get_db)
):
    history = await svc_add_points(
        db, request.user_id, request.points, request.source, request.description or ""
    )
    await db.commit()
    return {
        "id": history.id,
        "user_id": history.user_id,
        "change": history.change,
        "balance_after": history.balance_after,
        "source": history.source,
        "description": history.description,
        "created_at": history.created_at.isoformat() if history.created_at else "",
    }


@router.post("/deduct")
async def deduct_points_endpoint(
    request: DeductPointsRequest,
    db: AsyncSession = Depends(get_db)
):
    history = await svc_deduct_points(
        db, request.user_id, request.points, request.source, request.description or ""
    )
    await db.commit()
    return {
        "id": history.id,
        "user_id": history.user_id,
        "change": history.change,
        "balance_after": history.balance_after,
        "source": history.source,
        "description": history.description,
        "created_at": history.created_at.isoformat() if history.created_at else "",
    }


@router.get("/history", response_model=PointsHistoryResponse)
async def get_points_history_endpoint(
    user_id: int = Query(...),
    source: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    result = await svc_get_points_history(db, user_id, source, page, page_size)
    items = [
        PointsHistoryItem(
            id=h.id,
            change=h.change,
            balance_after=h.balance_after,
            source=h.source,
            description=h.description,
            created_at=h.created_at.isoformat() if h.created_at else "",
        )
        for h in result["items"]
    ]
    return PointsHistoryResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.post("/check-in")
async def daily_check_in_endpoint(
    request: CheckInRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await svc_daily_check_in(db, request.user_id)
    await db.commit()
    return result


@router.get("/check-in/status")
async def get_check_in_status_endpoint(
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    return await svc_get_check_in_status(db, user_id)


@router.get("/mall", response_model=MallItemListResponse)
async def list_mall_items_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    result = await svc_list_mall_items(db, page, page_size)
    items = [
        MallItemResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            points_cost=item.points_cost,
            stock=item.stock,
            image_url=item.image_url,
            status=item.status,
        )
        for item in result["items"]
    ]
    return MallItemListResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.post("/mall/{item_id}/exchange", response_model=ExchangeOrderResponse)
async def exchange_item_endpoint(
    item_id: int,
    request: ExchangeRequest,
    db: AsyncSession = Depends(get_db)
):
    order = await svc_exchange_item(db, request.user_id, item_id)
    await db.commit()
    return ExchangeOrderResponse(
        id=order.id,
        user_id=order.user_id,
        item_id=order.item_id,
        points_cost=order.points_cost,
        status=order.status,
        created_at=order.created_at.isoformat() if order.created_at else "",
        completed_at=order.completed_at.isoformat() if order.completed_at else None,
    )


@router.get("/exchange-orders", response_model=ExchangeOrderListResponse)
async def get_exchange_orders_endpoint(
    user_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    result = await svc_get_exchange_orders(db, user_id, page, page_size)
    items = [
        ExchangeOrderResponse(
            id=o.id,
            user_id=o.user_id,
            item_id=o.item_id,
            points_cost=o.points_cost,
            status=o.status,
            created_at=o.created_at.isoformat() if o.created_at else "",
            completed_at=o.completed_at.isoformat() if o.completed_at else None,
        )
        for o in result["items"]
    ]
    return ExchangeOrderListResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )
