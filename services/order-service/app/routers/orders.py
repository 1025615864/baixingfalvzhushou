"""订单服务 - API 路由"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus, OrderType, PaymentMethod
from app.services.order_service import order_service
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(
    order_type: OrderType,
    title: str,
    amount: float,
    description: Optional[str] = None,
    business_id: Optional[int] = None,
    business_type: Optional[str] = None,
    discount_amount: float = 0,
    current_user: dict = None,
    db: AsyncSession = Depends(get_db),
):
    """创建订单"""
    user_id = current_user.get("user_id") if current_user else 1

    order = await order_service.create_order(
        session=db,
        user_id=user_id,
        order_type=order_type,
        title=title,
        amount=amount,
        description=description,
        business_id=business_id,
        business_type=business_type,
        discount_amount=discount_amount,
    )

    return {
        "id": order.id,
        "order_no": order.order_no,
        "status": order.status.value,
        "amount": order.amount,
        "actual_amount": order.actual_amount,
    }


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    current_user: dict = None,
    db: AsyncSession = Depends(get_db),
):
    """获取订单详情"""
    user_id = current_user.get("user_id") if current_user else None
    order = await order_service.get_order(db, order_id, user_id)

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return {
        "id": order.id,
        "order_no": order.order_no,
        "order_type": order.order_type.value,
        "title": order.title,
        "description": order.description,
        "amount": order.amount,
        "discount_amount": order.discount_amount,
        "actual_amount": order.actual_amount,
        "status": order.status.value,
        "payment_method": order.payment_method.value if order.payment_method else None,
        "created_at": order.created_at.isoformat(),
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    }


@router.get("/")
async def list_orders(
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = None,
    db: AsyncSession = Depends(get_db),
):
    """获取用户订单列表"""
    user_id = current_user.get("user_id") if current_user else 1

    orders, total = await order_service.list_user_orders(
        db,
        user_id=user_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "id": o.id,
                "order_no": o.order_no,
                "title": o.title,
                "amount": o.amount,
                "actual_amount": o.actual_amount,
                "status": o.status.value,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ],
    }


@router.post("/{order_no}/pay")
async def pay_order(
    order_no: str,
    payment_method: PaymentMethod,
    saga_id: Optional[str] = None,
    current_user: dict = None,
    db: AsyncSession = Depends(get_db),
):
    """支付订单"""
    try:
        order = await order_service.pay_order(db, order_no, payment_method, saga_id)
        return {
            "id": order.id,
            "order_no": order.order_no,
            "status": order.status.value,
            "payment_method": order.payment_method.value,
            "paid_at": order.paid_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_no}/cancel")
async def cancel_order(
    order_no: str,
    reason: Optional[str] = None,
    current_user: dict = None,
    db: AsyncSession = Depends(get_db),
):
    """取消订单"""
    try:
        order = await order_service.cancel_order(db, order_no, reason)
        return {
            "id": order.id,
            "order_no": order.order_no,
            "status": order.status.value,
            "cancelled_at": order.cancelled_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_no}/complete")
async def complete_order(
    order_no: str,
    current_user: dict = None,
    db: AsyncSession = Depends(get_db),
):
    """完成订单"""
    try:
        order = await order_service.complete_order(db, order_no)
        return {
            "id": order.id,
            "order_no": order.order_no,
            "status": order.status.value,
            "completed_at": order.completed_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_no}/refund")
async def refund_order(
    order_no: str,
    reason: Optional[str] = None,
    current_user: dict = None,
    db: AsyncSession = Depends(get_db),
):
    """退款订单"""
    try:
        order = await order_service.refund_order(db, order_no, reason)
        return {
            "id": order.id,
            "order_no": order.order_no,
            "status": order.status.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
