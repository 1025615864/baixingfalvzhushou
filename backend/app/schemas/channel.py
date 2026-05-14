"""渠道相关 Pydantic 模式"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Any, Dict

from pydantic import BaseModel, Field


# ============ 基础 Schema ============

class ChannelBase(BaseModel):
    """渠道基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="渠道名称")
    code: str = Field(..., min_length=1, max_length=50, description="渠道代码")
    description: Optional[str] = Field(None, max_length=1000, description="渠道描述")
    url: Optional[str] = Field(None, max_length=500, description="渠道链接")
    type: str = Field(default="other", pattern=r"^(weixin|douyin|xiaohongshu|zhihu|bilibili|website|other)$", description="渠道类型")
    status: str = Field(default="active", pattern=r"^(active|inactive)$", description="状态")


class ChannelCreate(ChannelBase):
    """创建渠道请求模式"""
    landing_config: Optional[Dict[str, Any]] = Field(None, description="落地页配置")
    offer_config: Optional[Dict[str, Any]] = Field(None, description="优惠配置")
    tracking_config: Optional[Dict[str, Any]] = Field(None, description="追踪配置")


class ChannelUpdate(BaseModel):
    """更新渠道请求模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="渠道名称")
    description: Optional[str] = Field(None, max_length=1000, description="渠道描述")
    url: Optional[str] = Field(None, max_length=500, description="渠道链接")
    type: Optional[str] = Field(None, pattern=r"^(weixin|douyin|xiaohongshu|zhihu|bilibili|website|other)$", description="渠道类型")
    status: Optional[str] = Field(None, pattern=r"^(active|inactive)$", description="状态")
    landing_config: Optional[Dict[str, Any]] = Field(None, description="落地页配置")
    offer_config: Optional[Dict[str, Any]] = Field(None, description="优惠配置")
    tracking_config: Optional[Dict[str, Any]] = Field(None, description="追踪配置")


# ============ 响应 Schema ============

class ChannelResponse(ChannelBase):
    """渠道响应模式"""
    id: int = Field(..., description="渠道ID")
    visit_count: int = Field(default=0, description="访问数")
    register_count: int = Field(default=0, description="注册数")
    activation_count: int = Field(default=0, description="激活数")
    payment_count: int = Field(default=0, description="支付数")
    total_revenue: int = Field(default=0, description="总收入(分)")
    conversion_rate: float = Field(default=0.0, description="转化率")
    activation_rate: float = Field(default=0.0, description="激活率")
    payment_rate: float = Field(default=0.0, description="支付率")
    avg_order_value: float = Field(default=0.0, description="平均订单价值")
    landing_config: Optional[Dict[str, Any]] = Field(None, description="落地页配置")
    offer_config: Optional[Dict[str, Any]] = Field(None, description="优惠配置")
    tracking_config: Optional[Dict[str, Any]] = Field(None, description="追踪配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ChannelListResponse(BaseModel):
    """渠道列表响应"""
    channels: list[ChannelResponse] = Field(..., description="渠道列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")


# ============ 统计数据 Schema ============

class ChannelStats(BaseModel):
    """渠道统计数据"""
    total_channels: int = Field(..., description="总渠道数")
    active_channels: int = Field(..., description="活跃渠道数")
    total_visits: int = Field(..., description="总访问数")
    total_registers: int = Field(..., description="总注册数")
    total_activations: int = Field(..., description="总激活数")
    total_payments: int = Field(..., description="总支付数")
    total_revenue: int = Field(..., description="总收入(分)")
    avg_conversion_rate: float = Field(..., description="平均转化率")


class ChannelMetricsResponse(BaseModel):
    """渠道指标响应"""
    visit_count: int = Field(..., description="访问数")
    register_count: int = Field(..., description="注册数")
    activation_count: int = Field(..., description="激活数")
    payment_count: int = Field(..., description="支付数")
    total_revenue: float = Field(..., description="总收入(元)")
    avg_order_value: float = Field(..., description="平均订单价值")
    conversion_rate: float = Field(..., description="转化率")
    activation_rate: float = Field(..., description="激活率")
    payment_rate: float = Field(..., description="支付率")


class ConversionFunnel(BaseModel):
    """转化漏斗"""
    visits: int = Field(..., description="访问数")
    visits_percentage: float = Field(..., description="访问占比")
    registers: int = Field(..., description="注册数")
    registers_percentage: float = Field(..., description="注册转化率")
    activations: int = Field(..., description="激活数")
    activations_percentage: float = Field(..., description="激活转化率")
    payments: int = Field(..., description="支付数")
    payments_percentage: float = Field(..., description="支付转化率")


class ChannelAnalytics(BaseModel):
    """渠道分析数据"""
    channel_id: int = Field(..., description="渠道ID")
    channel_name: str = Field(..., description="渠道名称")
    funnel: ConversionFunnel = Field(..., description="转化漏斗")
    metrics: ChannelMetricsResponse = Field(..., description="渠道指标")


# ============ 追踪事件 Schema ============

class ChannelParams(BaseModel):
    """渠道参数"""
    source: Optional[str] = Field(None, description="utm_source")
    medium: Optional[str] = Field(None, description="utm_medium")
    campaign: Optional[str] = Field(None, description="utm_campaign")
    content: Optional[str] = Field(None, description="utm_content")
    term: Optional[str] = Field(None, description="utm_term")
    channel_id: Optional[str] = Field(None, description="自定义渠道ID")


class TrackEvent(BaseModel):
    """埋点事件"""
    event_type: str = Field(..., pattern=r"^(visit|register|activation|payment)$", description="事件类型")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    channel_params: ChannelParams = Field(..., description="渠道参数")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外数据")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="时间戳")


# ============ 查询参数 Schema ============

class ChannelListParams(BaseModel):
    """渠道列表查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页大小")
    name: Optional[str] = Field(None, description="按名称搜索")
    status: Optional[str] = Field(None, pattern=r"^(active|inactive)$", description="按状态过滤")
    type: Optional[str] = Field(None, pattern=r"^(weixin|douyin|xiaohongshu|zhihu|bilibili|website|other)$", description="按类型过滤")