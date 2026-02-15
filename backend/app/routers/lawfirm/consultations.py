"""咨询预约路由"""

from ...services.lawfirm_service import lawyer_service, consultation_service
from ...utils.deps import get_current_user, require_admin
from ...services.unified_notification_service import unified_notification_service
from ...services.lawfirm.consultations import ConsultationMessageService
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ...database import get_db
from ...models.lawfirm import LawyerConsultation, LawyerConsultationMessage, LawyerReview, Lawyer
from ...models.notification import Notification, NotificationType
from ...models.payment import PaymentOrder, PaymentStatus
from ...models.user import User
from ...schemas.lawfirm import (
    ConsultationCreate, ConsultationResponse, ConsultationListResponse,
)
from pydantic import BaseModel


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    consultation_id: int
    sender_user_id: int
    sender_role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/consultations", tags=["咨询预约"])


def _quantize_amount(amount: float) -> Decimal:
    """金额分 quantized"""
    return Decimal(str(amount)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP)


def _decimal_to_cents(amount: Decimal) -> int:
    """Decimal -> cents"""
    return int((amount * 100).to_integral_value())


def _generate_order_no() -> str:
    """生成订单号"""
    import time
    ts = int(time.time() * 1000)
    return f"CONSULT{ts}"


# ============ 咨询预约相关 ============

@router.post("", response_model=ConsultationResponse, summary="预约咨询")
async def create_consultation(
    data: ConsultationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """预约律师咨询"""
    # 检查律师是否存在
    lawyer = await lawyer_service.get_by_id(db, data.lawyer_id)
    if not lawyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="律师不存在")

    consultation = await consultation_service.create(db, current_user.id, data.model_dump())

    order: PaymentOrder | None = None
    fee = float(getattr(lawyer, "consultation_fee", 0.0) or 0.0)
    if fee > 0:
        amount = _quantize_amount(fee)
        amount_cents = _decimal_to_cents(amount)
        order = PaymentOrder(
            order_no=_generate_order_no(),
            user_id=int(current_user.id),
            order_type="consultation",
            amount=float(amount),
            actual_amount=float(amount),
            amount_cents=amount_cents,
            actual_amount_cents=amount_cents,
            status=PaymentStatus.PENDING,
            title=f"律师咨询：{lawyer.name}",
            description=data.subject,
            related_id=int(consultation.id),
            related_type="lawyer_consultation",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)

    # 发送律师接单提醒通知
    if lawyer.user_id is not None:
        notification = Notification(
            user_id=int(lawyer.user_id),
            type=NotificationType.SYSTEM,
            title="新的咨询预约",
            content=f"您有新的咨询预约：{consultation.subject}。请及时处理。",
            link=f"/lawyer/consultations/{consultation.id}",
            is_read=False,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        # WebSocket 推送（统一 notification payload）
        await unified_notification_service.notify_ws(
            user_id=int(lawyer.user_id),
            title="新的咨询预约",
            content=f"您有新的咨询预约：{consultation.subject}。请及时处理。",
            link=f"/lawyer/consultations/{consultation.id}",
            notification_id=int(notification.id),
        )

    return ConsultationResponse(
        id=consultation.id,
        user_id=consultation.user_id,
        lawyer_id=consultation.lawyer_id,
        subject=consultation.subject,
        description=consultation.description,
        category=consultation.category,
        contact_phone=consultation.contact_phone,
        preferred_time=consultation.preferred_time,
        status=consultation.status,
        admin_note=consultation.admin_note,
        created_at=consultation.created_at,
        updated_at=consultation.updated_at,
        lawyer_name=lawyer.name,
        payment_order_no=order.order_no if order else None,
        payment_status=order.status if order else None,
        payment_amount=order.actual_amount if order else None,
    )


@router.get("", response_model=ConsultationListResponse, summary="获取我的咨询")
async def get_my_consultations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: str | None = None,
):
    """获取我的咨询列表 - 使用批量查询优化N+1问题"""
    consultations, total = await consultation_service.get_by_user(
        db, current_user.id, page, page_size, status_filter
    )

    if not consultations:
        return ConsultationListResponse(
            items=[], total=0, page=page, page_size=page_size)

    # 批量获取律师信息，避免N+1查询
    lawyer_ids = list(set(c.lawyer_id for c in consultations if c.lawyer_id))
    lawyers_map: dict[int, Lawyer] = {}
    if lawyer_ids:
        lawyers_result = await db.execute(
            select(Lawyer).where(Lawyer.id.in_(lawyer_ids))
        )
        lawyers_map = {int(l.id): l for l in lawyers_result.scalars().all()}

    # 批量获取支付订单信息，避免N+1查询
    consultation_ids = [int(c.id) for c in consultations]
    orders_map: dict[int, PaymentOrder] = {}
    if consultation_ids:
        orders_result = await db.execute(
            select(PaymentOrder).where(
                PaymentOrder.related_id.in_(consultation_ids),
                PaymentOrder.related_type == "lawyer_consultation"
            )
        )
        orders_map = {int(o.related_id): o for o in orders_result.scalars().all()}

    # 批量获取评价信息，避免N+1查询
    reviews_map: dict[int, int] = {}  # consultation_id -> review_id
    if consultation_ids:
        reviews_result = await db.execute(
            select(LawyerReview.consultation_id, LawyerReview.id).where(
                LawyerReview.consultation_id.in_(consultation_ids),
                LawyerReview.user_id == current_user.id
            )
        )
        reviews_map = {int(cid): int(rid) for cid, rid in reviews_result.all()}

    items = []
    for c in consultations:
        lawyer = lawyers_map.get(c.lawyer_id)
        order = orders_map.get(int(c.id))
        review_id = reviews_map.get(int(c.id))
        
        # 检查是否可以评价：已完成的咨询且没有评价过
        can_review = c.status == "completed" and review_id is None

        items.append(ConsultationResponse(
            id=c.id,
            user_id=c.user_id,
            lawyer_id=c.lawyer_id,
            subject=c.subject,
            description=c.description,
            category=c.category,
            contact_phone=c.contact_phone,
            preferred_time=c.preferred_time,
            status=c.status,
            admin_note=c.admin_note,
            created_at=c.created_at,
            updated_at=c.updated_at,
            lawyer_name=lawyer.name if lawyer else None,
            payment_order_no=order.order_no if order else None,
            payment_status=order.status if order else None,
            review_id=review_id,
            can_review=can_review,
        ))

    return ConsultationListResponse(
        items=items, total=total, page=page, page_size=page_size)


@router.post("/{consultation_id}/cancel",
             response_model=ConsultationResponse, summary="取消我的咨询")
async def cancel_consultation(
    consultation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """取消咨询预约"""
    consultation = await consultation_service.get_by_id(db, consultation_id)
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="咨询不存在")

    if consultation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作")

    if consultation.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法取消该咨询")

    updated = await consultation_service.update_status(db, consultation_id, "cancelled")
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法取消该咨询")

    # 获取支付订单信息
    order_result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.related_id == consultation_id,
            PaymentOrder.related_type == "lawyer_consultation"
        )
    )
    order = order_result.scalar_one_or_none()

    return ConsultationResponse(
        id=updated.id,
        user_id=updated.user_id,
        lawyer_id=updated.lawyer_id,
        subject=updated.subject,
        description=updated.description,
        category=updated.category,
        contact_phone=updated.contact_phone,
        preferred_time=updated.preferred_time,
        status=updated.status,
        admin_note=updated.admin_note,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        lawyer_name=None,
        payment_order_no=order.order_no if order else None,
        payment_status=order.status if order else None,
    )


@router.get("/{consultation_id}/messages", summary="获取咨询消息列表")
async def get_consultation_messages(
    consultation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """获取咨询消息列表"""
    consultation = await consultation_service.get_by_id(db, consultation_id)
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="咨询不存在")

    is_participant = consultation.user_id == current_user.id
    is_related_lawyer = False
    if consultation.lawyer_id:
        lawyer = await lawyer_service.get_by_id(db, consultation.lawyer_id)
        is_related_lawyer = lawyer and lawyer.user_id == current_user.id

    if not (is_participant or is_related_lawyer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看消息")

    # 获取消息列表
    from sqlalchemy import select, desc
    query = select(LawyerConsultationMessage).where(
        LawyerConsultationMessage.consultation_id == consultation_id
    ).order_by(LawyerConsultationMessage.created_at)

    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    messages = result.scalars().all()

    # 转换为响应格式
    items = []
    for msg in messages:
        items.append(MessageResponse.model_validate(msg))

    # 获取总数
    count_query = select(func.count()).select_from(
        select(LawyerConsultationMessage).where(
            LawyerConsultationMessage.consultation_id == consultation_id
        ).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
