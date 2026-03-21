"""视频咨询预约路由"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.user import User
from ..models.lawfirm import Lawyer
from ..schemas.video_consultation import (
    VideoConsultationCreate,
    VideoConsultationResponse,
    VideoConsultationListResponse,
    VideoScheduleCreate,
    VideoScheduleUpdate,
    VideoScheduleResponse,
    VideoScheduleListResponse,
    VideoAvailableSlotsResponse,
    VideoSlotResponse,
    VideoConsultationFeeResponse,
    MemberDiscountResponse,
    UserUsageResponse,
)
from ..services.video_consultation import (
    video_consultation_service,
    video_schedule_service,
)
from ..utils.deps import get_current_user


router = APIRouter(prefix="/video-consultations", tags=["视频咨询"])


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
    return f"VC{ts}"


# ============ 视频咨询相关 ============

@router.post("", response_model=VideoConsultationResponse, summary="预约视频咨询")
async def create_video_consultation(
    data: VideoConsultationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """预约视频咨询"""
    # 检查律师是否存在
    lawyer_result = await db.execute(
        select(Lawyer).where(Lawyer.id == data.lawyer_id)
    )
    lawyer = lawyer_result.scalar_one_or_none()
    if not lawyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="律师不存在")

    # 创建预约
    try:
        booking = await video_consultation_service.create_booking(
            db,
            current_user,
            data.lawyer_id,
            data.scheduled_time,
            data.subject,
            data.description,
            data.category,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e))

    # 获取预约详情
    consultation = await video_consultation_service.get_by_id(db, booking["id"])
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建预约失败")

    # 检查是否需要支付
    payment_amount = booking.get("actual_fee", 0)
    order = None
    if payment_amount > 0:
        from ..models.payment import PaymentOrder, PaymentStatus
        amount = _quantize_amount(payment_amount)
        amount_cents = _decimal_to_cents(amount)
        order = PaymentOrder(
            order_no=_generate_order_no(),
            user_id=int(current_user.id),
            order_type="video_consultation",
            amount=float(amount),
            actual_amount=float(amount),
            amount_cents=amount_cents,
            actual_amount_cents=amount_cents,
            status=PaymentStatus.PENDING,
            title=f"视频咨询：{lawyer.name}",
            description=data.subject,
            related_id=int(consultation.id),
            related_type="video_consultation",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)

    return VideoConsultationResponse(
        id=consultation.id,
        user_id=consultation.user_id,
        lawyer_id=consultation.lawyer_id,
        subject=consultation.subject,
        description=consultation.description,
        category=consultation.category,
        scheduled_time=consultation.scheduled_time,
        duration_minutes=consultation.duration_minutes,
        meeting_room_id=consultation.meeting_room_id,
        meeting_password=consultation.meeting_password,
        meeting_url=consultation.meeting_url,
        status=consultation.status,
        payment_status=order.status.value if order else consultation.payment_status,
        payment_amount=consultation.payment_amount,
        is_free=consultation.is_free,
        discount_rate=consultation.discount_rate,
        started_at=consultation.started_at,
        ended_at=consultation.ended_at,
        completed_at=consultation.completed_at,
        cancelled_at=consultation.cancelled_at,
        created_at=consultation.created_at,
        updated_at=consultation.updated_at,
        lawyer_name=lawyer.name,
    )


@router.get("", response_model=VideoConsultationListResponse, summary="获取我的视频咨询")
async def get_my_video_consultations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: str | None = None,
):
    """获取用户的视频咨询列表"""
    consultations, total = await video_consultation_service.get_user_bookings(
        db, current_user.id, page, page_size, status_filter
    )

    if not consultations:
        return VideoConsultationListResponse(
            items=[], total=0, page=page, page_size=page_size)

    # 批量获取律师信息
    lawyer_ids = list(set(c.lawyer_id for c in consultations if c.lawyer_id))
    lawyers_map: dict[int, Lawyer] = {}
    if lawyer_ids:
        lawyers_result = await db.execute(
            select(Lawyer).where(Lawyer.id.in_(lawyer_ids))
        )
        lawyers_map = {int(l.id): l for l in lawyers_result.scalars().all()}

    items = []
    for c in consultations:
        lawyer = lawyers_map.get(c.lawyer_id)
        items.append(VideoConsultationResponse(
            id=c.id,
            user_id=c.user_id,
            lawyer_id=c.lawyer_id,
            subject=c.subject,
            description=c.description,
            category=c.category,
            scheduled_time=c.scheduled_time,
            duration_minutes=c.duration_minutes,
            meeting_room_id=c.meeting_room_id,
            meeting_password=c.meeting_password,
            meeting_url=c.meeting_url,
            status=c.status,
            payment_status=c.payment_status,
            payment_amount=c.payment_amount,
            is_free=c.is_free,
            discount_rate=c.discount_rate,
            started_at=c.started_at,
            ended_at=c.ended_at,
            completed_at=c.completed_at,
            cancelled_at=c.cancelled_at,
            created_at=c.created_at,
            updated_at=c.updated_at,
            lawyer_name=lawyer.name if lawyer else None,
        ))

    return VideoConsultationListResponse(
        items=items, total=total, page=page, page_size=page_size)


@router.get("/{consultation_id}", response_model=VideoConsultationResponse, summary="获取视频咨询详情")
async def get_video_consultation(
    consultation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取视频咨询详情"""
    consultation = await video_consultation_service.get_by_id(
        db, consultation_id
    )
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频咨询不存在")

    # 检查权限
    if consultation.user_id != current_user.id:
        # 检查是否是关联律师
        lawyer_result = await db.execute(
            select(Lawyer).where(
                Lawyer.id == consultation.lawyer_id,
                Lawyer.user_id == current_user.id
            )
        )
        lawyer = lawyer_result.scalar_one_or_none()
        if not lawyer:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看")

    # 获取律师信息
    lawyer_result = await db.execute(
        select(Lawyer).where(Lawyer.id == consultation.lawyer_id)
    )
    lawyer = lawyer_result.scalar_one_or_none()

    return VideoConsultationResponse(
        id=consultation.id,
        user_id=consultation.user_id,
        lawyer_id=consultation.lawyer_id,
        subject=consultation.subject,
        description=consultation.description,
        category=consultation.category,
        scheduled_time=consultation.scheduled_time,
        duration_minutes=consultation.duration_minutes,
        meeting_room_id=consultation.meeting_room_id,
        meeting_password=consultation.meeting_password,
        meeting_url=consultation.meeting_url,
        status=consultation.status,
        payment_status=consultation.payment_status,
        payment_amount=consultation.payment_amount,
        is_free=consultation.is_free,
        discount_rate=consultation.discount_rate,
        started_at=consultation.started_at,
        ended_at=consultation.ended_at,
        completed_at=consultation.completed_at,
        cancelled_at=consultation.cancelled_at,
        created_at=consultation.created_at,
        updated_at=consultation.updated_at,
        lawyer_name=lawyer.name if lawyer else None,
    )


@router.post("/{consultation_id}/confirm", summary="确认视频咨询")
async def confirm_video_consultation(
    consultation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """确认视频咨询预约（律师端）"""
    consultation = await video_consultation_service.get_by_id(
        db, consultation_id
    )
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频咨询不存在")

    # 检查是否是关联律师
    lawyer_result = await db.execute(
        select(Lawyer).where(
            Lawyer.id == consultation.lawyer_id,
            Lawyer.user_id == current_user.id
        )
    )
    lawyer = lawyer_result.scalar_one_or_none()
    if not lawyer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有接单律师可以确认")

    try:
        consultation = await video_consultation_service.confirm_booking(
            db, consultation_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e))

    return {"id": consultation.id, "status": consultation.status}


@router.post("/{consultation_id}/start", summary="开始视频咨询")
async def start_video_consultation(
    consultation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """开始视频咨询"""
    consultation = await video_consultation_service.get_by_id(
        db, consultation_id
    )
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频咨询不存在")

    # 检查权限
    is_user = consultation.user_id == current_user.id
    lawyer_result = await db.execute(
        select(Lawyer).where(
            Lawyer.id == consultation.lawyer_id,
            Lawyer.user_id == current_user.id
        )
    )
    is_lawyer = lawyer_result.scalar_one_or_none() is not None

    if not (is_user or is_lawyer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作")

    try:
        consultation = await video_consultation_service.start_consultation(
            db, consultation_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e))

    return {
        "id": consultation.id,
        "status": consultation.status,
        "meeting_url": consultation.meeting_url,
    }


@router.post("/{consultation_id}/end", summary="结束视频咨询")
async def end_video_consultation(
    consultation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """结束视频咨询"""
    consultation = await video_consultation_service.get_by_id(
        db, consultation_id
    )
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频咨询不存在")

    # 检查权限
    is_user = consultation.user_id == current_user.id
    lawyer_result = await db.execute(
        select(Lawyer).where(
            Lawyer.id == consultation.lawyer_id,
            Lawyer.user_id == current_user.id
        )
    )
    is_lawyer = lawyer_result.scalar_one_or_none() is not None

    if not (is_user or is_lawyer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作")

    try:
        consultation = await video_consultation_service.end_consultation(
            db, consultation_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e))

    return {
        "id": consultation.id,
        "status": consultation.status,
        "duration_minutes": consultation.duration_minutes,
    }


@router.post("/{consultation_id}/cancel", summary="取消视频咨询")
async def cancel_video_consultation(
    consultation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """取消视频咨询预约"""
    consultation = await video_consultation_service.get_by_id(
        db, consultation_id
    )
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频咨询不存在")

    if consultation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作")

    try:
        consultation = await video_consultation_service.cancel_booking(
            db, consultation_id, current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e))

    return {"id": consultation.id, "status": consultation.status}


# ============ 律师视频排班相关 ============

@router.get("/lawyers/{lawyer_id}/available-slots",
           response_model=VideoAvailableSlotsResponse, summary="查询律师可用视频时段")
async def get_lawyer_video_slots(
    lawyer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    date: datetime,
):
    """查询律师在指定日期的可用视频时段"""
    slots = await video_schedule_service.get_available_slots(db, lawyer_id, date)

    slot_responses = []
    for slot in slots:
        slot_responses.append(VideoSlotResponse(
            schedule_id=slot["schedule_id"],
            date=slot["date"],
            start_time=slot["start_time"],
            end_time=slot["end_time"],
            consultation_fee=slot["consultation_fee"],
            available_count=slot["available_count"],
        ))

    return VideoAvailableSlotsResponse(
        lawyer_id=lawyer_id, date=date, slots=slot_responses)


@router.get("/lawyers/{lawyer_id}/fee",
           response_model=VideoConsultationFeeResponse, summary="获取律师视频咨询费用")
async def get_lawyer_video_fee(
    lawyer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取律师视频咨询费用"""
    fee_info = await video_consultation_service.get_video_consultation_fee(
        db, lawyer_id
    )

    return VideoConsultationFeeResponse(
        fee=fee_info["fee"],
        duration=fee_info["duration"],
        enabled=fee_info["enabled"],
    )


# ============ 会员权益相关 ============

@router.get("/member-discount", response_model=MemberDiscountResponse,
           summary="获取我的会员折扣")
async def get_member_discount(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取当前用户的会员折扣"""
    discount_info = await video_consultation_service.calculate_member_discount(
        db, current_user
    )

    return MemberDiscountResponse(
        tier=discount_info["tier"],
        discount_rate=discount_info["discount_rate"],
        free_monthly_count=discount_info["free_monthly_count"],
        is_free=discount_info["is_free"],
    )


@router.get("/usage", response_model=UserUsageResponse, summary="获取我的使用情况")
async def get_my_usage(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取本月视频咨询使用情况"""
    usage = await video_consultation_service.get_user_usage(
        db, current_user.id
    )

    return UserUsageResponse(
        year_month=usage["year_month"],
        free_used=usage["free_used"],
        paid_count=usage["paid_count"],
        remaining_free=usage["remaining_free"],
        tier=usage.get("tier"),
    )