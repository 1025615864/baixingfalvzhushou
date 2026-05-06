"""会员路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.membership_service import MembershipService, MembershipTier
from ..middleware.auth import get_current_user
from ..models import User

router = APIRouter(prefix="/membership", tags=["会员"])


class MembershipInfoResponse(BaseModel):
    tier: str
    is_vip: bool
    vip_remaining_days: int
    permissions: dict

    class Config:
        from_attributes = True


class UpgradeRequest(BaseModel):
    days: int = 30
    tier: str = MembershipTier.VIP


class UpgradeResponse(BaseModel):
    success: bool
    message: str
    tier: str
    vip_expires_at: Optional[str] = None


@router.get("/info", response_model=MembershipInfoResponse)
async def get_membership_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """获取当前用户会员信息"""
    service = MembershipService(db)
    tier = service.get_tier(current_user)
    is_vip = service.is_vip(current_user)
    remaining_days = service.get_vip_remaining_days(current_user)
    permissions = service.get_permissions(current_user)

    return MembershipInfoResponse(
        tier=tier,
        is_vip=is_vip,
        vip_remaining_days=remaining_days,
        permissions=permissions,
    )


@router.get("/permissions")
async def get_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """获取当前用户权限列表"""
    service = MembershipService(db)
    permissions = service.get_permissions(current_user)
    return {"permissions": permissions}


@router.post("/upgrade", response_model=UpgradeResponse)
async def upgrade_membership(
    request: UpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """升级会员（管理员或内部调用）"""
    if request.tier not in (MembershipTier.VIP, MembershipTier.SVIP):
        raise HTTPException(status_code=400, detail="Invalid tier")

    if request.days <= 0 or request.days > 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")

    service = MembershipService(db)
    success = await service.upgrade_to_vip(
        user_id=current_user.id,
        days=request.days,
        tier=request.tier,
    )

    if not success:
        raise HTTPException(status_code=500, detail="Upgrade failed")

    user = await db.get(User, current_user.id)
    return UpgradeResponse(
        success=True,
        message=f"Successfully upgraded to {request.tier}",
        tier=request.tier,
        vip_expires_at=user.vip_expires_at.isoformat() if user.vip_expires_at else None,
    )


@router.post("/cancel", response_model=UpgradeResponse)
async def cancel_membership(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """取消会员资格"""
    service = MembershipService(db)
    success = await service.cancel_vip(current_user.id)

    if not success:
        raise HTTPException(status_code=500, detail="Cancellation failed")

    return UpgradeResponse(
        success=True,
        message="Membership cancelled",
        tier=MembershipTier.FREE,
    )


@router.get("/check/{permission}")
async def check_permission(
    permission: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """检查是否有特定权限"""
    service = MembershipService(db)
    has_permission = await service.check_permission(current_user.id, permission)
    return {
        "permission": permission,
        "allowed": has_permission,
    }
