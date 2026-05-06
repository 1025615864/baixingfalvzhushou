"""评价领域路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...schemas import ReviewResponse, ReviewCreate
from ...services import ReviewService
from ...middleware.auth import require_permissions
from ...shared.permissions import Permission

router = APIRouter(prefix="/reviews", tags=["评价"])


@router.post("/", response_model=ReviewResponse)
async def create_review(
    request: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.REVIEW_CREATE)),
):
    service = ReviewService(db)
    review = await service.create(
        consultation_id=request.consultation_id,
        lawyer_id=request.lawyer_id,
        user_id=current_user.id,
        rating=request.rating,
        content=request.content,
        is_anonymous=request.is_anonymous,
    )
    return ReviewResponse.model_validate(review)


@router.get("/consultation/{consultation_id}", response_model=ReviewResponse)
async def get_review_by_consultation(
    consultation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.REVIEW_READ)),
):
    service = ReviewService(db)
    review = await service.get_by_consultation(consultation_id)
    if not review:
        return None
    return ReviewResponse.model_validate(review)


@router.get("/lawyer/{lawyer_id}")
async def get_lawyer_reviews(
    lawyer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.REVIEW_READ)),
):
    service = ReviewService(db)
    reviews, total = await service.get_by_lawyer(
        lawyer_id=lawyer_id,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [ReviewResponse.model_validate(r) for r in reviews],
        "total": total,
        "page": page,
        "page_size": page_size,
    }