"""退款路由"""
from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.payment import PaymentRefund, RefundStatus, PaymentOrder, PaymentStatus
from ...models.user import User
from ...services.payment import PaymentCoreService, wechatpay_service, alipay_service
from ...utils.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateRefundRequest(BaseModel):
    """创建退款请求"""
    order_no: str = Field(..., description="原订单号")
    amount: float = Field(..., gt=0, description="退款金额")
    reason: str | None = Field(None, max_length=200, description="退款原因")


class RefundResponse(BaseModel):
    """退款响应"""
    refund_no: str
    order_no: str
    amount: float
    status: str
    reason: str | None
    created_at: str


@router.post("/refunds", response_model=RefundResponse, summary="申请退款")
async def create_refund(
    request: CreateRefundRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RefundResponse:
    """申请退款"""
    # 查找原订单
    order = await PaymentCoreService.get_order_by_no(db, request.order_no)
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    
    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此订单")
    
    if order.status != PaymentStatus.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="订单未支付或已退款")
    
    if request.amount > order.actual_amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="退款金额不能大于订单金额")
    
    # 检查是否已有退款
    result = await db.execute(
        select(PaymentRefund).where(PaymentRefund.order_no == request.order_no)
    )
    existing_refund = result.scalar_one_or_none()
    
    if existing_refund and existing_refund.status in [RefundStatus.PENDING, RefundStatus.PROCESSING]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该订单已有待处理退款")
    
    # 创建退款记录
    refund_no = PaymentCoreService.generate_refund_no()
    refund = PaymentRefund(
        refund_no=refund_no,
        order_no=request.order_no,
        user_id=current_user.id,
        amount=request.amount,
        amount_cents=int(request.amount * 100),
        status=RefundStatus.PENDING,
        reason=request.reason,
    )
    db.add(refund)
    await db.flush()
    
    try:
        # 调用第三方支付退款
        if order.payment_method == "wechat":
            result = await wechatpay_service.create_refund(
                db=db,
                order_no=request.order_no,
                refund_no=refund_no,
                amount=request.amount,
                reason=request.reason,
            )
            refund.refund_trade_no = result.get("refund_id")
            refund.status = RefundStatus.PROCESSING
        
        elif order.payment_method == "alipay":
            result = await alipay_service.create_refund(
                order_no=request.order_no,
                refund_no=refund_no,
                amount=request.amount,
                reason=request.reason,
            )
            refund.refund_trade_no = result.get("trade_no")
            refund.status = RefundStatus.SUCCESS
            refund.processed_at = result.get("gmt_refund_pay")
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"不支持的支付方式: {order.payment_method}"
            )
        
        await db.commit()
        await db.refresh(refund)
        
        return RefundResponse(
            refund_no=refund.refund_no,
            order_no=refund.order_no,
            amount=refund.amount,
            status=refund.status,
            reason=refund.reason,
            created_at=refund.created_at.isoformat() if refund.created_at else "",
        )
    
    except Exception as e:
        logger.exception("Refund creation failed")
        refund.status = RefundStatus.FAILED
        refund.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/refunds/{refund_no}", response_model=RefundResponse, summary="查询退款")
async def get_refund(
    refund_no: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RefundResponse:
    """查询退款详情"""
    result = await db.execute(
        select(PaymentRefund).where(PaymentRefund.refund_no == refund_no)
    )
    refund = result.scalar_one_or_none()
    
    if not refund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="退款记录不存在")
    
    if refund.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此退款记录")
    
    return RefundResponse(
        refund_no=refund.refund_no,
        order_no=refund.order_no,
        amount=refund.amount,
        status=refund.status,
        reason=refund.reason,
        created_at=refund.created_at.isoformat() if refund.created_at else "",
    )


@router.get("/refunds", summary="获取用户退款列表")
async def get_user_refunds(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> dict[str, Any]:
    """获取当前用户的退款列表"""
    query = select(PaymentRefund).where(PaymentRefund.user_id == current_user.id)
    
    if status:
        query = query.where(PaymentRefund.status == status)
    
    # 获取总数
    count_result = await db.execute(
        select(PaymentRefund).where(PaymentRefund.user_id == current_user.id)
    )
    total = len(count_result.scalars().all())
    
    # 分页
    query = query.order_by(PaymentRefund.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    refunds = list(result.scalars().all())
    
    return {
        "items": [
            RefundResponse(
                refund_no=refund.refund_no,
                order_no=refund.order_no,
                amount=refund.amount,
                status=refund.status,
                reason=refund.reason,
                created_at=refund.created_at.isoformat() if refund.created_at else "",
            )
            for refund in refunds
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
