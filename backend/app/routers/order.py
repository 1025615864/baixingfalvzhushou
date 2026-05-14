from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_db
from ..models.user import User
from ..services.order_service import OrderService
from ..utils.deps import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])


class CreateOrderRequest(BaseModel):
    service_type: str
    service_id: int
    amount: float
    payment_method: Optional[str] = None
    coupon_code: Optional[str] = None
    note: Optional[str] = None


class CancelOrderRequest(BaseModel):
    reason: Optional[str] = None


class PayOrderRequest(BaseModel):
    payment_method: str


async def get_order_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderService:
    return OrderService(db)


@router.get("/orders")
async def list_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    return await service.list_orders(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/orders/stats")
async def order_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    return await service.get_order_stats(user_id=current_user.id)


@router.get("/orders/{order_id}")
async def get_order_detail(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    return await service.get_order_detail(user_id=current_user.id, order_id=order_id)


@router.post("/orders")
async def create_order(
    data: CreateOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    return await service.create_order(user_id=current_user.id, data=data.model_dump())


@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    data: CancelOrderRequest = CancelOrderRequest(),
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    return await service.cancel_order(
        user_id=current_user.id, order_id=order_id, reason=data.reason
    )


@router.post("/orders/{order_id}/pay")
async def pay_order(
    order_id: int,
    data: PayOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[OrderService, Depends(get_order_service)],
):
    return await service.pay_order(
        user_id=current_user.id, order_id=order_id, payment_method=data.payment_method
    )
