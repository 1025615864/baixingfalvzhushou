"""会员体系 API 路由

提供会员权益查询、付费转化统计功能。
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
from ..services.membership_service import membership_service, conversion_tracking_service

router = APIRouter(prefix="/membership", tags=["会员体系"])


class MembershipBenefitsResponse(BaseModel):
    """会员权益响应"""

    tier: str
    name: str
    daily_ai_chat_limit: int
    daily_document_limit: int
    priority_support: bool
    advanced_features: bool
    api_access: bool
    custom_branding: bool


class UserMembershipResponse(BaseModel):
    """用户会员信息响应"""

    tier: str
    is_vip: bool
    benefits: dict[str, Any]
    quota: dict[str, Any]


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
        return {"tier": tier, "name": "未知",
                "daily_ai_chat_limit": 0, "daily_document_limit": 0}
    return benefits


@router.get("/me", response_model=UserMembershipResponse, summary="获取当前用户会员信息")
async def get_my_membership(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取当前用户的会员等级和权益"""
    result = await membership_service.get_user_benefits(db, current_user)
    return result


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
