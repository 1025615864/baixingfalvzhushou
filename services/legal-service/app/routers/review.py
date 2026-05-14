"""评价路由"""
import json
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import AsyncSessionLocal
from ..services.review_service import ReviewService
from ..models.review import Review
from ..models.review_appeal import ReviewAppeal
from ..middleware.auth import get_current_user, AuthUser
from ..schemas.response import ApiResponse, PaginatedData

router = APIRouter()


class CreateReviewRequest(BaseModel):
    consultation_id: int
    rating: int
    content: Optional[str] = None
    is_anonymous: bool = False


class ReviewResponse(BaseModel):
    id: int
    consultation_id: int
    lawyer_id: int
    user_id: int
    rating: int
    content: Optional[str] = None
    is_anonymous: bool
    created_at: str

    class Config:
        from_attributes = True


class LawyerStatsResponse(BaseModel):
    lawyer_id: int
    total: int
    avg_rating: float


class AppealRequest(BaseModel):
    reason: str
    evidence: Optional[str] = None


class AppealReviewRequest(BaseModel):
    approved: bool
    reject_reason: Optional[str] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_review(
    body: CreateReviewRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """提交评价 - 需要用户登录"""
    from ..services.consultation_service import ConsultationService

    consultation_service = ConsultationService(db)
    consultation = await consultation_service.get(body.consultation_id)

    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    if consultation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权评价此咨询")

    if consultation.status not in ["answered", "closed"]:
        raise HTTPException(status_code=400, detail="咨询未完成，无法评价")

    service = ReviewService(db)

    existing = await service.get_by_consultation(body.consultation_id)
    if existing:
        raise HTTPException(status_code=400, detail="已提交过评价")

    review = await service.create(
        consultation_id=body.consultation_id,
        lawyer_id=consultation.lawyer_id,
        user_id=current_user.id,
        rating=body.rating,
        content=body.content,
        is_anonymous=body.is_anonymous,
    )
    return ApiResponse.success(ReviewResponse.model_validate(review))


@router.get("/consultation/{consultation_id}")
async def get_review_by_consultation(
    consultation_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取咨询的评价"""
    service = ReviewService(db)
    review = await service.get_by_consultation(consultation_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return ApiResponse.success(ReviewResponse.model_validate(review))


@router.get("/lawyer/{lawyer_id}")
async def get_lawyer_reviews(
    lawyer_id: int,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律师的所有评价"""
    service = ReviewService(db)
    reviews, total = await service.get_by_lawyer(lawyer_id, page, page_size)
    items = [ReviewResponse.model_validate(r) for r in reviews]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.get("/lawyer/{lawyer_id}/stats")
async def get_lawyer_stats(
    lawyer_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律师评分统计"""
    service = ReviewService(db)
    stats = await service.get_lawyer_stats(lawyer_id)
    return ApiResponse.success(LawyerStatsResponse(
        lawyer_id=lawyer_id,
        total=stats["total"],
        avg_rating=stats["avg_rating"],
    ))


@router.get("/lawyer/{lawyer_id}/tags")
async def get_lawyer_review_tags(
    lawyer_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律师评价标签云"""
    result = await db.execute(
        select(Review).where(Review.lawyer_id == lawyer_id)
    )
    reviews = result.scalars().all()

    tag_counter = {}
    for review in reviews:
        if review.tags:
            try:
                tags_list = json.loads(review.tags)
            except (json.JSONDecodeError, TypeError):
                continue
            for tag_line in tags_list:
                if ":" in tag_line:
                    tag, count = tag_line.split(":", 1)
                    tag_counter[tag] = tag_counter.get(tag, 0) + int(count)
                else:
                    tag_counter[tag_line] = tag_counter.get(tag_line, 0) + 1

    sorted_tags = sorted(tag_counter.items(), key=lambda x: x[1], reverse=True)
    tags = [{"tag": t[0], "count": t[1]} for t in sorted_tags]
    return ApiResponse.success({"lawyer_id": lawyer_id, "tags": tags})


@router.post("/{review_id}/appeal")
async def appeal_review(
    review_id: int,
    body: AppealRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """律师对差评发起申诉"""
    review = await db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="评价不存在")
    if review.rating > 2:
        raise HTTPException(status_code=400, detail="仅1-2星评价可申诉")

    from ..services.lawyer_service import LawyerService
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer or lawyer.id != review.lawyer_id:
        raise HTTPException(status_code=403, detail="无权申诉此评价")

    existing = await db.scalar(
        select(ReviewAppeal).where(
            ReviewAppeal.review_id == review_id,
            ReviewAppeal.status == "pending",
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="已有待审核的申诉")

    appeal = ReviewAppeal(
        review_id=review_id,
        lawyer_id=lawyer.id,
        reason=body.reason,
        evidence=body.evidence,
    )
    db.add(appeal)
    await db.commit()
    await db.refresh(appeal)

    return ApiResponse.success({"id": appeal.id, "review_id": review_id, "status": "pending"})


@router.post("/appeal/{appeal_id}/review")
async def review_appeal(
    appeal_id: int,
    body: AppealReviewRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """管理员审核申诉"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限审核")

    appeal = await db.get(ReviewAppeal, appeal_id)
    if not appeal:
        raise HTTPException(status_code=404, detail="申诉不存在")

    appeal.status = "approved" if body.approved else "rejected"
    appeal.admin_note = body.reject_reason
    appeal.reviewed_by = current_user.id
    appeal.reviewed_at = datetime.now()
    await db.commit()

    return ApiResponse.success({
        "appeal_id": appeal_id,
        "status": appeal.status,
        "message": "申诉已处理",
    })
