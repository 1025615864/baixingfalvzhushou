"""会员体系 API 路由

提供会员权益查询、会员订阅管理、付费转化统计功能。
支持新的会员等级体系：
- 免费用户 (free): 基础功能
- 月度会员 (monthly): ¥29/月
- 年度会员 (annual): ¥299/年 (享8.6折)
- 终身会员 (lifetime): ¥999 (一次购买终身权益)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..utils.deps import get_current_user, require_admin
from ..services.membership_service import (
    membership_service,
    conversion_tracking_service,
    MembershipTier,
)

router = APIRouter(prefix="/membership", tags=["会员体系"])


# ==================== 响应模型 ====================

class MembershipPricingResponse(BaseModel):
    """会员价格响应"""

    tier: str
    name: str
    monthly_price: float
    annual_price: float
    annual_discount: float
    lifetime_price: float
    savings_annual: float


class MembershipBenefitsResponse(BaseModel):
    """会员权益响应"""

    tier: str
    name: str
    daily_ai_chat_limit: int
    unlimited_ai_chat: bool
    video_consultation_discount: float
    free_video_consultations_per_month: int
    priority_support: bool
    points_multiplier: float
    contract_review_per_month: int
    unlimited_contract_review: bool
    lawyer_consultation_discount: float


class UserMembershipDetailResponse(BaseModel):
    """用户会员详细信息响应"""

    user_id: int
    level: str
    level_name: str
    start_date: datetime | None
    end_date: datetime | None
    auto_renew: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    benefits: dict[str, Any] | None
    is_vip: bool


class UserMembershipResponse(BaseModel):
    """用户会员信息响应"""

    tier: str
    is_vip: bool
    benefits: dict[str, Any]
    quota: dict[str, Any]


class CreateOrderRequest(BaseModel):
    """创建订单请求"""

    tier: str
    duration: str
    payment_method: str = "alipay"


class CreateOrderResponse(BaseModel):
    """创建订单响应"""

    order_no: str
    amount: float
    payment_url: str | None = None


class UpgradeRequest(BaseModel):
    """升级会员请求"""

    tier: str
    duration: str


class UpgradeResponse(BaseModel):
    """升级会员响应"""

    success: bool
    order_no: str
    payment_url: str | None = None


class ConversionStatsResponse(BaseModel):
    """转化统计响应"""

    total_conversions: int
    total_amount: float
    conversion_types: dict[str, int]
    period_days: int


class RevenueStatsResponse(BaseModel):
    """收入统计响应"""

    total_revenue: float
    order_count: int
    avg_order_value: float
    by_order_type: dict[str, dict[str, float]]


class ConversionHistoryItem(BaseModel):
    """转化历史项"""

    order_no: str
    order_type: str | None
    amount: float
    paid_at: str | None


class ConversionHistoryResponse(BaseModel):
    """转化历史响应"""

    items: list[ConversionHistoryItem]
    total: int
    page: int
    page_size: int


# ==================== API 端点 ====================

@router.get("/pricing",
            response_model=list[MembershipPricingResponse],
            summary="获取会员价格")
async def list_membership_pricing():
    """列出所有会员等级的价格配置"""
    pricing = membership_service.list_pricing()
    return pricing


@router.get("/benefits",
            response_model=list[MembershipBenefitsResponse],
            summary="获取所有会员权益配置")
async def list_membership_benefits():
    """列出所有会员等级的权益配置"""
    benefits = membership_service.list_benefits()
    return benefits


@router.get("/benefits/{tier}",
            response_model=MembershipBenefitsResponse, summary="获取指定会员等级权益")
async def get_membership_benefits(tier: str):
    """获取指定会员等级的权益配置"""
    benefits = membership_service.get_benefits(tier)
    if not benefits:
        return {
            "tier": tier,
            "name": "未知",
            "daily_ai_chat_limit": 0,
            "unlimited_ai_chat": False,
            "video_consultation_discount": 1.0,
            "free_video_consultations_per_month": 0,
            "priority_support": False,
            "points_multiplier": 1.0,
            "contract_review_per_month": 0,
            "unlimited_contract_review": False,
            "lawyer_consultation_discount": 1.0,
        }
    return benefits


@router.get("/me", response_model=UserMembershipDetailResponse,
            summary="获取当前用户会员信息")
async def get_my_membership(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取当前用户的会员等级和权益详细信息"""
    result = await membership_service.get_user_membership(db, current_user)
    return result


@router.get("/me/benefits", response_model=UserMembershipResponse,
            summary="获取当前用户权益")
async def get_my_membership_benefits(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取当前用户的权益（含配额信息）"""
    result = await membership_service.get_user_benefits(db, current_user)
    return result


@router.post("/upgrade",
            response_model=UpgradeResponse,
            summary="升级会员")
async def upgrade_membership(
    request: UpgradeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """升级会员订阅"""
    # 计算价格
    amount = await membership_service.calculate_price(request.tier, request.duration)

    if amount <= 0 and request.tier != MembershipTier.FREE.value:
        return {
            "success": False,
            "order_no": "",
            "payment_url": None,
        }

    # 创建会员记录
    membership = await membership_service.create_membership(
        db, int(current_user.id), request.tier, request.duration
    )

    # TODO: 创建支付订单（后续集成支付系统）
    order_no = f"MEM{int(current_user.id)}{int(datetime.now(timezone.utc).timestamp())}"

    return {
        "success": True,
        "order_no": order_no,
        "payment_url": None,  # TODO: 集成支付跳转链接
    }


@router.post("/orders",
            response_model=CreateOrderResponse,
            summary="创建会员订单")
async def create_membership_order(
    request: CreateOrderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """创建会员订单"""
    # 验证会员等级
    if request.tier not in [t.value for t in MembershipTier]:
        request.tier = MembershipTier.MONTHLY.value

    if request.duration not in ["monthly", "annual", "lifetime"]:
        request.duration = "monthly"

    # 计算价格
    amount = await membership_service.calculate_price(request.tier, request.duration)

    # 生成订单号
    order_no = f"MEM{int(current_user.id)}{int(datetime.now(timezone.utc).timestamp())}"

    return {
        "order_no": order_no,
        "amount": amount,
        "payment_url": None,  # TODO: 集成支付跳转链接
    }


@router.get("/orders",
            summary="获取会员订单列表")
async def get_membership_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(ge=1, default=1),
    page_size: int = Query(ge=1, le=100, default=20),
):
    """获取当前用户的会员订单列表"""
    # TODO: 查询支付订单表获取会员相关订单
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats/conversions",
            response_model=ConversionStatsResponse, summary="获取转化统计")
async def get_conversion_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(ge=1, le=365, default=30),
):
    """获取当前用户的转化统计"""
    stats = await conversion_tracking_service.get_conversion_stats(db, int(current_user.id), days)
    return stats


@router.get("/stats/revenue", response_model=RevenueStatsResponse,
            summary="获取收入统计（管理员）")
async def get_revenue_stats(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """获取收入统计（需要管理员权限）"""
    stats = await conversion_tracking_service.get_revenue_stats(db, start_date, end_date)
    return stats


@router.get("/history", response_model=ConversionHistoryResponse,
            summary="获取用户转化历史")
async def get_conversion_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(ge=1, default=1),
    page_size: int = Query(ge=1, le=100, default=20),
):
    """获取当前用户的付费转化历史"""
    history = await conversion_tracking_service.get_user_conversion_history(
        db, int(current_user.id), page, page_size
    )
    return history


@router.get("/admin/stats/revenue",
            response_model=RevenueStatsResponse, summary="获取收入统计（管理员）")
async def admin_get_revenue_stats(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """管理员获取收入统计"""
    stats = await conversion_tracking_service.get_revenue_stats(db, start_date, end_date)
    return stats


@router.get("/admin/stats/conversions",
            response_model=ConversionStatsResponse, summary="获取全局转化统计（管理员）")
async def admin_get_conversion_stats(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(ge=1, le=365, default=30),
):
    """管理员获取全局转化统计"""
    stats = await conversion_tracking_service.get_conversion_stats(db, None, days)
    return stats
