"""律师路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import Lawyer
from ..services.lawyer_service import LawyerService
from ..middleware.auth import get_current_user, get_current_lawyer, get_admin_user, AuthUser
from ..schemas.response import ApiResponse, PaginatedData

router = APIRouter()


class LawyerResponse(BaseModel):
    id: int
    user_id: int
    name: str
    title: Optional[str] = None
    specialties: list
    bio: Optional[str] = None
    rating: float
    consultation_count: int
    status: str

    class Config:
        from_attributes = True


class LawyerListResponse(BaseModel):
    items: list[LawyerResponse]
    total: int
    page: int
    page_size: int


class LawyerProfileUpdateRequest(BaseModel):
    title: Optional[str] = None
    specialties: Optional[list] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    price_range: Optional[str] = None
    avatar: Optional[str] = None


@router.get("/")
async def list_lawyers(
    page: int = 1,
    page_size: int = 20,
    specialty: Optional[str] = None,
    city: Optional[str] = None,
    min_rating: Optional[float] = None,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律师列表 - 公开接口"""
    service = LawyerService(db)
    lawyers, total = await service.list_lawyers(page, page_size, specialty, city, min_rating)
    items = [LawyerResponse.model_validate(l) for l in lawyers]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.get("/search")
async def search_lawyers(
    specialty: Optional[str] = None,
    city: Optional[str] = None,
    min_rating: Optional[float] = None,
    available: Optional[bool] = True,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """搜索律师 - 公开接口"""
    service = LawyerService(db)
    lawyers, total = await service.search_lawyers(
        specialty=specialty,
        city=city,
        min_rating=min_rating,
        available=available,
        page=page,
        page_size=page_size
    )
    items = [LawyerResponse.model_validate(l) for l in lawyers]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.get("/{lawyer_id}")
async def get_lawyer(
    lawyer_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律师详情 - 公开接口"""
    service = LawyerService(db)
    lawyer = await service.get_lawyer(lawyer_id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    return ApiResponse.success(LawyerResponse.model_validate(lawyer))


@router.patch("/me/profile")
async def update_my_profile(
    body: LawyerProfileUpdateRequest,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """更新当前律师的个人资料"""
    service = LawyerService(db)
    lawyer = await service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")
    updated = await service.update_profile(lawyer.id, body.dict(exclude_unset=True))
    return ApiResponse.success(LawyerResponse.model_validate(updated))


@router.get("/me/consultations")
async def get_my_consultations(
    page: int = 1,
    page_size: int = 20,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取当前律师的咨询列表"""
    service = LawyerService(db)
    lawyer = await service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")
    from ..services.consultation_service import ConsultationService
    consultation_service = ConsultationService(db)
    consultations, total = await consultation_service.list_by_lawyer(lawyer.id, page, page_size)
    items = [{"id": c.id, "user_id": c.user_id, "category": c.category,
               "title": c.title, "status": c.status} for c in consultations]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.post("/{lawyer_id}/verify")
async def verify_lawyer(
    lawyer_id: int,
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """认证律师 - 需要管理员权限"""
    service = LawyerService(db)
    result = await service.verify(lawyer_id)
    return ApiResponse.success(result)


@router.get("/me/pending")
async def get_my_pending_consultations(
    page: int = 1,
    page_size: int = 20,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取当前律师的待处理咨询列表"""
    service = LawyerService(db)
    lawyer = await service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")
    from ..services.consultation_service import ConsultationService
    consultation_service = ConsultationService(db)
    consultations, total = await consultation_service.list_by_lawyer(lawyer.id, page, page_size)
    pending = [c for c in consultations if c.status in ["pending", "processing"]]
    items = [{"id": c.id, "user_id": c.user_id, "category": c.category,
               "title": c.title, "status": c.status, "created_at": c.created_at.isoformat() if c.created_at else None} for c in pending]
    paginated = PaginatedData.create(items, len(pending), page, page_size)
    return ApiResponse.success(paginated)


@router.get("/me/stats")
async def get_my_lawyer_stats(
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取当前律师的统计信息"""
    service = LawyerService(db)
    lawyer = await service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    from ..services.consultation_service import ConsultationService
    consultation_service = ConsultationService(db)
    stats = await consultation_service.get_stats(lawyer.id)

    return ApiResponse.success({
        "lawyer_id": lawyer.id,
        "total_consultations": stats["total"],
        "pending_consultations": stats["pending"],
        "processing_consultations": stats["processing"],
        "answered_consultations": stats["answered"],
        "avg_rating": lawyer.rating,
        "rating_count": lawyer.rating_count,
        "response_time": lawyer.response_time or 0,
    })


@router.get("/me/schedule")
async def get_my_schedule(
    year: int,
    month: int,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取当前律师的排班"""
    from ..services.schedule_service import ScheduleService
    service = ScheduleService(db)
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    schedules = await service.get_by_lawyer_month(lawyer.id, year, month)
    items = [
        {
            "id": s.id,
            "date": s.date.isoformat() if s.date else None,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "is_available": s.is_available,
        }
        for s in schedules
    ]
    return ApiResponse.success({"items": items, "total": len(schedules)})


@router.get("/recommended")
async def get_recommended_lawyers(
    user_id: Optional[int] = None,
    limit: int = 5,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取推荐律师列表 - 基于智能匹配"""
    from ..services.matching_service import MatchingService
    matching_service = MatchingService(db)

    if user_id:
        recommended = await matching_service.get_recommended_lawyers(user_id, limit)
    else:
        recommended = await matching_service.match_by_specialty("婚姻继承", limit=limit)

    return ApiResponse.success({"items": recommended, "total": len(recommended)})


@router.get("/matching/{consultation_id}")
async def match_lawyers_for_consultation(
    consultation_id: int,
    limit: int = 5,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """为特定咨询匹配律师"""
    from ..services.matching_service import MatchingService
    matching_service = MatchingService(db)
    matched = await matching_service.match_for_consultation(consultation_id, limit)
    return ApiResponse.success({"items": matched, "total": len(matched)})
