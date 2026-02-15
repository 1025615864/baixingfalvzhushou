"""营销渠道追踪API

支持UTM参数追踪和渠道归因分析"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Annotated, Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.channel import Channel
from ..schemas.channel import (
    ChannelCreate,
    ChannelUpdate,
    ChannelResponse,
    ChannelListResponse,
    ChannelStats,
    ChannelMetricsResponse,
    ConversionFunnel,
    ChannelAnalytics,
    ChannelParams,
    TrackEvent,
)
from ..utils.structured_logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/channel-tracking", tags=["渠道追踪"])


# ============ 辅助函数 ============

def parse_json_config(config_str: Optional[str]) -> Optional[Dict[str, Any]]:
    """解析JSON配置字符串"""
    if not config_str:
        return None
    try:
        return json.loads(config_str)
    except json.JSONDecodeError:
        return None


def build_channel_response(channel: Channel) -> ChannelResponse:
    """构建渠道响应对象"""
    return ChannelResponse(
        id=channel.id,
        name=channel.name,
        code=channel.code,
        description=channel.description,
        url=channel.url,
        type=channel.type,
        status=channel.status,
        visit_count=channel.visit_count,
        register_count=channel.register_count,
        activation_count=channel.activation_count,
        payment_count=channel.payment_count,
        total_revenue=channel.total_revenue,
        conversion_rate=channel.conversion_rate,
        activation_rate=channel.activation_rate,
        payment_rate=channel.payment_rate,
        avg_order_value=channel.avg_order_value,
        landing_config=parse_json_config(channel.landing_config),
        offer_config=parse_json_config(channel.offer_config),
        tracking_config=parse_json_config(channel.tracking_config),
        created_at=channel.created_at,
        updated_at=channel.updated_at,
    )


# ============ 统计 API ============

@router.get("/stats", response_model=ChannelStats)
async def get_channel_stats(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """获取渠道统计数据"""
    # 总渠道数
    total_result = await db.execute(select(func.count()).select_from(Channel))
    total_channels = total_result.scalar() or 0

    # 活跃渠道数
    active_result = await db.execute(
        select(func.count()).select_from(Channel).where(Channel.status == "active")
    )
    active_channels = active_result.scalar() or 0

    # 汇总统计数据
    stats_result = await db.execute(
        select(
            func.sum(Channel.visit_count).label("total_visits"),
            func.sum(Channel.register_count).label("total_registers"),
            func.sum(Channel.activation_count).label("total_activations"),
            func.sum(Channel.payment_count).label("total_payments"),
            func.sum(Channel.total_revenue).label("total_revenue"),
        )
    )
    row = stats_result.one_or_none()

    total_visits = row.total_visits if row and row.total_visits else 0
    total_registers = row.total_registers if row and row.total_registers else 0
    total_activations = row.total_activations if row and row.total_activations else 0
    total_payments = row.total_payments if row and row.total_payments else 0
    total_revenue = row.total_revenue if row and row.total_revenue else 0

    # 计算平均转化率
    avg_conversion_rate = round(total_payments / total_visits * 100, 2) if total_visits > 0 else 0.0

    return ChannelStats(
        total_channels=total_channels,
        active_channels=active_channels,
        total_visits=total_visits,
        total_registers=total_registers,
        total_activations=total_activations,
        total_payments=total_payments,
        total_revenue=total_revenue,
        avg_conversion_rate=avg_conversion_rate,
    )


# ============ 渠道列表 API ============

@router.get("/list", response_model=ChannelListResponse)
async def get_channel_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小"),
    name: Optional[str] = Query(None, description="按名称搜索"),
    status: Optional[str] = Query(None, pattern=r"^(active|inactive)$", description="按状态过滤"),
    type: Optional[str] = Query(None, pattern=r"^(weixin|douyin|xiaohongshu|zhihu|bilibili|website|other)$", description="按类型过滤"),
):
    """获取渠道列表（支持分页、搜索和过滤）"""
    # 构建查询条件
    conditions = []
    if name:
        conditions.append(Channel.name.ilike(f"%{name}%"))
    if status:
        conditions.append(Channel.status == status)
    if type:
        conditions.append(Channel.type == type)

    # 查询总数
    count_query = select(func.count()).select_from(Channel)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 查询数据
    query = select(Channel).order_by(Channel.created_at.desc())
    if conditions:
        query = query.where(and_(*conditions))

    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    channels = result.scalars().all()

    # 构建响应
    channel_responses = [build_channel_response(channel) for channel in channels]

    return ChannelListResponse(
        channels=channel_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


# ============ 渠道详情 API ============

@router.get("/detail/{channel_id}", response_model=ChannelResponse)
async def get_channel_detail(
    channel_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """获取单个渠道详情"""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="渠道不存在"
        )

    return build_channel_response(channel)


@router.get("/detail/by-code/{code}", response_model=ChannelResponse)
async def get_channel_by_code(
    code: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """通过代码获取渠道详情"""
    result = await db.execute(select(Channel).where(Channel.code == code))
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="渠道不存在"
        )

    return build_channel_response(channel)


# ============ 渠道管理 API ============

@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    data: ChannelCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """创建新渠道"""
    # 检查渠道代码是否已存在
    existing = await db.execute(select(Channel).where(Channel.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"渠道代码 '{data.code}' 已存在"
        )

    # 创建渠道
    channel = Channel(
        name=data.name,
        code=data.code,
        description=data.description,
        url=data.url,
        type=data.type,
        status=data.status,
        landing_config=json.dumps(data.landing_config, ensure_ascii=False) if data.landing_config else None,
        offer_config=json.dumps(data.offer_config, ensure_ascii=False) if data.offer_config else None,
        tracking_config=json.dumps(data.tracking_config, ensure_ascii=False) if data.tracking_config else None,
    )

    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    logger.info(f"创建渠道成功: {channel.code} - {channel.name}")
    return build_channel_response(channel)


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: int,
    data: ChannelUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """更新渠道"""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="渠道不存在"
        )

    # 更新字段
    update_data = data.model_dump(exclude_unset=True)

    # 处理JSON字段
    if "landing_config" in update_data and update_data["landing_config"] is not None:
        update_data["landing_config"] = json.dumps(update_data["landing_config"], ensure_ascii=False)
    if "offer_config" in update_data and update_data["offer_config"] is not None:
        update_data["offer_config"] = json.dumps(update_data["offer_config"], ensure_ascii=False)
    if "tracking_config" in update_data and update_data["tracking_config"] is not None:
        update_data["tracking_config"] = json.dumps(update_data["tracking_config"], ensure_ascii=False)

    for field, value in update_data.items():
        setattr(channel, field, value)

    await db.commit()
    await db.refresh(channel)

    logger.info(f"更新渠道成功: {channel.code}")
    return build_channel_response(channel)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """删除渠道"""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="渠道不存在"
        )

    await db.delete(channel)
    await db.commit()

    logger.info(f"删除渠道成功: {channel.code} - {channel.name}")
    return None


# ============ 追踪事件 API ============

@router.post("/track")
async def track_event(
    events: list[TrackEvent],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """埋点事件上报"""
    for event in events:
        # 记录埋点事件到日志
        logger.info(
            f"Channel Track: {event.event_type}",
            extra={
                "event_type": event.event_type,
                "user_id": event.user_id,
                "channel_params": event.channel_params.model_dump(),
                "timestamp": event.timestamp.isoformat(),
            }
        )

        # 如果有渠道ID，更新渠道统计
        if event.channel_params.channel_id:
            result = await db.execute(
                select(Channel).where(Channel.code == event.channel_params.channel_id)
            )
            channel = result.scalar_one_or_none()

            if channel:
                # 根据事件类型更新统计
                if event.event_type == "visit":
                    channel.visit_count += 1
                elif event.event_type == "register":
                    channel.register_count += 1
                elif event.event_type == "activation":
                    channel.activation_count += 1
                elif event.event_type == "payment":
                    channel.payment_count += 1

                await db.commit()

    return {"success": True, "count": len(events)}


# ============ 分析数据 API ============

@router.get("/analytics", response_model=list[ChannelAnalytics])
async def get_analytics(
    db: Annotated[AsyncSession, Depends(get_db)],
    channel_ids: Optional[str] = Query(None, description="频道ID列表，逗号分隔"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
):
    """获取渠道分析数据"""
    query = select(Channel).where(Channel.status == "active")

    if channel_ids:
        ids = [int(cid.strip()) for cid in channel_ids.split(",") if cid.strip().isdigit()]
        if ids:
            query = query.where(Channel.id.in_(ids))

    result = await db.execute(query)
    channels = result.scalars().all()

    results = []
    for channel in channels:
        # 计算漏斗数据
        visits = channel.visit_count
        registers = channel.register_count
        activations = channel.activation_count
        payments = channel.payment_count

        funnel = ConversionFunnel(
            visits=visits,
            visits_percentage=100.0,
            registers=registers,
            registers_percentage=round(registers / visits * 100, 2) if visits > 0 else 0.0,
            activations=activations,
            activations_percentage=round(activations / registers * 100, 2) if registers > 0 else 0.0,
            payments=payments,
            payments_percentage=round(payments / activations * 100, 2) if activations > 0 else 0.0,
        )

        metrics = ChannelMetricsResponse(
            visit_count=visits,
            register_count=registers,
            activation_count=activations,
            payment_count=payments,
            total_revenue=channel.total_revenue / 100,  # 转换为元
            avg_order_value=channel.avg_order_value,
            conversion_rate=channel.conversion_rate,
            activation_rate=channel.activation_rate,
            payment_rate=channel.payment_rate,
        )

        analytics = ChannelAnalytics(
            channel_id=channel.id,
            channel_name=channel.name,
            funnel=funnel,
            metrics=metrics,
        )
        results.append(analytics)

    return results


@router.get("/analytics/{channel_id}", response_model=ChannelAnalytics)
async def get_channel_analytics(
    channel_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
):
    """获取单个渠道的详细分析数据"""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="渠道不存在"
        )

    # 计算漏斗数据
    visits = channel.visit_count
    registers = channel.register_count
    activations = channel.activation_count
    payments = channel.payment_count

    funnel = ConversionFunnel(
        visits=visits,
        visits_percentage=100.0,
        registers=registers,
        registers_percentage=round(registers / visits * 100, 2) if visits > 0 else 0.0,
        activations=activations,
        activations_percentage=round(activations / registers * 100, 2) if registers > 0 else 0.0,
        payments=payments,
        payments_percentage=round(payments / activations * 100, 2) if activations > 0 else 0.0,
    )

    metrics = ChannelMetricsResponse(
        visit_count=visits,
        register_count=registers,
        activation_count=activations,
        payment_count=payments,
        total_revenue=channel.total_revenue / 100,  # 转换为元
        avg_order_value=channel.avg_order_value,
        conversion_rate=channel.conversion_rate,
        activation_rate=channel.activation_rate,
        payment_rate=channel.payment_rate,
    )

    return ChannelAnalytics(
        channel_id=channel.id,
        channel_name=channel.name,
        funnel=funnel,
        metrics=metrics,
    )


@router.get("/analytics/compare")
async def compare_channels(
    db: Annotated[AsyncSession, Depends(get_db)],
    channel_ids: str = Query(..., description="频道ID列表，逗号分隔"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
):
    """获取渠道对比数据"""
    ids = [int(cid.strip()) for cid in channel_ids.split(",") if cid.strip().isdigit()]

    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供有效的渠道ID"
        )

    result = await db.execute(select(Channel).where(Channel.id.in_(ids)))
    channels = result.scalars().all()

    comparison = []
    for channel in channels:
        comparison.append({
            "channel_id": channel.id,
            "channel_code": channel.code,
            "channel_name": channel.name,
            "metrics": {
                "visits": channel.visit_count,
                "registers": channel.register_count,
                "activations": channel.activation_count,
                "payments": channel.payment_count,
                "revenue": channel.total_revenue / 100,  # 转换为元
                "conversion_rate": channel.conversion_rate,
            },
        })

    return {"comparison": comparison}
