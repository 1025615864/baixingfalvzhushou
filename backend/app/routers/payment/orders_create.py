from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.utils.deps import get_current_user
from app.models.user import User
from app.models.payment import PaymentOrder, PaymentStatus, OrderType
from app.services.payment_service import payment_service

router = APIRouter()


class CreateOrderRequest(BaseModel):
    order_type: str
    amount: float
    title: str = "支付订单"
    description: str | None = None
    payment_method: str | None = None
    related_id: int | None = None
    related_type: str | None = None


VALID_ORDER_TYPES = {"consultation", "service", "vip", "recharge", "light_consult_review", "ai_pack"}


@router.post("/orders")
async def create_order(
    data: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.order_type not in VALID_ORDER_TYPES:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"ok": False, "error": f"无效的订单类型: {data.order_type}"})

    try:
        order = await payment_service.create_order(
            db=db,
            user_id=current_user.id,
            amount=data.amount,
            order_type=data.order_type,
            title=data.title,
            description=data.description,
            related_id=data.related_id,
            related_type=data.related_type,
        )
    except ValueError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})

    return {
        "order_no": order.order_no,
        "amount": order.actual_amount,
        "status": order.status,
        "title": order.title,
        "created_at": str(order.created_at) if order.created_at else None,
    }


@router.get("/orders")
async def list_orders(
    page: int = 1,
    page_size: int = 10,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    orders, total = await payment_service.get_user_orders(
        db, user_id=current_user.id, page=page, page_size=page_size,
        status_filter=status_filter,
    )
    items = []
    for o in orders:
        items.append({
            "order_no": o.order_no, "amount": o.actual_amount,
            "status": o.status, "title": o.title,
            "payment_method": o.payment_method,
            "created_at": str(o.created_at) if o.created_at else None,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/orders/{order_no}")
async def get_order(order_no: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    order = await payment_service.get_order(db, order_no)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看")
    return {
        "order_no": order.order_no, "amount": order.actual_amount,
        "status": order.status, "title": order.title,
        "description": order.description,
        "payment_method": order.payment_method,
        "trade_no": order.trade_no,
        "paid_at": str(order.paid_at) if order.paid_at else None,
        "created_at": str(order.created_at) if order.created_at else None,
    }


@router.post("/orders/{order_no}/cancel")
async def cancel_order(order_no: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        order = await payment_service.cancel_order(db, order_no=order_no, user_id=current_user.id)
        return {"message": "订单已取消", "status": order.status}
    except ValueError as e:
        if "不允许取消" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/balance")
async def get_balance(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    balance = await payment_service.get_user_balance(db, user_id=current_user.id)
    return {"balance": balance.balance, "frozen": balance.frozen}


@router.get("/balance/transactions")
async def get_balance_transactions(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    transactions, total = await payment_service.get_balance_transactions(db, user_id=current_user.id, page=page, page_size=page_size)
    items = []
    for t in transactions:
        items.append({
            "id": t.id, "type": t.type, "amount": t.amount,
            "balance_before": t.balance_before, "balance_after": t.balance_after,
            "description": t.description,
            "created_at": str(t.created_at) if t.created_at else None,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/pricing")
async def get_pricing(db: AsyncSession = Depends(get_db)):
    pricing = await payment_service.get_pricing(db)
    return pricing
