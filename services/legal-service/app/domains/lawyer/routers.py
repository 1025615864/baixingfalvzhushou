"""律师领域路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...schemas import LawyerResponse
from ...services import LawyerService
from ...middleware.auth import require_permissions
from ...shared.permissions import Permission

router = APIRouter(prefix="/lawyers", tags=["律师"])


@router.get("/")
async def list_lawyers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    specialty: str = None,
    city: str = None,
    min_rating: float = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.LAWYER_READ)),
):
    service = LawyerService(db)
    lawyers, total = await service.list_lawyers(
        page=page,
        page_size=page_size,
        specialty=specialty,
        city=city,
        min_rating=min_rating,
    )
    return {
        "items": [LawyerResponse.model_validate(l) for l in lawyers],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/search")
async def search_lawyers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    specialty: str = None,
    city: str = None,
    min_rating: float = None,
    available: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.LAWYER_READ)),
):
    service = LawyerService(db)
    lawyers, total = await service.search_lawyers(
        specialty=specialty,
        city=city,
        min_rating=min_rating,
        available=available,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [LawyerResponse.model_validate(l) for l in lawyers],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{lawyer_id}", response_model=LawyerResponse)
async def get_lawyer(
    lawyer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.LAWYER_READ)),
):
    service = LawyerService(db)
    lawyer = await service.get_lawyer(lawyer_id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")
    return LawyerResponse.model_validate(lawyer)


@router.patch("/{lawyer_id}/profile")
async def update_lawyer_profile(
    lawyer_id: int,
    profile_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.LAWYER_UPDATE)),
):
    service = LawyerService(db)
    lawyer = await service.update_profile(lawyer_id, profile_data)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")
    return {"message": "资料更新成功"}


@router.post("/{lawyer_id}/verify")
async def verify_lawyer(
    lawyer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.LAWYER_VERIFY)),
):
    service = LawyerService(db)
    result = await service.verify(lawyer_id)
    return result