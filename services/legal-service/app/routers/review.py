"""评价路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.review_service import ReviewService
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
