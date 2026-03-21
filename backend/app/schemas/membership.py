"""会员系统 Schema

定义会员相关的请求和响应模型。
"""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# ==================== 会员等级枚举 ====================

class MembershipLevel(str):
    """会员等级"""
    FREE = "free"        # 免费用户
    MONTHLY = "monthly"  # 月度会员
    ANNUAL = "annual"    # 年度会员
    LIFETIME = "lifetime"  # 终身会员


# ==================== 会员权益配置 ====================

class MembershipBenefits(BaseModel):
    """会员权益配置"""
    tier: str = Field(..., description="会员等级")
    name: str = Field(..., description="等级名称")
    price_monthly: float = Field(..., description="月度价格(元)")
    price_annual: float = Field(..., description="年度价格(元)")
    price_lifetime: float = Field(..., description="终身价格(元)")
    
    # AI咨询相关
    daily_ai_chat_limit: int = Field(..., description="每日AI咨询次数限制")
    unlimited_ai_chat: bool = Field(default=False, description="是否无限AI咨询")
    
    # 视频咨询相关
    video_consultation_discount: float = Field(default=1.0, description="视频咨询折扣")
    free_video_consultations_per_month: int = Field(default=0, description="每月免费视频咨询次数")
    
    # 客服相关
    priority_support: bool = Field(default=False, description="是否专属客服")
    
    # 积分相关
    points_multiplier: float = Field(default=1.0, description="积分倍数")
    
    # 合同审查相关
    contract_review_per_month: int = Field(default=0, description="每月合同审查次数")
    unlimited_contract_review: bool = Field(default=False, description="是否不限量合同审查")
    
    # 律师咨询折扣
    lawyer_consultation_discount: float = Field(default=1.0, description="律师咨询折扣")


class MembershipPricing(BaseModel):
    """会员价格信息"""
    tier: str = Field(..., description="会员等级")
    name: str = Field(..., description="等级名称")
    monthly_price: float = Field(..., description="月度价格")
    annual_price: float = Field(..., description="年度价格")
    annual_discount: float = Field(..., description="年度折扣比例")
    lifetime_price: float = Field(..., description="终身价格")
    savings_annual: float = Field(..., description="年度节省金额")


# ==================== 用户会员信息 ====================

class UserMembership(BaseModel):
    """用户会员信息"""
    user_id: int = Field(..., description="用户ID")
    level: str = Field(..., description="当前会员等级")
    level_name: str = Field(..., description="等级名称")
    start_date: datetime | None = Field(default=None, description="会员开始时间")
    end_date: datetime | None = Field(default=None, description="会员结束时间(终身会员为null)")
    auto_renew: bool = Field(default=False, description="是否自动续费")
    is_active: bool = Field(default=False, description="会员是否有效")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class UserMembershipResponse(BaseModel):
    """用户会员信息响应"""
    membership: UserMembership
    benefits: MembershipBenefits | None = None
    quota: dict[str, Any] = Field(default_factory=dict)
    is_vip: bool = Field(default=False, description="是否是付费会员")


# ==================== 会员订单 ====================

class CreateMembershipOrderRequest(BaseModel):
    """创建会员订单请求"""
    tier: str = Field(..., description="会员等级")
    duration: str = Field(..., description="订阅时长: monthly/annual/lifetime")
    payment_method: str = Field(default="alipay", description="支付方式: alipay/wechat")


class MembershipOrder(BaseModel):
    """会员订单"""
    id: int = Field(..., description="订单ID")
    order_no: str = Field(..., description="订单号")
    user_id: int = Field(..., description="用户ID")
    tier: str = Field(..., description="会员等级")
    duration: str = Field(..., description="订阅时长")
    amount: float = Field(..., description="金额")
    payment_method: str | None = Field(default=None, description="支付方式")
    status: str = Field(..., description="订单状态: pending/paid/cancelled/refunded")
    created_at: datetime = Field(..., description="创建时间")
    paid_at: datetime | None = Field(default=None, description="支付时间")
    expires_at: datetime | None = Field(default=None, description="到期时间")

    class Config:
        from_attributes = True


class CreateMembershipOrderResponse(BaseModel):
    """创建会员订单响应"""
    order: MembershipOrder
    payment_url: str | None = Field(default=None, description="支付链接")


class UpgradeMembershipRequest(BaseModel):
    """升级会员请求"""
    tier: str = Field(..., description="目标会员等级")
    duration: str = Field(..., description="订阅时长: monthly/annual/lifetime")


class UpgradeMembershipResponse(BaseModel):
    """升级会员响应"""
    success: bool = Field(..., description="是否成功")
    order: MembershipOrder
    payment_url: str | None = Field(default=None, description="支付链接")


# ==================== 转化统计 ====================

class ConversionStats(BaseModel):
    """转化统计"""
    total_conversions: int = Field(default=0, description="总转化数")
    total_amount: float = Field(default=0.0, description="总金额")
    conversion_types: dict[str, int] = Field(default_factory=dict, description="转化类型统计")
    period_days: int = Field(default=30, description="统计周期(天)")


class RevenueStats(BaseModel):
    """收入统计"""
    total_revenue: float = Field(default=0.0, description="总收入")
    order_count: int = Field(default=0, description="订单数")
    avg_order_value: float = Field(default=0.0, description="平均订单金额")
    by_order_type: dict[str, dict[str, float]] = Field(default_factory=dict, description="按类型统计")


class ConversionHistoryItem(BaseModel):
    """转化历史项"""
    order_no: str = Field(..., description="订单号")
    order_type: str | None = Field(default=None, description="订单类型")
    amount: float = Field(..., description="金额")
    paid_at: str | None = Field(default=None, description="支付时间")


class ConversionHistoryResponse(BaseModel):
    """转化历史响应"""
    items: list[ConversionHistoryItem] = Field(default_factory=list)
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="页码")
    page_size: int = Field(default=20, description="每页数量")


# ==================== 响应模型 ====================

class MembershipInfoResponse(BaseModel):
    """获取会员信息响应"""
    membership: UserMembership


class MembershipLevelsResponse(BaseModel):
    """获取会员等级列表响应"""
    levels: list[MembershipPricing]
    benefits: list[MembershipBenefits]


class MembershipBenefitsResponse(BaseModel):
    """获取会员权益响应"""
    benefits: MembershipBenefits