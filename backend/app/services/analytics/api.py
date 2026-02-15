from __future__ import annotations

from datetime import datetime, timezone, timedelta

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.user import User
from ...schemas.analytics import (
    ActionStatisticsItem,
    ActionStatisticsResponse,
    BehaviorHistoryItem,
    BehaviorHistoryResponse,
    BehaviorLogRequest,
    BehaviorLogResponse,
    ConversionFunnelData,
    ConversionFunnelRequest,
    ConversionFunnelResponse,
    ConversionFunnelStep,
    FeatureUsage,
    FunnelStepResult,
    MetricsResponse,
    RevenueDataPoint,
    RevenueResponse,
    RevenueSource,
    ResourceViewCountResponse,
    RetentionItem,
    RetentionRequest,
    RetentionResponse,
    UserActivityPoint,
    UserBehaviorData,
)
from ...services.analytics_service import analytics_service


async def log_behavior_request(
    *,
    request: Request,
    data: BehaviorLogRequest,
    current_user: User,
    db: AsyncSession,
) -> BehaviorLogResponse:
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    referrer = request.headers.get("referer")

    log = await analytics_service.log_behavior(
        db=db,
        user_id=int(current_user.id),
        action=data.action,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        metadata=data.metadata,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer,
        session_id=data.session_id,
    )

    return BehaviorLogResponse(
        id=int(log.id),
        user_id=int(log.user_id) if log.user_id else None,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=int(log.resource_id) if log.resource_id else None,
        metadata=log.metadata_json,
        created_at=log.created_at,
    )


async def get_behavior_history_request(
    *,
    current_user: User,
    db: AsyncSession,
    action: str | None = None,
    resource_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> BehaviorHistoryResponse:
    logs = await analytics_service.get_user_behavior_history(
        db=db,
        user_id=int(current_user.id),
        action=action,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )

    items = [
        BehaviorHistoryItem(
            id=int(log.id),
            action=log.action,
            resource_type=log.resource_type,
            resource_id=int(log.resource_id) if log.resource_id else None,
            metadata=log.metadata_json,
            created_at=log.created_at,
        )
        for log in logs
    ]

    return BehaviorHistoryResponse(
        user_id=int(current_user.id),
        total=len(items),
        items=items,
    )


async def get_resource_view_count_request(
    *,
    resource_type: str,
    resource_id: int,
    db: AsyncSession,
) -> ResourceViewCountResponse:
    count = await analytics_service.get_resource_view_count(
        db=db,
        resource_type=resource_type,
        resource_id=resource_id,
    )

    return ResourceViewCountResponse(
        resource_type=resource_type,
        resource_id=resource_id,
        view_count=count,
    )


async def get_action_statistics_request(
    *,
    db: AsyncSession,
    start_date: str | None = None,
    end_date: str | None = None,
    action: str | None = None,
) -> ActionStatisticsResponse:
    if not start_date:
        start_date = (
            datetime.now(
                timezone.utc) -
            timedelta(
                days=7)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    start_dt = datetime.strptime(start_date,
                                 "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, tzinfo=timezone.utc
    )

    stats = await analytics_service.get_action_statistics(
        db=db,
        start_date=start_dt,
        end_date=end_dt,
        action=action,
    )

    items = [ActionStatisticsItem(action=act, count=count)
             for act, count in stats.items()]

    return ActionStatisticsResponse(
        start_date=start_date,
        end_date=end_date,
        items=items,
    )


async def conversion_funnel_request(
    *,
    db: AsyncSession,
    data: ConversionFunnelRequest,
) -> ConversionFunnelResponse:
    tzinfo = datetime.now().astimezone().tzinfo
    start_dt = datetime.strptime(
        data.start_date, "%Y-%m-%d").replace(tzinfo=tzinfo)
    end_dt = datetime.strptime(data.end_date, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, tzinfo=tzinfo
    )

    funnel_steps = [
        {
            "name": step.name,
            "action": step.action,
            "resource_type": step.resource_type,
            "condition": step.condition,
        }
        for step in data.funnel_steps
    ]

    results = await analytics_service.get_conversion_funnel(
        db=db,
        start_date=start_dt,
        end_date=end_dt,
        funnel_steps=funnel_steps,
    )

    steps = [
        FunnelStepResult(
            name=result["name"],
            count=result["count"],
            conversion_rate=result["conversion_rate"],
            drop_rate=result["drop_rate"],
        )
        for result in results
    ]

    return ConversionFunnelResponse(
        start_date=data.start_date,
        end_date=data.end_date,
        steps=steps,
    )


async def user_retention_request(
    *,
    db: AsyncSession,
    data: RetentionRequest,
) -> RetentionResponse:
    tzinfo = datetime.now().astimezone().tzinfo
    cohort_dt = datetime.strptime(
        data.cohort_date, "%Y-%m-%d").replace(tzinfo=tzinfo)

    results = await analytics_service.get_user_retention(
        db=db,
        cohort_date=cohort_dt,
        retention_days=data.retention_days,
    )

    start_of_day = datetime(
        cohort_dt.year,
        cohort_dt.month,
        cohort_dt.day,
        tzinfo=cohort_dt.tzinfo)
    end_of_day = start_of_day.replace(hour=23, minute=59, second=59)

    query = select(User.id).where(
        User.created_at >= start_of_day,
        User.created_at <= end_of_day,
    )
    result = await db.execute(query)
    cohort_count = len(result.scalars().all())

    retention_items = [
        RetentionItem(day=item["day"], count=item["count"], rate=item["rate"])
        for item in results
    ]

    return RetentionResponse(
        cohort_date=data.cohort_date,
        cohort_count=cohort_count,
        retention=retention_items,
    )


# ============ 商业Dashboard相关 ============


async def get_metrics(
    *,
    db: AsyncSession,
) -> MetricsResponse:
    """
    获取关键指标

    Args:
        db: 数据库会话

    Returns:
        MetricsResponse: 关键指标响应
    """
    from datetime import datetime, timezone, timedelta
    from ...models.user import User

    # 计算时间范围
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    # 获取DAU（日活跃用户）
    dau = await analytics_service.get_daily_active_users(db=db, date=today_start)

    # 获取MAU估算值（过去30天新注册用户）
    thirty_days_ago = today_start - timedelta(days=30)
    query = select(User.id).where(User.created_at >= thirty_days_ago)
    result = await db.execute(query)
    mau = len(result.scalars().all())

    # 获取总收入（模拟数据，实际应从支付表查询）
    total_revenue = 0.0
    # TODO: 从payment表汇总收入

    # 获取付费用户数（模拟数据，实际应从支付表查询）
    paying_users = 0
    # TODO: 从payment表统计付费用户

    return MetricsResponse(
        dau=dau,
        mau=mau,
        total_revenue=total_revenue,
        paying_users=paying_users,
        timestamp=now.strftime("%Y-%m-%d %H:%M:%S UTC"),
    )


async def get_revenue(
    *,
    db: AsyncSession,
    start_date: str | None = None,
    end_date: str | None = None,
) -> RevenueResponse:
    """
    获取收入统计

    Args:
        db: 数据库会话
        start_date: 开始日期，格式：YYYY-MM-DD
        end_date: 结束日期，格式：YYYY-MM-DD

    Returns:
        RevenueResponse: 收入统计响应
    """
    from datetime import datetime, timezone, timedelta

    # 设置默认时间范围（过去30天）
    if not start_date:
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, tzinfo=timezone.utc
    )

    # 生成收入趋势数据（模拟数据，实际应从支付表查询）
    trend = []
    current_dt = start_dt
    while current_dt <= end_dt:
        # TODO: 从payment表按日期汇总收入
        trend.append(
            RevenueDataPoint(
                date=current_dt.strftime("%Y-%m-%d"),
                revenue=0.0,
                membership=0.0,
                consultation=0.0,
                other=0.0,
            )
        )
        current_dt += timedelta(days=1)

    # 收入来源分布（模拟数据）
    total = sum(data.revenue for data in trend)
    sources = [
        RevenueSource(
            name="会员订阅",
            value=0.0,
            percentage=0.0 if total == 0 else 0.0,
            color="#3B82F6",
        ),
        RevenueSource(
            name="咨询服务",
            value=0.0,
            percentage=0.0 if total == 0 else 0.0,
            color="#10B981",
        ),
        RevenueSource(
            name="其他",
            value=0.0,
            percentage=0.0 if total == 0 else 0.0,
            color="#F59E0B",
        ),
    ]

    return RevenueResponse(
        trend=trend,
        sources=sources,
        total=total,
    )


async def get_conversion_dashboard(
    *,
    db: AsyncSession,
    start_date: str | None = None,
    end_date: str | None = None,
) -> ConversionFunnelData:
    """
    获取转化漏斗Dashboard数据

    Args:
        db: 数据库会话
        start_date: 开始日期，格式：YYYY-MM-DD
        end_date: 结束日期，格式：YYYY-MM-DD

    Returns:
        ConversionFunnelData: 转化漏斗数据
    """
    from datetime import datetime, timezone, timedelta

    # 设置默认时间范围（过去7天）
    if not start_date:
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, tzinfo=timezone.utc
    )

    # 定义漏斗步骤
    funnel_steps = [
        {
            "name": "浏览首页",
            "action": "page_view",
            "resource_type": None,
            "condition": None,
        },
        {
            "name": "浏览律师列表",
            "action": "page_view",
            "resource_type": "lawyer",
            "condition": None,
        },
        {
            "name": "发起咨询",
            "action": "click",
            "resource_type": "consultation",
            "condition": None,
        },
        {
            "name": "支付成功",
            "action": "purchase",
            "resource_type": "payment",
            "condition": None,
        },
    ]

    # 获取漏斗数据
    results = await analytics_service.get_conversion_funnel(
        db=db,
        start_date=start_dt,
        end_date=end_dt,
        funnel_steps=funnel_steps,
    )

    # 构建步骤数据
    steps = [
        ConversionFunnelStep(
            name=result["name"],
            count=result["count"],
            conversion_rate=result["conversion_rate"],
            drop_rate=result["drop_rate"],
            color=_get_step_color(i),
        )
        for i, result in enumerate(results)
    ]

    # 计算整体转化率和总用户数
    total_users = steps[0].count if steps else 0
    overall_conversion = steps[-1].conversion_rate if steps else 0.0

    return ConversionFunnelData(
        steps=steps,
        total_users=total_users,
        overall_conversion=overall_conversion,
        start_date=start_date,
        end_date=end_date,
    )


async def get_user_behavior_dashboard(
    *,
    db: AsyncSession,
    start_date: str | None = None,
    end_date: str | None = None,
) -> UserBehaviorData:
    """
    获取用户行为Dashboard数据

    Args:
        db: 数据库会话
        start_date: 开始日期，格式：YYYY-MM-DD
        end_date: 结束日期，格式：YYYY-MM-DD

    Returns:
        UserBehaviorData: 用户行为数据
    """
    from datetime import datetime, timezone, timedelta
    from ...models.user import User

    # 设置默认时间范围（过去7天）
    if not start_date:
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, tzinfo=timezone.utc
    )

    # 生成活跃度趋势数据
    activity_trend = []
    current_dt = start_dt
    total_sessions = 0
    total_session_duration = 0.0

    while current_dt <= end_dt:
        # 获取日活跃用户
        dau = await analytics_service.get_daily_active_users(db=db, date=current_dt)

        # 获取新注册用户
        from sqlalchemy import select
        day_start = datetime(
            current_dt.year, current_dt.month, current_dt.day, tzinfo=timezone.utc
        )
        day_end = day_start.replace(hour=23, minute=59, second=59)
        query = select(User.id).where(User.created_at >= day_start, User.created_at <= day_end)
        result = await db.execute(query)
        new_users = len(result.scalars().all())

        # 计算回归用户（模拟数据）
        returning_users = max(0, dau - new_users)

        activity_trend.append(
            UserActivityPoint(
                date=current_dt.strftime("%Y-%m-%d"),
                active_users=dau,
                new_users=new_users,
                returning_users=returning_users,
            )
        )

        # 累计会话数据（模拟）
        # TODO: 从behavior_log表实际统计
        total_sessions += dau
        total_session_duration += dau * 120  # 假设平均会话时长2分钟

        current_dt += timedelta(days=1)

    # 获取功能使用统计
    action_stats = await analytics_service.get_action_statistics(
        db=db, start_date=start_dt, end_date=end_dt, action=None
    )

    total_actions = sum(action_stats.values())
    feature_usage = [
        FeatureUsage(
            feature="页面浏览",
            usage_count=action_stats.get("page_view", 0),
            percentage=(
                action_stats.get("page_view", 0) / total_actions * 100 if total_actions > 0 else 0
            ),
            color="#3B82F6",
        ),
        FeatureUsage(
            feature="点击",
            usage_count=action_stats.get("click", 0),
            percentage=(
                action_stats.get("click", 0) / total_actions * 100 if total_actions > 0 else 0
            ),
            color="#10B981",
        ),
        FeatureUsage(
            feature="搜索",
            usage_count=action_stats.get("search", 0),
            percentage=(
                action_stats.get("search", 0) / total_actions * 100 if total_actions > 0 else 0
            ),
            color="#F59E0B",
        ),
        FeatureUsage(
            feature="收藏",
            usage_count=action_stats.get("favorite", 0),
            percentage=(
                action_stats.get("favorite", 0) / total_actions * 100 if total_actions > 0 else 0
            ),
            color="#EF4444",
        ),
    ]

    # 计算平均会话时长（秒）
    average_session_duration = (
        total_session_duration / total_sessions if total_sessions > 0 else 0
    )

    return UserBehaviorData(
        activity_trend=activity_trend,
        feature_usage=feature_usage,
        total_sessions=total_sessions,
        average_session_duration=average_session_duration,
    )


def _get_step_color(step_index: int) -> str:
    """获取漏斗步骤颜色"""
    colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]
    return colors[step_index % len(colors)]
