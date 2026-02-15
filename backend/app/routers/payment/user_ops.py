from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.payment import BalanceTransaction, PaymentOrder, PaymentStatus
from ...models.user import User
from ...utils.deps import get_current_user
from . import post_processing as payment_post

router = APIRouter()


class OrderResponse(BaseModel):
    id: int
    order_no: str
    order_type: str
    amount: float
    actual_amount: float
    status: str
    payment_method: str | None
    title: str
    created_at: object
    paid_at: object | None


class BalanceResponse(BaseModel):
    balance: float
    frozen: float
    total_recharged: float
    total_consumed: float


@router.get("/orders", summary="获取订单列表")
async def get_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: str | None = None,
):
    """获取当前用户的订单列表"""
    query = select(PaymentOrder).where(PaymentOrder.user_id == current_user.id)

    if status_filter:
        query = query.where(PaymentOrder.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total: int = int(await db.scalar(count_query) or 0)

    query = query.order_by(PaymentOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()

    items = [
        OrderResponse(
            id=o.id,
            order_no=o.order_no,
            order_type=o.order_type,
            amount=o.amount,
            actual_amount=o.actual_amount,
            status=o.status,
            payment_method=o.payment_method,
            title=o.title,
            created_at=o.created_at,
            paid_at=o.paid_at,
        )
        for o in orders
    ]

    return {"items": items, "total": total}


@router.get("/orders/{order_no}", summary="获取订单详情")
async def get_order_detail(
    order_no: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取订单详情"""
    result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.order_no == order_no,
            PaymentOrder.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return OrderResponse(
        id=order.id,
        order_no=order.order_no,
        order_type=order.order_type,
        amount=order.amount,
        actual_amount=order.actual_amount,
        status=order.status,
        payment_method=order.payment_method,
        title=order.title,
        created_at=order.created_at,
        paid_at=order.paid_at,
    )


@router.post("/orders/{order_no}/cancel", summary="取消订单")
async def cancel_order(
    order_no: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """取消订单"""
    result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.order_no == order_no,
            PaymentOrder.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status != PaymentStatus.PENDING:
        raise HTTPException(status_code=400, detail="只能取消待支付订单")

    order.status = PaymentStatus.CANCELLED
    await db.commit()

    return {"message": "订单已取消"}


@router.get("/balance", summary="获取余额")
async def get_balance(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取当前用户余额"""
    balance = await payment_post.get_or_create_balance(db, current_user.id)

    return BalanceResponse(
        balance=balance.balance,
        frozen=balance.frozen,
        total_recharged=balance.total_recharged,
        total_consumed=balance.total_consumed,
    )


@router.get("/balance/transactions", summary="获取余额交易记录")
async def get_balance_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """获取余额交易记录"""
    query = select(BalanceTransaction).where(
        BalanceTransaction.user_id == current_user.id)

    count_query = select(func.count()).select_from(query.subquery())
    total: int = int(await db.scalar(count_query) or 0)

    query = query.order_by(BalanceTransaction.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    transactions = result.scalars().all()

    items = [
        {
            "id": t.id,
            "type": t.type,
            "amount": t.amount,
            "balance_after": t.balance_after,
            "description": t.description,
            "created_at": t.created_at,
        }
        for t in transactions
    ]

    return {"items": items, "total": total}
