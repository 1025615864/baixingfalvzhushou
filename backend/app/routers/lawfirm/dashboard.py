"""数据看板路由"""

import json
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.lawfirm import LawyerConsultation, LawyerReview
from ...models.notification import Notification, NotificationType
from ...models.payment import PaymentOrder
from ...models.settlement import LawyerWallet, WithdrawalRequest, LawyerIncomeRecord
from ...models.user import User
from ...schemas.lawfirm import (
    LawyerDashboardResponse,
    LawyerWorkbenchResponse,
    IncomeTrendResponse,
    ConsultationStatsResponse,
    LawyerPerformanceResponse,
    LawyerRankingResponse,
    LawyerWalletInfo,
    LawyerConsultationStats,
    LawyerReviewStats,
    ConsultationResponse,
    ReviewResponse,
)
from ...services.lawfirm_service import lawyer_stats_service
from ...utils.deps import get_current_user

router = APIRouter(prefix="/lawyer", tags=["数据看板"])


async def _ensure_wallet(db: AsyncSession, lawyer_id: int) -> LawyerWallet:
    result = await db.execute(
        select(LawyerWallet).where(LawyerWallet.lawyer_id == int(lawyer_id))
    )
    wallet = result.scalar_one_or_none()
    if wallet:
        return wallet

    wallet = LawyerWallet(
        lawyer_id=int(lawyer_id),
        total_income=0.0,
        withdrawn_amount=0.0,
        pending_amount=0.0,
        frozen_amount=0.0,
        available_amount=0.0,
    )
    db.add(wallet)
    await db.flush()
    return wallet


def _serialize_consultation(consultation: LawyerConsultation,
                            lawyer_name: str | None) -> ConsultationResponse:
    return ConsultationResponse(
        id=int(consultation.id),
        user_id=int(consultation.user_id),
        lawyer_id=int(consultation.lawyer_id),
        subject=consultation.subject,
        description=consultation.description,
        category=consultation.category,
        contact_phone=consultation.contact_phone,
        preferred_time=consultation.preferred_time,
        status=consultation.status,
        admin_note=consultation.admin_note,
        created_at=consultation.created_at,
        updated_at=consultation.updated_at,
        lawyer_name=lawyer_name,
        payment_order_no=None,
        payment_status=None,
        payment_amount=None,
        review_id=None,
        can_review=False,
    )


def _serialize_review(review: LawyerReview) -> ReviewResponse:
    tags = json.loads(review.tags) if review.tags else []
    return ReviewResponse(
        id=int(review.id),
        lawyer_id=int(review.lawyer_id),
        user_id=int(review.user_id),
        consultation_id=review.consultation_id,
        rating=int(review.rating),
        content=review.content,
        is_anonymous=bool(review.is_anonymous),
        professionalism=review.professionalism,
        responsiveness=review.responsiveness,
        attitude=review.attitude,
        tags=tags,
        created_at=review.created_at,
        username=None,
    )


async def _get_unread_notifications(db: AsyncSession, user_id: int) -> int:
    unread = await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == int(user_id),
            Notification.is_read == False,
        )
    )
    return int(unread or 0)


async def _get_consultation_stats(
    db: AsyncSession,
    lawyer_id: int,
    today: datetime,
) -> LawyerConsultationStats:
    total = await db.scalar(
        select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.lawyer_id == int(lawyer_id)
        )
    )
    pending = await db.scalar(
        select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.lawyer_id == int(lawyer_id),
            LawyerConsultation.status == "pending",
        )
    )
    confirmed = await db.scalar(
        select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.lawyer_id == int(lawyer_id),
            LawyerConsultation.status == "confirmed",
        )
    )
    completed = await db.scalar(
        select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.lawyer_id == int(lawyer_id),
            LawyerConsultation.status == "completed",
        )
    )
    cancelled = await db.scalar(
        select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.lawyer_id == int(lawyer_id),
            LawyerConsultation.status == "cancelled",
        )
    )
    today_count = await db.scalar(
        select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.lawyer_id == int(lawyer_id),
            LawyerConsultation.created_at >= today,
        )
    )
    return LawyerConsultationStats(
        total=int(total or 0),
        pending=int(pending or 0),
        confirmed=int(confirmed or 0),
        completed=int(completed or 0),
        cancelled=int(cancelled or 0),
        today_count=int(today_count or 0),
    )


async def _get_review_stats(db: AsyncSession,
                            lawyer_id: int) -> LawyerReviewStats:
    total_reviews = await db.scalar(
        select(func.count(LawyerReview.id)).where(
            LawyerReview.lawyer_id == int(lawyer_id))
    )
    avg_rating = await db.scalar(
        select(func.avg(LawyerReview.rating)).where(
            LawyerReview.lawyer_id == int(lawyer_id))
    )
    rating_counts = {}
    for rating in range(1, 6):
        count = await db.scalar(
            select(func.count(LawyerReview.id)).where(
                LawyerReview.lawyer_id == int(lawyer_id),
                LawyerReview.rating == rating,
            )
        )
        rating_counts[rating] = int(count or 0)
    return LawyerReviewStats(
        total_reviews=int(total_reviews or 0),
        average_rating=round(float(avg_rating or 0.0), 1),
        rating_5_count=rating_counts[5],
        rating_4_count=rating_counts[4],
        rating_3_count=rating_counts[3],
        rating_2_count=rating_counts[2],
        rating_1_count=rating_counts[1],
    )


async def _require_verified_lawyer(db: AsyncSession, current_user: User):
    """获取当前用户的律师信息"""
    from ...models.lawfirm import Lawyer
    from sqlalchemy import select

    res = await db.execute(
        select(Lawyer).where(
            Lawyer.user_id == int(current_user.id),
            Lawyer.is_active,
        )
    )
    lawyer = res.scalar_one_or_none()
    if not lawyer:
        raise HTTPException(status_code=403, detail="未绑定律师资料")
    return lawyer


@router.get("/dashboard", response_model=LawyerDashboardResponse,
            summary="律师-数据看板")
async def lawyer_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师数据看板"""
    lawyer = await _require_verified_lawyer(db, current_user)

    # 获取钱包信息
    wallet = await _ensure_wallet(db, int(lawyer.id))

    # 获取待处理提现金额
    pending_withdrawal_result = await db.execute(
        select(func.sum(WithdrawalRequest.amount)).where(
            and_(
                WithdrawalRequest.lawyer_id == int(lawyer.id),
                WithdrawalRequest.status == "pending",
            )
        )
    )
    pending_withdrawal = float(pending_withdrawal_result.scalar() or 0.0)

    wallet_info = LawyerWalletInfo(
        balance=float(wallet.available_amount),
        frozen=float(wallet.frozen_amount),
        total_income=float(wallet.total_income),
        total_withdrawn=float(wallet.withdrawn_amount),
        pending_withdrawal=pending_withdrawal,
    )

    # 获取咨询统计
    today = datetime.now(
        timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0)
    consultation_stats = await _get_consultation_stats(db, int(lawyer.id), today)

    # 评价统计
    review_stats = await _get_review_stats(db, int(lawyer.id))

    recent_consultations_result = await db.execute(
        select(LawyerConsultation)
        .where(LawyerConsultation.lawyer_id == int(lawyer.id))
        .order_by(LawyerConsultation.created_at.desc())
        .limit(5)
    )
    recent_consultations = [
        _serialize_consultation(c, lawyer.name)
        for c in recent_consultations_result.scalars().all()
    ]

    recent_reviews_result = await db.execute(
        select(LawyerReview)
        .where(LawyerReview.lawyer_id == int(lawyer.id))
        .order_by(LawyerReview.created_at.desc())
        .limit(5)
    )
    recent_reviews = [_serialize_review(
        r) for r in recent_reviews_result.scalars().all()]

    unread_notifications = await _get_unread_notifications(db, int(current_user.id))

    return LawyerDashboardResponse(
        wallet=wallet_info,
        consultation_stats=consultation_stats,
        review_stats=review_stats,
        recent_consultations=recent_consultations,
        recent_reviews=recent_reviews,
        unread_notifications=unread_notifications,
    )


@router.get("/workbench", response_model=LawyerWorkbenchResponse,
            summary="律师-工作台")
async def lawyer_workbench(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师工作台"""
    lawyer = await _require_verified_lawyer(db, current_user)

    wallet = await _ensure_wallet(db, int(lawyer.id))

    pending_withdrawal_result = await db.execute(
        select(func.sum(WithdrawalRequest.amount)).where(
            and_(
                WithdrawalRequest.lawyer_id == int(lawyer.id),
                WithdrawalRequest.status == "pending",
            )
        )
    )
    pending_withdrawal_amount = float(
        pending_withdrawal_result.scalar() or 0.0)
    pending_withdrawals = await db.scalar(
        select(func.count(WithdrawalRequest.id)).where(
            WithdrawalRequest.lawyer_id == int(lawyer.id),
            WithdrawalRequest.status == "pending",
        )
    )

    wallet_info = LawyerWalletInfo(
        balance=float(wallet.available_amount),
        frozen=float(wallet.frozen_amount),
        total_income=float(wallet.total_income),
        total_withdrawn=float(wallet.withdrawn_amount),
        pending_withdrawal=pending_withdrawal_amount,
    )

    # 待处理咨询
    pending_res = await db.execute(
        select(LawyerConsultation)
        .where(
            LawyerConsultation.lawyer_id == int(lawyer.id),
            LawyerConsultation.status == "pending",
        )
        .order_by(LawyerConsultation.created_at.desc())
        .limit(5)
    )
    pending_consultations = [
        _serialize_consultation(c, lawyer.name)
        for c in pending_res.scalars().all()
    ]

    # 今日统计
    today = datetime.now(
        timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0)
    today_stats = await _get_consultation_stats(db, int(lawyer.id), today)

    recent_reviews_result = await db.execute(
        select(LawyerReview)
        .where(LawyerReview.lawyer_id == int(lawyer.id))
        .order_by(LawyerReview.created_at.desc())
        .limit(5)
    )
    recent_reviews = [_serialize_review(
        r) for r in recent_reviews_result.scalars().all()]

    unread_notifications = await _get_unread_notifications(db, int(current_user.id))

    return LawyerWorkbenchResponse(
        wallet=wallet_info,
        pending_consultations=pending_consultations,
        pending_withdrawals=int(pending_withdrawals or 0),
        pending_withdrawal_amount=pending_withdrawal_amount,
        recent_reviews=recent_reviews,
        unread_notifications=unread_notifications,
        today_stats=today_stats,
    )


@router.get("/income-trend", response_model=IncomeTrendResponse,
            summary="律师-收入趋势")
async def get_income_trend(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = 30,
):
    """获取收入趋势"""
    lawyer = await _require_verified_lawyer(db, current_user)

    start_date = datetime.now(timezone.utc) - timedelta(days=int(days))
    result = await db.execute(
        select(
            func.date(LawyerIncomeRecord.created_at).label("date"),
            func.sum(LawyerIncomeRecord.lawyer_income).label("income"),
        )
        .where(
            LawyerIncomeRecord.lawyer_id == int(lawyer.id),
            LawyerIncomeRecord.created_at >= start_date,
        )
        .group_by(func.date(LawyerIncomeRecord.created_at))
        .order_by(func.date(LawyerIncomeRecord.created_at))
    )

    trend = []
    total_income = 0.0
    for row in result.all():
        date_value = row.date
        date_str = date_value.isoformat() if hasattr(
            date_value, "isoformat") else str(date_value)
        income = float(row.income or 0.0)
        total_income += income
        trend.append({"date": date_str, "income": income})

    return {
        "lawyer_id": int(lawyer.id),
        "days": int(days),
        "trend": trend,
        "total_income": round(total_income, 2),
    }


@router.get("/consultation-stats",
            response_model=ConsultationStatsResponse, summary="律师-咨询统计")
async def get_consultation_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取咨询统计"""
    lawyer = await _require_verified_lawyer(db, current_user)

    total = await db.scalar(
        select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.lawyer_id == int(lawyer.id))
    )
    completed = await db.scalar(
        select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.lawyer_id == int(lawyer.id),
            LawyerConsultation.status == "completed",
        )
    )
    cancelled = await db.scalar(
        select(func.count(LawyerConsultation.id)).where(
            LawyerConsultation.lawyer_id == int(lawyer.id),
            LawyerConsultation.status == "cancelled",
        )
    )

    completed_rows = await db.execute(
        select(LawyerConsultation.created_at, LawyerConsultation.updated_at).where(
            LawyerConsultation.lawyer_id == int(lawyer.id),
            LawyerConsultation.status == "completed",
            LawyerConsultation.updated_at.is_not(None),
        )
    )
    durations = []
    for created_at, updated_at in completed_rows.all():
        if created_at and updated_at:
            durations.append((updated_at - created_at).total_seconds() / 60)
    avg_response_minutes = round(
        sum(durations) / len(durations),
        1) if durations else 0.0

    total_count = int(total or 0)
    completed_count = int(completed or 0)
    cancelled_count = int(cancelled or 0)
    completion_rate = round(
        completed_count / total_count * 100,
        1) if total_count else 0.0

    return {
        "lawyer_id": int(lawyer.id),
        "total": total_count,
        "completed": completed_count,
        "cancelled": cancelled_count,
        "completion_rate": completion_rate,
        "avg_response_minutes": avg_response_minutes,
    }


@router.get("/performance",
            response_model=LawyerPerformanceResponse, summary="律师-绩效分析")
async def get_performance(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取绩效分析"""
    lawyer = await _require_verified_lawyer(db, current_user)
    return await lawyer_stats_service.get_lawyer_performance(db, int(lawyer.id))


@router.post("/consultations/{consultation_id}/accept", summary="律师-接受咨询")
async def accept_consultation(
    consultation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师接受咨询预约"""
    lawyer = await _require_verified_lawyer(db, current_user)

    # 获取咨询
    result = await db.execute(
        select(LawyerConsultation).where(
            LawyerConsultation.id == consultation_id)
    )
    consultation = result.scalar_one_or_none()
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询不存在")

    if consultation.lawyer_id != lawyer.id:
        raise HTTPException(status_code=403, detail="无权操作")

    if consultation.status not in ["pending", "confirmed"]:
        raise HTTPException(status_code=400, detail="咨询状态不允许接受")

    # 更新状态为confirmed（已确认）
    consultation.status = "confirmed"

    # 发送通知给用户
    if consultation.user_id:
        notification = Notification(
            user_id=int(consultation.user_id),
            type=NotificationType.SYSTEM,
            title="咨询已被接受",
            content=f"您的咨询 '{consultation.subject}' 已被律师接受。",
            link=f"/user/consultations/{consultation.id}",
            is_read=False,
        )
        db.add(notification)
        await db.commit()  # 提交以获取 notification ID
        await db.refresh(notification)  # 刷新以获取 ID

        # WebSocket 推送（统一 notification payload）
        from ...services.unified_notification_service import unified_notification_service
        await unified_notification_service.notify_ws(
            user_id=int(consultation.user_id),
            title="咨询已被接受",
            content=f"您的咨询 '{consultation.subject}' 已被律师接受。",
            link=f"/user/consultations/{consultation.id}",
            notification_id=int(notification.id),
        )

    await db.commit()
    await db.refresh(consultation)

    # 获取支付订单信息
    order_result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.related_id == consultation.id,
            PaymentOrder.related_type == "lawyer_consultation"
        )
    )
    order = order_result.scalar_one_or_none()

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
    )
