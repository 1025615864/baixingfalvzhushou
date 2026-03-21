"""律师路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import Lawyer
from ..services.lawyer_service import LawyerService

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


@router.get("/", response_model=LawyerListResponse)
async def list_lawyers(
    page: int = 1,
    page_size: int = 20,
    specialty: Optional[str] = None,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律师列表"""
    service = LawyerService(db)
    lawyers, total = await service.list_lawyers(page, page_size, specialty)
    return LawyerListResponse(
        items=[LawyerResponse.model_validate(l) for l in lawyers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{lawyer_id}", response_model=LawyerResponse)
async def get_lawyer(
    lawyer_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律师详情"""
    service = LawyerService(db)
    lawyer = await service.get_lawyer(lawyer_id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    return LawyerResponse.model_validate(lawyer)


@router.post("/{lawyer_id}/verify")
async def verify_lawyer(
    lawyer_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """认证律师"""
    service = LawyerService(db)
    result = await service.verify(lawyer_id)
    return result
