from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.order_service import order_service
from app.models.order import OrderStatus, OrderType, PaymentMethod

router = APIRouter()
admin_router = APIRouter()


@router.get("")
async def list_orders(
    user_id: int = Query(...),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    order_status = None
    if status:
        try:
            order_status = OrderStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的订单状态: {status}")

    orders, total = await order_service.list_user_orders(
        db, user_id=user_id, status=order_status,
        offset=(page - 1) * page_size, limit=page_size,
    )
    return {
        "items": [_order_to_dict(o) for o in orders],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{order_id}")
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    try:
        order_id_int = int(order_id)
        order = await order_service.get_order(db, order_id=order_id_int)
    except ValueError:
        order = await order_service.get_order_by_no(db, order_no=order_id)

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return _order_to_dict(order)


@router.post("")
async def create_order(body: dict, db: AsyncSession = Depends(get_db)):
    try:
        order_type = OrderType(body.get("order_type", "consultation"))
    except ValueError:
        order_type = OrderType.CONSULTATION

    order = await order_service.create_order(
        db,
        user_id=body.get("user_id", 1),
        order_type=order_type,
        title=body.get("title", ""),
        amount=float(body.get("amount", 0)),
        description=body.get("description"),
        business_id=body.get("business_id"),
        business_type=body.get("business_type"),
        discount_amount=float(body.get("discount_amount", 0)),
    )
    await db.commit()
    return _order_to_dict(order)


@router.put("/{order_id}/status")
async def update_status(order_id: str, body: dict, db: AsyncSession = Depends(get_db)):
    status = body.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="缺少 status 字段")

    if status == "paid":
        try:
            payment_method = PaymentMethod(body.get("payment_method", "alipay"))
        except ValueError:
            payment_method = PaymentMethod.ALIPAY
        try:
            order = await order_service.get_order_by_no(db, order_no=order_id)
            if not order:
                try:
                    order = await order_service.get_order(db, order_id=int(order_id))
                except ValueError:
                    raise HTTPException(status_code=404, detail="订单不存在")
            order = await order_service.pay_order(db, order_no=order.order_no, payment_method=payment_method)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif status == "completed":
        try:
            order = await order_service.get_order_by_no(db, order_no=order_id)
            if not order:
                try:
                    order = await order_service.get_order(db, order_id=int(order_id))
                except ValueError:
                    raise HTTPException(status_code=404, detail="订单不存在")
            order = await order_service.complete_order(db, order_no=order.order_no)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif status == "cancelled":
        reason = body.get("reason", "用户取消")
        try:
            order = await order_service.get_order_by_no(db, order_no=order_id)
            if not order:
                try:
                    order = await order_service.get_order(db, order_id=int(order_id))
                except ValueError:
                    raise HTTPException(status_code=404, detail="订单不存在")
            order = await order_service.cancel_order(db, order_no=order.order_no, reason=reason)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail=f"不支持的状态变更: {status}")

    await db.commit()
    return _order_to_dict(order)


@router.delete("/{order_id}/cancel")
async def cancel_order(order_id: str, db: AsyncSession = Depends(get_db)):
    try:
        order = await order_service.get_order_by_no(db, order_no=order_id)
        if not order:
            try:
                order = await order_service.get_order(db, order_id=int(order_id))
            except ValueError:
                raise HTTPException(status_code=404, detail="订单不存在")
        order = await order_service.cancel_order(db, order_no=order.order_no)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return {"success": True}


@admin_router.get("")
async def admin_list_orders(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    order_status = None
    if status:
        try:
            order_status = OrderStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的订单状态: {status}")

    orders, total = await order_service.list_all_orders(
        db, status=order_status,
        offset=(page - 1) * page_size, limit=page_size,
    )
    return {
        "items": [_order_to_dict(o) for o in orders],
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
    }
