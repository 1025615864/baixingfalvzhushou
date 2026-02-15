"""用户行为分析API路由

提供用户行为日志记录、查询等API接口。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..schemas.analytics import (
    ActionStatisticsResponse,
    BehaviorLogRequest,
    BehaviorLogResponse,
    BehaviorHistoryResponse,
    ConversionFunnelData as ConversionFunnelDashboardResponse,
    ConversionFunnelRequest,
    ConversionFunnelResponse,
    MetricsResponse,
    ResourceViewCountResponse,
    RevenueResponse,
    RetentionRequest,
    RetentionResponse,
    UserBehaviorData,
)
from ..services.analytics.api import (
    get_conversion_dashboard,
    get_metrics,
    get_revenue,
    get_user_behavior_dashboard,
    log_behavior_request,
    get_behavior_history_request,
    get_resource_view_count_request,
    get_action_statistics_request,
    conversion_funnel_request,
    user_retention_request,
)
from ..utils.deps import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/log", response_model=BehaviorLogResponse, summary="记录用户行为")
async def log_behavior(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    data: BehaviorLogRequest,
):
    """
    记录用户行为日志

    支持的行为类型：
    - page_view: 页面浏览
    - click: 点击
    - submit: 提交
    - search: 搜索
    - download: 下载
    - share: 分享
    - favorite: 收藏
    - comment: 评论
    - like: 点赞
    - purchase: 购买
    - register: 注册
    - login: 登录
    - logout: 登出

    支持的资源类型：
    - post: 帖子
    - consultation: 咨询
    - lawyer: 律师
    - news: 新闻
    - knowledge: 知识库
    - contract: 合同
    - document: 文档
    - payment: 支付
    - order: 订单
    """
    return await log_behavior_request(
        request=request,
        data=data,
        current_user=current_user,
        db=db,
    )


@router.get("/history", response_model=BehaviorHistoryResponse,
            summary="获取用户行为历史")
async def get_behavior_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    action: Annotated[str | None, Query(description="行为类型过滤")] = None,
    resource_type: Annotated[str | None, Query(description="资源类型过滤")] = None,
    limit: Annotated[int, Query(description="返回数量限制", ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(description="偏移量", ge=0)] = 0,
):
    """获取当前用户的行为历史记录"""
    return await get_behavior_history_request(
        current_user=current_user,
        db=db,
        action=action,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )


@router.get("/resource/{resource_type}/{resource_id}/view-count",
            response_model=ResourceViewCountResponse, summary="获取资源浏览次数")
async def get_resource_view_count(
    resource_type: str,
    resource_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取指定资源的浏览次数"""
    return await get_resource_view_count_request(
        resource_type=resource_type,
        resource_id=resource_id,
        db=db,
    )


@router.get("/statistics/actions",
            response_model=ActionStatisticsResponse, summary="获取行为统计")
async def get_action_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Annotated[str | None, Query(
        description="开始日期，格式：YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, Query(
        description="结束日期，格式：YYYY-MM-DD")] = None,
    action: Annotated[str | None, Query(description="行为类型过滤")] = None,
):
    """
    获取行为统计

    需要管理员权限
    """
    return await get_action_statistics_request(
        db=db,
        start_date=start_date,
        end_date=end_date,
        action=action,
    )


# ============ 转化漏斗分析相关 ============


@router.post("/funnel/conversion",
             response_model=ConversionFunnelResponse, summary="用户转化漏斗分析")
async def conversion_funnel(
    db: Annotated[AsyncSession, Depends(get_db)],
    data: ConversionFunnelRequest,
):
    """
    获取用户转化漏斗分析

    需要管理员权限
    """
    return await conversion_funnel_request(
        db=db,
        data=data,
    )


# ============ 用户留存分析相关 ============


@router.post("/retention", response_model=RetentionResponse, summary="用户留存分析")
async def user_retention(
    db: Annotated[AsyncSession, Depends(get_db)],
    data: RetentionRequest,
):
    """
    获取用户留存分析

    需要管理员权限
    """
    return await user_retention_request(
        db=db,
        data=data,
    )


# ============ 商业Dashboard相关 ============


@router.get("/dashboard/metrics", response_model=MetricsResponse, summary="获取Dashboard关键指标")
async def dashboard_metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    获取Dashboard关键指标

    包括：
    - DAU: 日活跃用户数
    - MAU: 月活跃用户数
    - 总收入
    - 付费用户数
    """
    return await get_metrics(
        db=db,
    )


@router.get("/dashboard/revenue", response_model=RevenueResponse, summary="获取收入统计")
async def dashboard_revenue(
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Annotated[str | None, Query(
        description="开始日期，格式：YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, Query(
        description="结束日期，格式：YYYY-MM-DD")] = None,
):
    """
    获取收入统计

    包括收入趋势和收入来源分布
    """
    return await get_revenue(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/dashboard/conversion", response_model=ConversionFunnelDashboardResponse,
            summary="获取转化漏斗Dashboard数据")
async def dashboard_conversion(
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Annotated[str | None, Query(
        description="开始日期，格式：YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, Query(
        description="结束日期，格式：YYYY-MM-DD")] = None,
):
    """
    获取转化漏斗Dashboard数据

    展示用户从浏览到付费的转化路径
    """
    return await get_conversion_dashboard(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/dashboard/user-behavior", response_model=UserBehaviorData,
            summary="获取用户行为Dashboard数据")
async def dashboard_user_behavior(
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Annotated[str | None, Query(
        description="开始日期，格式：YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, Query(
        description="结束日期，格式：YYYY-MM-DD")] = None,
):
    """
    获取用户行为Dashboard数据

    包括用户活跃度趋势和功能使用情况
    """
    return await get_user_behavior_dashboard(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )
