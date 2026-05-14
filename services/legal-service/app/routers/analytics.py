"""数据分析路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.analytics_service import AnalyticsService
from ..middleware.auth import get_current_lawyer, get_current_user, AuthUser
from ..schemas.response import ApiResponse

router = APIRouter()


@router.get("/overview")
async def get_overview(
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """核心指标概览"""
    from ..services.lawyer_service import LawyerService
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    service = AnalyticsService(db)
    data = await service.get_overview(lawyer.id)
    return ApiResponse.success(data)


@router.get("/trends")
async def get_trends(
    days: int = 30,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """趋势图表数据"""
    from ..services.lawyer_service import LawyerService
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    service = AnalyticsService(db)
    data = await service.get_trends(lawyer.id, days)
    return ApiResponse.success({"days": days, "trends": data})


@router.get("/channel-distribution")
async def get_channel_distribution(
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """案源渠道分布"""
    from ..services.lawyer_service import LawyerService
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    service = AnalyticsService(db)
    data = await service.get_channel_distribution(lawyer.id)
    return ApiResponse.success({"channels": data, "lawyer_id": lawyer.id})


@router.get("/ranking")
async def get_ranking(
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """排名对比"""
    from ..services.lawyer_service import LawyerService
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    service = AnalyticsService(db)
    data = await service.get_ranking(lawyer.id)
    return ApiResponse.success(data)


@router.get("/firm-dashboard")
async def get_firm_dashboard(
    firm_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """律所数据看板"""
    service = AnalyticsService(db)
    data = await service.get_firm_dashboard(firm_id)
    return ApiResponse.success(data)