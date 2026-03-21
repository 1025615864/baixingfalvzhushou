"""律所路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import LawFirm
from ..services.firm_service import FirmService

router = APIRouter()


class FirmResponse(BaseModel):
    id: int
    name: str
    license_no: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class FirmListResponse(BaseModel):
    items: list[FirmResponse]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=FirmListResponse)
async def list_firms(
    page: int = 1,
    page_size: int = 20,
    province: Optional[str] = None,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律所列表"""
    service = FirmService(db)
    firms, total = await service.list_firms(page, page_size, province)
    return FirmListResponse(
        items=[FirmResponse.model_validate(f) for f in firms],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{firm_id}", response_model=FirmResponse)
async def get_firm(
    firm_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律所详情"""
    service = FirmService(db)
    firm = await service.get_firm(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firm not found")
    return FirmResponse.model_validate(firm)
