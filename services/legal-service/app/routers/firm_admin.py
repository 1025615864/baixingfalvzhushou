"""平台律所管理路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.firm_service import FirmService
from ..services.firm_admin_service import FirmAdminService
from ..middleware.auth import get_admin_user, AuthUser
from ..schemas.response import ApiResponse, PaginatedData

router = APIRouter()


class FirmAdminApprovalRequest(BaseModel):
    action: str  # "approve" or "reject"
    reason: Optional[str] = None


class PlatformFirmResponse(BaseModel):
    id: int
    user_id: int
    name: str
    license_no: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    status: str
    lawyer_count: int = 0
    created_at: str

    class Config:
        from_attributes = True


class FirmStatsResponse(BaseModel):
    lawyer_count: int
    consultation_count: int
    active_consultations: int
    total_revenue: float

    class Config:
        from_attributes = True


def require_platform_firm_admin(current_user: AuthUser) -> AuthUser:
    """验证平台律所管理员权限"""
    if current_user.role not in ["admin", "platform_firm_admin"]:
        raise HTTPException(status_code=403, detail="需要平台律所管理员权限")
    return current_user


@router.get("/firms")
async def list_all_firms(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    province: Optional[str] = None,
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取所有律所列表 - 平台管理员"""
    require_platform_firm_admin(current_user)

    service = FirmService(db)
    firms, total = await service.list_firms(page, page_size, province, status=status)

    items = [
        {
            "id": f.id,
            "user_id": f.user_id,
            "name": f.name,
            "license_no": f.license_no,
            "province": f.province,
            "city": f.city,
            "status": f.status,
            "lawyer_count": f.lawyer_count,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in firms
    ]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.get("/firms/pending")
async def list_pending_firms(
    page: int = 1,
    page_size: int = 20,
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取待审核律所列表"""
    require_platform_firm_admin(current_user)

    service = FirmService(db)
    firms, total = await service.list_firms(page, page_size, status="pending")

    items = [
        {
            "id": f.id,
            "user_id": f.user_id,
            "name": f.name,
            "province": f.province,
            "city": f.city,
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in firms
    ]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.get("/firms/reviewing")
async def list_reviewing_firms(
    page: int = 1,
    page_size: int = 20,
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取审核中的律所列表"""
    require_platform_firm_admin(current_user)

    service = FirmService(db)
    firms, total = await service.list_firms(page, page_size, status="reviewing")

    items = [
        {
            "id": f.id,
            "user_id": f.user_id,
            "name": f.name,
            "province": f.province,
            "city": f.city,
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in firms
    ]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.post("/firms/{firm_id}/approve")
async def approve_firm(
    firm_id: int,
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """审核通过律所"""
    require_platform_firm_admin(current_user)

    service = FirmService(db)

    try:
        firm = await service.approve_firm(firm_id, current_user.id)
        return ApiResponse.success({
            "id": firm.id,
            "name": firm.name,
            "status": firm.status,
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/firms/{firm_id}/reject")
async def reject_firm(
    firm_id: int,
    reason: str = Query(..., description="拒绝原因"),
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """审核拒绝律所"""
    require_platform_firm_admin(current_user)

    service = FirmService(db)

    try:
        firm = await service.reject_firm(firm_id, current_user.id, reason)
        return ApiResponse.success({
            "id": firm.id,
            "name": firm.name,
            "status": firm.status,
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/firms/{firm_id}/stats")
async def get_firm_stats(
    firm_id: int,
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律所统计信息"""
    require_platform_firm_admin(current_user)

    service = FirmService(db)
    firm = await service.get_firm(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="律所不存在")

    admin_service = FirmAdminService(db)
    stats = await admin_service.get_firm_stats(firm_id)

    return ApiResponse.success(stats)


@router.get("/firms/{firm_id}/lawyer-stats")
async def get_firm_lawyer_stats(
    firm_id: int,
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律所律师统计"""
    require_platform_firm_admin(current_user)

    service = FirmService(db)
    firm = await service.get_firm(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="律所不存在")

    admin_service = FirmAdminService(db)
    stats = await admin_service.get_lawyer_stats(firm_id)

    return ApiResponse.success({"items": stats, "total": len(stats)})