"""支付订单路由"""
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import PaymentOrder

router = APIRouter()


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


def generate_order_no() -> str:
    """生成订单号"""
    now = datetime.now()
    random_part = secrets.token_hex(4).upper()
    return f"ORD{now.strftime('%Y%m%d')}{random_part}"


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    request: CreateOrderRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """创建支付订单"""
    order_no = generate_order_no()

    order = PaymentOrder(
        order_no=order_no,
        user_id=request.user_id,
        order_type=request.order_type,
        amount=request.amount,
        actual_amount=request.amount,
        amount_cents=int(request.amount * 100),
        actual_amount_cents=int(request.amount * 100),
        status="pending",
        payment_method=request.payment_method,
        title=request.title,
        description=request.description,
        expires_at=datetime.now() + timedelta(minutes=30),
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    return OrderResponse.model_validate(order)


@router.get("/orders/{order_no}", response_model=OrderResponse)
async def get_order(
    order_no: str,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取订单详情"""
    result = await db.execute(
        PaymentOrder.__table__.select().where(PaymentOrder.order_no == order_no)
    )
    order = result.fetchone()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse(
        id=order.id,
        order_no=order.order_no,
        user_id=order.user_id,
        amount=float(order.amount),
        status=order.status,
        payment_method=order.payment_method,
        title=order.title,
        expires_at=order.expires_at,
        created_at=order.created_at,
    )


@router.post("/orders/{order_no}/pay")
async def initiate_payment(
    order_no: str,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """发起支付"""
    result = await db.execute(
        PaymentOrder.__table__.select().where(PaymentOrder.order_no == order_no)
    )
    order = result.fetchone()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Order is not pending")

    # TODO: 调用具体的支付通道
    return {
        "order_no": order_no,
        "payment_url": f"https://payment.example.com/pay?order={order_no}",
        "qr_code": "data:image/png;base64,..."
    }
