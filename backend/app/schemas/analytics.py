"""用户行为分析相关Schema"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ============ 行为日志相关 ============

class BehaviorLogRequest(BaseModel):
    """行为日志请求"""
    action: str = Field(..., description="行为类型")
    resource_type: str | None = Field(None, description="资源类型")
    resource_id: int | None = Field(None, description="资源ID")
    metadata: dict[str, Any] | None = Field(None, description="额外元数据")
    session_id: str | None = Field(None, description="会话ID")


class BehaviorLogResponse(BaseModel):
    """行为日志响应"""
    id: int
    user_id: int | None
    action: str
    resource_type: str | None
    resource_id: int | None
    metadata: str | None
    created_at: datetime


class BehaviorHistoryItem(BaseModel):
    """行为历史项"""
    id: int
    action: str
    resource_type: str | None
    resource_id: int | None
    metadata: str | None
    created_at: datetime


class BehaviorHistoryResponse(BaseModel):
    """行为历史响应"""
    user_id: int
    total: int
    items: list[BehaviorHistoryItem]


class ResourceViewCountResponse(BaseModel):
    """资源浏览次数响应"""
    resource_type: str
    resource_id: int
    view_count: int


class ActionStatisticsItem(BaseModel):
    """行为统计项"""
    action: str
    count: int


class ActionStatisticsResponse(BaseModel):
    """行为统计响应"""
    start_date: str
    end_date: str
    items: list[ActionStatisticsItem]


# ============ 转化漏斗分析相关 ============


class FunnelStepRequest(BaseModel):
    """漏斗步骤请求"""
    name: str = Field(..., description="步骤名称")
    action: str = Field(..., description="行为类型")
    resource_type: str | None = Field(None, description="资源类型")
    condition: dict[str, Any] | None = Field(None, description="额外条件")


class ConversionFunnelRequest(BaseModel):
    """转化漏斗分析请求"""
    start_date: str = Field(..., description="开始日期，格式：YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期，格式：YYYY-MM-DD")
    funnel_steps: list[FunnelStepRequest] = Field(..., description="漏斗步骤列表")


class FunnelStepResult(BaseModel):
    """漏斗步骤结果"""
    name: str
    count: int
    conversion_rate: float
    drop_rate: float


class ConversionFunnelResponse(BaseModel):
    """转化漏斗分析响应"""
    start_date: str
    end_date: str
    steps: list[FunnelStepResult]


# ============ 用户留存分析相关 ============


class RetentionRequest(BaseModel):
    """留存分析请求"""
    cohort_date: str = Field(..., description="队列日期，格式：YYYY-MM-DD")
    retention_days: list[int] = Field(default=[1, 7, 30], description="留存天数列表")


class RetentionItem(BaseModel):
    """留存项"""
    day: int
    count: int
    rate: float


class RetentionResponse(BaseModel):
    """留存分析响应"""
    cohort_date: str
    cohort_count: int
    retention: list[RetentionItem]


# ============ 商业Dashboard相关 ============


class MetricsResponse(BaseModel):
    """关键指标响应"""
    dau: int = Field(..., description="日活跃用户数")
    mau: int = Field(..., description="月活跃用户数")
    total_revenue: float = Field(..., description="总收入（元）")
    paying_users: int = Field(..., description="付费用户数")
    timestamp: str = Field(..., description="数据时间戳")


class RevenueDataPoint(BaseModel):
    """收入数据点"""
    date: str = Field(..., description="日期")
    revenue: float = Field(..., description="总收入")
    membership: float | None = Field(None, description="会员收入")
    consultation: float | None = Field(None, description="咨询收入")
    other: float | None = Field(None, description="其他收入")


class RevenueSource(BaseModel):
    """收入来源"""
    name: str = Field(..., description="来源名称")
    value: float = Field(..., description="金额")
    percentage: float = Field(..., description="占比")
    color: str = Field(..., description="颜色")


class RevenueResponse(BaseModel):
    """收入统计响应"""
    trend: list[RevenueDataPoint] = Field(..., description="收入趋势")
    sources: list[RevenueSource] = Field(..., description="收入来源分布")
    total: float = Field(..., description="总收入")


class ConversionFunnelStep(BaseModel):
    """转化漏斗步骤"""
    name: str = Field(..., description="步骤名称")
    count: int = Field(..., description="用户数量")
    conversion_rate: float = Field(..., description="转化率")
    drop_rate: float = Field(..., description="流失率")
    color: str | None = Field(None, description="颜色")


class ConversionFunnelData(BaseModel):
    """转化漏斗数据"""
    steps: list[ConversionFunnelStep] = Field(..., description="漏斗步骤")
    total_users: int = Field(..., description="总用户数")
    overall_conversion: float = Field(..., description="整体转化率")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")


class UserActivityPoint(BaseModel):
    """用户活跃度数据点"""
    date: str = Field(..., description="日期")
    active_users: int = Field(..., description="活跃用户数")
    new_users: int = Field(..., description="新用户数")
    returning_users: int = Field(..., description="回归用户数")


class FeatureUsage(BaseModel):
    """功能使用情况"""
    feature: str = Field(..., description="功能名称")
    usage_count: int = Field(..., description="使用次数")
    percentage: float = Field(..., description="使用占比")
    color: str | None = Field(None, description="颜色")


class UserBehaviorData(BaseModel):
    """用户行为数据"""
    activity_trend: list[UserActivityPoint] = Field(..., description="活跃度趋势")
    feature_usage: list[FeatureUsage] = Field(..., description="功能使用情况")
    total_sessions: int = Field(..., description="总会话数")
    average_session_duration: float = Field(..., description="平均会话时长（秒）")
