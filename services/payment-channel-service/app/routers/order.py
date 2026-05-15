import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import PaymentOrder
from ..services.channels import get_adapter
from ..services.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter()
payment_service = PaymentService()


class CreateOrderRequest(BaseModel):
    user_id: int
    order_type: str
    amount: float
    title: str
    description: str = ""
    payment_method: str = "alipay"


class OrderResponse(BaseModel):
    id: int
    order_no: str
    user_id: int
    amount: float
    status: str
    payment_method: str
    title: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int


class PaymentStatusResponse(BaseModel):
    order_no: str
    status: str
    provider: str
    provider_status: str
    trade_no: Optional[str] = None
    paid_at: Optional[datetime] = None


def generate_order_no() -> str:
    now = datetime.now()
    random_part = secrets.token_hex(4).upper()
    return f"ORD{now.strftime('%Y%m%d')}{random_part}"


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    request: CreateOrderRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    order_no = generate_order_no()

    order = await payment_service.create_payment(
        db=db,
        order_no=order_no,
        user_id=request.user_id,
        order_type=request.order_type,
        amount=request.amount,
        title=request.title,
        description=request.description,
        payment_method=request.payment_method,
    )

    await db.commit()
    await db.refresh(order)

    return OrderResponse.model_validate(order)


@router.get("/orders", response_model=OrderListResponse)
async def list_orders(
    user_id: int = Query(..., description="用户ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, alias="status", description="订单状态筛选"),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    query = select(PaymentOrder).where(PaymentOrder.user_id == user_id)

    if status_filter:
        query = query.where(PaymentOrder.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(PaymentOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    orders = result.scalars().all()

    items = [OrderResponse.model_validate(order) for order in orders]

    return OrderListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/orders/{order_no}", response_model=OrderResponse)
async def get_order(
    order_no: str,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse.model_validate(order)


@router.post("/orders/{order_no}/pay")
async def initiate_payment(
    order_no: str,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Order is not pending")

    provider = order.payment_method or "alipay"

    try:
        adapter = get_adapter(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported payment provider: {provider}")

    try:
        payment_result = await adapter.create_payment(
            order_no=order.order_no,
            amount=order.amount_cents,
            title=order.title,
            description=order.description or "",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment initiation failed: {str(e)}")

    return {
        "order_no": order_no,
        "payment_url": payment_result.get("payment_url", ""),
        "qr_code": payment_result.get("qr_code", ""),
        "provider": provider,
    }


@router.get("/orders/{order_no}/status", response_model=PaymentStatusResponse)
async def query_payment_status(
    order_no: str,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    try:
        status_info = await payment_service.query_payment_status(db, order_no)
    except ValueError:
        raise HTTPException(status_code=404, detail="Order not found")

    provider = status_info["payment_method"] or "alipay"

    try:
        adapter = get_adapter(provider)
        provider_result = await adapter.query_payment(order_no)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported payment provider: {provider}")
    except Exception:
        logger.error("Failed to query payment from provider %s for order %s", provider, order_no)
        provider_result = {}

    if provider == "alipay":
        provider_status = provider_result.get("trade_status", "UNKNOWN")
    elif provider == "wechat":
        provider_status = provider_result.get("trade_state", "UNKNOWN")
    else:
        provider_status = "UNKNOWN"

    return PaymentStatusResponse(
        order_no=order_no,
        status=status_info["status"],
        provider=provider,
        provider_status=provider_status,
        trade_no=status_info.get("trade_no"),
        paid_at=status_info.get("paid_at"),
    )
