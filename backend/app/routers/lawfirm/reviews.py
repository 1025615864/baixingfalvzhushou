"""评价系统路由"""

import json
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.lawfirm import LawyerReview
from ...models.user import User
from ...schemas.lawfirm import (
    ReviewCreate, ReviewResponse, ReviewListResponse, ReviewSummaryResponse,
)
from ...services.lawfirm_service import lawyer_service, review_service
from ...utils.deps import get_current_user

router = APIRouter(prefix="/reviews", tags=["评价系统"])


async def _get_owned_consultation(
        db: AsyncSession, consultation_id: int, user_id: int):
    """获取用户拥有的咨询"""
    from ...models.lawfirm import LawyerConsultation
    from sqlalchemy.orm import selectinload

    res = await db.execute(
        select(LawyerConsultation)
        .options(selectinload(LawyerConsultation.lawyer))
        .where(
            LawyerConsultation.id == int(consultation_id),
            LawyerConsultation.user_id == int(user_id),
        )
    )
    return res.scalar_one_or_none()


@router.post("", response_model=ReviewResponse, summary="提交评价")
async def create_review(
    data: ReviewCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """提交律师评价"""
    # 检查律师是否存在
    lawyer = await lawyer_service.get_by_id(db, data.lawyer_id)
    if not lawyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="律师不存在")

    if data.consultation_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须指定咨询ID")

    consultation = await _get_owned_consultation(db, int(data.consultation_id), int(current_user.id))
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="咨询不存在")

    if int(consultation.lawyer_id) != int(data.lawyer_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="咨询与律师不匹配")

    if str(consultation.status).lower() != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅已完成咨询可评价")

    # 检查是否已评价
    existing = await db.execute(
        select(LawyerReview).where(
            LawyerReview.user_id == int(current_user.id),
            LawyerReview.consultation_id == int(data.consultation_id),
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该咨询已评价")

    # 处理标签
    tags_json = json.dumps(data.tags) if data.tags else None

    review = LawyerReview(
        lawyer_id=int(data.lawyer_id),
        user_id=int(current_user.id),
        consultation_id=int(data.consultation_id),
        rating=int(data.rating),
        content=data.content,
        is_anonymous=data.is_anonymous,
        professionalism=data.professionalism,
        responsiveness=data.responsiveness,
        attitude=data.attitude,
        tags=tags_json,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    # 解析标签
    tags_list = json.loads(review.tags) if review.tags else []

    return ReviewResponse(
        id=review.id,
        lawyer_id=review.lawyer_id,
        user_id=review.user_id,
        consultation_id=review.consultation_id,
        rating=review.rating,
        content=review.content,
        is_anonymous=review.is_anonymous,
        professionalism=review.professionalism,
        responsiveness=review.responsiveness,
        attitude=review.attitude,
        tags=tags_list,
        created_at=review.created_at,
    )


@router.get("/lawyers/{lawyer_id}",
            response_model=ReviewListResponse, summary="获取律师评价")
async def get_lawyer_reviews(
    lawyer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
):
    """获取律师的评价列表"""
    reviews, total = await review_service.get_by_lawyer(db, lawyer_id, page, page_size)

    # 计算平均评分
    avg_rating = 0.0
    if reviews:
        total_rating = sum(r.rating for r in reviews)
        avg_rating = total_rating / len(reviews)

    items = []
    for r in reviews:
        items.append(ReviewResponse(
            id=r.id,
            lawyer_id=r.lawyer_id,
            user_id=r.user_id,
            consultation_id=r.consultation_id,
            rating=r.rating,
            content=r.content,
            is_anonymous=r.is_anonymous,
            professionalism=r.professionalism,
            responsiveness=r.responsiveness,
            attitude=r.attitude,
            tags=json.loads(r.tags) if r.tags else [],
            created_at=r.created_at,
        ))

    return ReviewListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        average_rating=avg_rating)


@router.get("/lawyers/{lawyer_id}/summary",
            response_model=ReviewSummaryResponse, summary="获取律师评价摘要")
async def get_lawyer_review_summary(
        lawyer_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    """获取律师评价摘要"""
    lawyer = await lawyer_service.get_by_id(db, lawyer_id)
    if not lawyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="律师不存在")

    stats = await review_service.get_summary(db, lawyer_id)

    return ReviewSummaryResponse(
        lawyer_id=lawyer_id,
        lawyer_name=lawyer.name,
        total_reviews=stats["total"],
        average_rating=stats["avg_rating"],
        rating_distribution=stats["distribution"],
        tag_stats=stats["tag_stats"],
        dimension_stats=stats["dimension_stats"],
        popular_tags=stats["tag_stats"],
    )
