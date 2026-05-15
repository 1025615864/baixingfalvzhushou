"""会员路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from ..database import AsyncSessionLocal
from ..services.membership_service import MembershipService, MembershipTier
from ..middleware.auth import get_current_user
from ..models import User

router = APIRouter(prefix="/membership", tags=["会员"])

# ==================== 价格配置 ====================

PRICING_PLANS = [
    {"tier": "monthly", "name": "月度会员", "monthly_price": 29, "annual_price": 299, "annual_discount": 0.14, "lifetime_price": 999, "savings_annual": 49},
    {"tier": "annual", "name": "年度会员", "monthly_price": 25, "annual_price": 299, "annual_discount": 0.14, "lifetime_price": 999, "savings_annual": 49},
    {"tier": "lifetime", "name": "终身会员", "monthly_price": 999, "annual_price": 999, "annual_discount": 0.0, "lifetime_price": 999, "savings_annual": 0},
]

TIER_BENEFITS = {
    "free": {
        "tier": "free", "tier_name": "免费用户",
        "benefits": [
            {"name": "AI咨询每日3次", "description": "每日3次AI法律咨询", "icon": "robot"},
            {"name": "文书模板5套", "description": "免费下载5套法律文书", "icon": "document"},
        ],
        "features": {"ai_consultation_limit": 3, "document_templates": 5, "lawyer_discount": 0, "priority_support": False, "custom_reports": False},
    },
    "monthly": {
        "tier": "monthly", "tier_name": "月度会员",
        "benefits": [
            {"name": "AI咨询每日10次", "description": "每日10次AI法律咨询", "icon": "robot"},
            {"name": "律师服务9折", "description": "所有律师服务享9折", "icon": "discount"},
            {"name": "文书模板15套", "description": "免费下载15套法律文书", "icon": "document"},
            {"name": "专属客服", "description": "工作日专属客服优先响应", "icon": "support"},
        ],
        "features": {"ai_consultation_limit": 10, "document_templates": 15, "lawyer_discount": 10, "priority_support": True, "custom_reports": False},
    },
    "annual": {
        "tier": "annual", "tier_name": "年度会员",
        "benefits": [
            {"name": "AI咨询无限次", "description": "无限次AI法律咨询", "icon": "robot"},
            {"name": "律师服务8折", "description": "所有律师服务享8折", "icon": "discount"},
            {"name": "文书模板50套", "description": "免费下载50套法律文书", "icon": "document"},
            {"name": "VIP专属客服", "description": "7x24小时VIP专属客服", "icon": "support"},
            {"name": "月度法律报告", "description": "每月推送个人法律风险评估报告", "icon": "report"},
        ],
        "features": {"ai_consultation_limit": -1, "document_templates": 50, "lawyer_discount": 20, "priority_support": True, "custom_reports": True},
    },
    "lifetime": {
        "tier": "lifetime", "tier_name": "终身会员",
        "benefits": [
            {"name": "AI咨询无限次", "description": "永久无限次AI法律咨询", "icon": "robot"},
            {"name": "律师服务7折", "description": "所有律师服务享7折优惠", "icon": "discount"},
            {"name": "文书模板全量", "description": "免费下载全部法律文书模板", "icon": "document"},
            {"name": "终身专属管家", "description": "终身专属法律管家服务", "icon": "support"},
            {"name": "年度法律报告", "description": "年度综合法律风险评估", "icon": "report"},
            {"name": "合同审查无限次", "description": "无限次AI合同审查服务", "icon": "contract"},
        ],
        "features": {"ai_consultation_limit": -1, "document_templates": -1, "lawyer_discount": 30, "priority_support": True, "custom_reports": True},
    },
}


def _resolve_tier(user: User) -> str:
    if user.role in ("admin", "super_admin"):
        return "lifetime"
    if not user.vip_expires_at or user.vip_expires_at <= datetime.now(timezone.utc):
        return "free"
    return "annual" if user.role == "svip" else "monthly"


# ==================== Schemas ====================

class MembershipInfoResponse(BaseModel):
    tier: str
    is_vip: bool
    vip_remaining_days: int
    permissions: dict

    class Config:
        from_attributes = True


class MembershipMeResponse(BaseModel):
    user_id: int
    level: str
    level_name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    auto_renew: bool = False
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    benefits: Optional[dict] = None
    is_vip: bool = False


class UpgradeRequest(BaseModel):
    days: int = 30
    tier: str = MembershipTier.VIP


class UpgradeResponse(BaseModel):
    success: bool
    message: str
    tier: str
    vip_expires_at: Optional[str] = None


# ==================== 定价与权益 ====================

@router.get("/pricing")
async def get_pricing():
    """获取会员价格配置"""
    return PRICING_PLANS


@router.get("/benefits")
async def get_all_benefits():
    """获取所有会员等级权益"""
    return list(TIER_BENEFITS.values())


@router.get("/benefits/{tier}")
async def get_tier_benefits(tier: str):
    """获取指定等级权益"""
    if tier not in TIER_BENEFITS:
        raise HTTPException(status_code=404, detail="未知会员等级")
    return TIER_BENEFITS[tier]


# ==================== 用户会员信息 ====================

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


@router.get("/me", response_model=MembershipMeResponse)
async def get_my_membership_detail(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """获取当前用户会员详细信息"""
    service = MembershipService(db)
    tier = service.get_tier(current_user)
    is_vip = service.is_vip(current_user)
    remaining_days = service.get_vip_remaining_days(current_user)

    user_tier = _resolve_tier(current_user)
    benefits_data = TIER_BENEFITS.get(user_tier, TIER_BENEFITS["free"])

    level_names = {"free": "免费用户", "monthly": "月度会员", "annual": "年度会员", "lifetime": "终身会员"}

    return MembershipMeResponse(
        user_id=current_user.id,
        level=user_tier,
        level_name=level_names.get(user_tier, "免费用户"),
        start_date=current_user.created_at.isoformat() if current_user.created_at else None,
        end_date=current_user.vip_expires_at.isoformat() if current_user.vip_expires_at else None,
        auto_renew=False,
        is_active=is_vip or user_tier == "lifetime",
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
        updated_at=current_user.updated_at.isoformat() if current_user.updated_at else None,
        benefits=benefits_data,
        is_vip=is_vip,
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


# ==================== 升级与取消 ====================

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
