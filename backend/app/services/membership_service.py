"""会员体系服务

提供会员权益配置、付费转化统计功能。
支持新的会员等级体系：
- 免费用户 (free): 基础功能
- 月度会员 (monthly): ¥29/月
- 年度会员 (annual): ¥299/年 (享8.6折)
- 终身会员 (lifetime): ¥999 (一次购买终身权益)
"""
import logging
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.system import SystemConfig
from ..models.payment import PaymentOrder, PaymentStatus
from ..models.user import User
from ..models.membership import Membership
from .quota_service import quota_service

logger = logging.getLogger(__name__)


class MembershipTier(Enum):
    """会员等级"""

    FREE = "free"
    MONTHLY = "monthly"
    ANNUAL = "annual"
    LIFETIME = "lifetime"


# 会员价格配置
MEMBERSHIP_PRICING = {
    MembershipTier.FREE.value: {
        "name": "免费用户",
        "monthly_price": 0,
        "annual_price": 0,
        "lifetime_price": 0,
    },
    MembershipTier.MONTHLY.value: {
        "name": "月度会员",
        "monthly_price": 29,
        "annual_price": 299,
        "annual_discount": 0.86,  # 8.6折
        "lifetime_price": 999,
    },
    MembershipTier.ANNUAL.value: {
        "name": "年度会员",
        "monthly_price": 29,
        "annual_price": 299,
        "annual_discount": 0.86,
        "lifetime_price": 999,
    },
    MembershipTier.LIFETIME.value: {
        "name": "终身会员",
        "monthly_price": 29,
        "annual_price": 299,
        "annual_discount": 0.86,
        "lifetime_price": 999,
    },
}


class MembershipBenefit:
    """会员权益配置"""

    def __init__(
        self,
        tier: str,
        name: str,
        daily_ai_chat_limit: int = 3,
        unlimited_ai_chat: bool = False,
        video_consultation_discount: float = 1.0,
        free_video_consultations_per_month: int = 0,
        priority_support: bool = False,
        points_multiplier: float = 1.0,
        contract_review_per_month: int = 0,
        unlimited_contract_review: bool = False,
        lawyer_consultation_discount: float = 1.0,
        can_view_lawyer_info: bool = True,
        can_read_news: bool = True,
    ):
        self.tier = tier
        self.name = name
        self.daily_ai_chat_limit = daily_ai_chat_limit
        self.unlimited_ai_chat = unlimited_ai_chat
        self.video_consultation_discount = video_consultation_discount
        self.free_video_consultations_per_month = free_video_consultations_per_month
        self.priority_support = priority_support
        self.points_multiplier = points_multiplier
        self.contract_review_per_month = contract_review_per_month
        self.unlimited_contract_review = unlimited_contract_review
        self.lawyer_consultation_discount = lawyer_consultation_discount
        self.can_view_lawyer_info = can_view_lawyer_info
        self.can_read_news = can_read_news


class MembershipService:
    """会员服务"""

    def __init__(self):
        self._benefits: dict[str, MembershipBenefit] = {}
        self._pricing: dict[str, dict] = {}
        self._init_default_benefits()
        self._init_pricing()

    def _init_pricing(self):
        """初始化价格配置"""
        self._pricing = {
            MembershipTier.FREE.value: {
                "name": "免费用户",
                "monthly_price": 0,
                "annual_price": 0,
                "lifetime_price": 0,
                "annual_discount": 0,
                "savings_annual": 0,
            },
            MembershipTier.MONTHLY.value: {
                "name": "月度会员",
                "monthly_price": 29,
                "annual_price": 299,
                "annual_discount": 0.86,
                "lifetime_price": 999,
                "savings_annual": 349 - 299,  # 月度按年计算 - 年度价格
            },
            MembershipTier.ANNUAL.value: {
                "name": "年度会员",
                "monthly_price": 29,
                "annual_price": 299,
                "annual_discount": 0.86,
                "lifetime_price": 999,
                "savings_annual": 0,
            },
            MembershipTier.LIFETIME.value: {
                "name": "终身会员",
                "monthly_price": 29,
                "annual_price": 299,
                "annual_discount": 0.86,
                "lifetime_price": 999,
                "savings_annual": 0,
            },
        }

    def _init_default_benefits(self):
        """初始化默认权益配置"""
        self._benefits = {
            # 免费用户：AI咨询3次/天、查看律师信息、阅读新闻
            MembershipTier.FREE.value: MembershipBenefit(
                tier=MembershipTier.FREE.value,
                name="免费用户",
                daily_ai_chat_limit=3,
                unlimited_ai_chat=False,
                video_consultation_discount=1.0,
                free_video_consultations_per_month=0,
                priority_support=False,
                points_multiplier=1.0,
                contract_review_per_month=0,
                unlimited_contract_review=False,
                lawyer_consultation_discount=1.0,
                can_view_lawyer_info=True,
                can_read_news=True,
            ),
            # 月度会员：无限AI咨询、视频咨询8折、专属客服、积分双倍
            MembershipTier.MONTHLY.value: MembershipBenefit(
                tier=MembershipTier.MONTHLY.value,
                name="月度会员",
                daily_ai_chat_limit=0,
                unlimited_ai_chat=True,
                video_consultation_discount=0.8,
                free_video_consultations_per_month=0,
                priority_support=True,
                points_multiplier=2.0,
                contract_review_per_month=0,
                unlimited_contract_review=False,
                lawyer_consultation_discount=1.0,
                can_view_lawyer_info=True,
                can_read_news=True,
            ),
            # 年度会员：所有月度权益 + 视频咨询免费3次、合同审查5份、律师咨询9折
            MembershipTier.ANNUAL.value: MembershipBenefit(
                tier=MembershipTier.ANNUAL.value,
                name="年度会员",
                daily_ai_chat_limit=0,
                unlimited_ai_chat=True,
                video_consultation_discount=0.0,  # 免费
                free_video_consultations_per_month=3,
                priority_support=True,
                points_multiplier=2.0,
                contract_review_per_month=5,
                unlimited_contract_review=False,
                lawyer_consultation_discount=0.9,
                can_view_lawyer_info=True,
                can_read_news=True,
            ),
            # 终身会员：所有权益 + 不限量视频咨询、不限量合同审查、律师咨询8折
            MembershipTier.LIFETIME.value: MembershipBenefit(
                tier=MembershipTier.LIFETIME.value,
                name="终身会员",
                daily_ai_chat_limit=0,
                unlimited_ai_chat=True,
                video_consultation_discount=0.0,  # 免费无限量
                free_video_consultations_per_month=999,  # 表示无限
                priority_support=True,
                points_multiplier=2.0,
                contract_review_per_month=0,
                unlimited_contract_review=True,
                lawyer_consultation_discount=0.8,
                can_view_lawyer_info=True,
                can_read_news=True,
            ),
        }

    def get_pricing(self, tier: str) -> dict[str, Any] | None:
        """获取会员价格配置

        Args:
            tier: 会员等级

        Returns:
            价格配置
        """
        return self._pricing.get(tier)

    def list_pricing(self) -> list[dict[str, Any]]:
        """列出所有会员价格配置

        Returns:
            价格配置列表
        """
        return [
            {
                "tier": k,
                "name": v["name"],
                "monthly_price": v["monthly_price"],
                "annual_price": v["annual_price"],
                "annual_discount": v.get("annual_discount", 0),
                "lifetime_price": v["lifetime_price"],
                "savings_annual": v.get("savings_annual", 0),
            }
            for k, v in self._pricing.items()
        ]

    def get_benefits(self, tier: str) -> dict[str, Any] | None:
        """获取会员权益配置

        Args:
            tier: 会员等级

        Returns:
            权益配置
        """
        benefit = self._benefits.get(tier)
        if benefit:
            return {
                "tier": benefit.tier,
                "name": benefit.name,
                "daily_ai_chat_limit": benefit.daily_ai_chat_limit,
                "unlimited_ai_chat": benefit.unlimited_ai_chat,
                "video_consultation_discount": benefit.video_consultation_discount,
                "free_video_consultations_per_month": benefit.free_video_consultations_per_month,
                "priority_support": benefit.priority_support,
                "points_multiplier": benefit.points_multiplier,
                "contract_review_per_month": benefit.contract_review_per_month,
                "unlimited_contract_review": benefit.unlimited_contract_review,
                "lawyer_consultation_discount": benefit.lawyer_consultation_discount,
                "can_view_lawyer_info": benefit.can_view_lawyer_info,
                "can_read_news": benefit.can_read_news,
            }
        return None

    def list_benefits(self) -> list[dict[str, Any]]:
        """列出所有会员权益配置

        Returns:
            权益配置列表
        """
        return [
            {
                "tier": k,
                "name": v.name,
                "daily_ai_chat_limit": v.daily_ai_chat_limit,
                "unlimited_ai_chat": v.unlimited_ai_chat,
                "video_consultation_discount": v.video_consultation_discount,
                "free_video_consultations_per_month": v.free_video_consultations_per_month,
                "priority_support": v.priority_support,
                "points_multiplier": v.points_multiplier,
                "contract_review_per_month": v.contract_review_per_month,
                "unlimited_contract_review": v.unlimited_contract_review,
                "lawyer_consultation_discount": v.lawyer_consultation_discount,
                "can_view_lawyer_info": v.can_view_lawyer_info,
                "can_read_news": v.can_read_news,
            }
            for k, v in self._benefits.items()
        ]

    async def get_user_tier(self, db: AsyncSession, user: User) -> str:
        """获取用户会员等级

        Args:
            db: 数据库会话
            user: 用户

        Returns:
            会员等级
        """
        # 查询会员表
        result = await db.execute(
            select(Membership).where(Membership.user_id == user.id)
        )
        membership = result.scalar_one_or_none()

        if membership:
            # 检查会员是否有效
            if membership.level != MembershipTier.FREE.value:
                if membership.end_date:
                    if membership.end_date.tzinfo is None:
                        membership.end_date = membership.end_date.replace(tzinfo=timezone.utc)
                    if membership.end_date > datetime.now(timezone.utc):
                        return membership.level
                else:
                    # 终身会员
                    return membership.level

        # 如果会员表没有记录或已过期，检查用户表的vip_expires_at字段作为兼容
        vip_expires = getattr(user, "vip_expires_at", None)
        if vip_expires and isinstance(vip_expires, datetime):
            if vip_expires.tzinfo is None:
                vip_expires = vip_expires.replace(tzinfo=timezone.utc)
            if vip_expires > datetime.now(timezone.utc):
                return MembershipTier.MONTHLY.value

        return MembershipTier.FREE.value

    async def get_user_membership(
        self, db: AsyncSession, user: User
    ) -> dict[str, Any]:
        """获取用户完整的会员信息

        Args:
            db: 数据库会话
            user: 用户

        Returns:
            用户会员信息
        """
        # 查询会员表
        result = await db.execute(
            select(Membership).where(Membership.user_id == user.id)
        )
        membership = result.scalar_one_or_none()

        tier = await self.get_user_tier(db, user)
        benefits = self.get_benefits(tier)
        pricing = self.get_pricing(tier)

        # 计算会员是否有效
        is_active = False
        if membership:
            if membership.level != MembershipTier.FREE.value:
                if membership.end_date:
                    if membership.end_date.tzinfo is None:
                        membership.end_date = membership.end_date.replace(tzinfo=timezone.utc)
                    if membership.end_date > datetime.now(timezone.utc):
                        is_active = True
                else:
                    # 终身会员
                    is_active = True

        return {
            "user_id": user.id,
            "level": tier,
            "level_name": pricing.get("name", "免费用户") if pricing else "免费用户",
            "start_date": membership.start_date if membership else None,
            "end_date": membership.end_date if membership else None,
            "auto_renew": membership.auto_renew if membership else False,
            "is_active": is_active,
            "created_at": membership.created_at if membership else datetime.now(timezone.utc),
            "updated_at": membership.updated_at if membership else datetime.now(timezone.utc),
            "benefits": benefits,
            "is_vip": is_active and tier != MembershipTier.FREE.value,
        }

    async def get_user_benefits(
            self, db: AsyncSession, user: User) -> dict[str, Any]:
        """获取用户权益

        Args:
            db: 数据库会话
            user: 用户

        Returns:
            用户权益信息
        """
        tier = await self.get_user_tier(db, user)
        benefits = self.get_benefits(tier)
        quota_info = await quota_service.get_today_quota(db, user)

        return {
            "tier": tier,
            "benefits": benefits,
            "quota": {
                "ai_chat": {
                    "limit": quota_info.get("ai_chat_limit"),
                    "used": quota_info.get("ai_chat_used"),
                    "remaining": quota_info.get("ai_chat_remaining"),
                },
                "document_generate": {
                    "limit": quota_info.get("document_generate_limit"),
                    "used": quota_info.get("document_generate_used"),
                    "remaining": quota_info.get("document_generate_remaining"),
                },
            },
            "is_vip": quota_info.get("is_vip_active", False),
        }

    async def create_membership(
        self,
        db: AsyncSession,
        user_id: int,
        tier: str,
        duration: str,
    ) -> Membership:
        """创建/更新会员订阅

        Args:
            db: 数据库会话
            user_id: 用户ID
            tier: 会员等级
            duration: 订阅时长 (monthly/annual/lifetime)

        Returns:
            会员记录
        """
        # 查询现有会员
        result = await db.execute(
            select(Membership).where(Membership.user_id == user_id)
        )
        membership = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        # 计算结束时间
        end_date = None
        if duration == "monthly":
            end_date = now + timedelta(days=30)
        elif duration == "annual":
            end_date = now + timedelta(days=365)
        # lifetime 为 None（终身）

        if membership:
            # 更新现有会员
            membership.level = tier
            membership.start_date = now
            membership.end_date = end_date
            membership.auto_renew = (duration == "monthly")
            membership.updated_at = now
        else:
            # 创建新会员
            membership = Membership(
                user_id=user_id,
                level=tier,
                start_date=now,
                end_date=end_date,
                auto_renew=(duration == "monthly"),
                created_at=now,
                updated_at=now,
            )
            db.add(membership)

        await db.commit()
        await db.refresh(membership)

        logger.info(f"Created/Updated membership for user {user_id}: tier={tier}, duration={duration}")

        return membership

    async def calculate_price(self, tier: str, duration: str) -> float:
        """计算会员价格

        Args:
            tier: 会员等级
            duration: 订阅时长 (monthly/annual/lifetime)

        Returns:
            价格
        """
        pricing = self._pricing.get(tier)
        if not pricing:
            return 0.0

        if duration == "monthly":
            return float(pricing["monthly_price"])
        elif duration == "annual":
            return float(pricing["annual_price"])
        elif duration == "lifetime":
            return float(pricing["lifetime_price"])

        return 0.0


class ConversionTrackingService:
    """付费转化追踪服务"""

    def __init__(self):
        self._conversion_events: list[dict[str, Any]] = []

    async def track_conversion(
        self,
        db: AsyncSession,
        user_id: int,
        order_no: str,
        amount: float,
        conversion_type: str = "purchase",
        source: str = "web",
    ) -> dict[str, Any]:
        """追踪转化事件

        Args:
            db: 数据库会话
            user_id: 用户ID
            order_no: 订单号
            amount: 金额
            conversion_type: 转化类型
            source: 来源

        Returns:
            追踪结果
        """
        event = {
            "id": f"conv_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            "user_id": user_id,
            "order_no": order_no,
            "amount": amount,
            "conversion_type": conversion_type,
            "source": source,
            "timestamp": datetime.now(
                timezone.utc).isoformat(),
        }
        self._conversion_events.append(event)

        logger.info(
            f"Conversion tracked: {conversion_type} for user {user_id}, amount: {amount}")

        return {
            "tracked": True,
            "conversion_id": event["id"],
        }

    async def get_conversion_stats(
        self,
        db: AsyncSession,
        user_id: int | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """获取转化统计

        Args:
            db: 数据库会话
            user_id: 用户ID（可选）
            days: 天数

        Returns:
            转化统计
        """
        now = datetime.now(timezone.utc)
        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)

        filtered = self._conversion_events
        if user_id is not None:
            filtered = [e for e in filtered if e.get("user_id") == user_id]

        total_amount = sum(e.get("amount", 0) for e in filtered)
        conversion_types: dict[str, int] = {}
        for e in filtered:
            ct = e.get("conversion_type", "unknown")
            conversion_types[ct] = conversion_types.get(ct, 0) + 1

        return {
            "total_conversions": len(filtered),
            "total_amount": total_amount,
            "conversion_types": conversion_types,
            "period_days": days,
        }

    async def get_revenue_stats(
        self,
        db: AsyncSession,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """获取收入统计

        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            收入统计
        """
        query = select(PaymentOrder).where(
            PaymentOrder.status == PaymentStatus.PAID)

        if start_date:
            query = query.where(PaymentOrder.paid_at >= start_date)
        if end_date:
            query = query.where(PaymentOrder.paid_at <= end_date)

        result = await db.execute(query)
        orders = result.scalars().all()

        total_revenue = sum(float(o.actual_amount or 0) for o in orders)
        order_count = len(orders)
        avg_order_value = total_revenue / order_count if order_count > 0 else 0

        by_type: dict[str, dict[str, Any]] = {}
        for o in orders:
            ot = o.order_type or "unknown"
            if ot not in by_type:
                by_type[ot] = {"count": 0, "amount": 0.0}
            by_type[ot]["count"] += 1
            by_type[ot]["amount"] += float(o.actual_amount or 0)

        return {
            "total_revenue": total_revenue,
            "order_count": order_count,
            "avg_order_value": avg_order_value,
            "by_order_type": by_type,
        }

    async def get_user_conversion_history(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """获取用户转化历史

        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页数量

        Returns:
            转化历史
        """
        query = select(PaymentOrder).where(
            PaymentOrder.user_id == user_id,
            PaymentOrder.status == PaymentStatus.PAID,
        )

        count_query = select(func.count()).select_from(query.subquery())
        total: int = int(await db.scalar(count_query) or 0)

        query = query.order_by(PaymentOrder.paid_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        orders = result.scalars().all()

        items = [
            {
                "order_no": o.order_no,
                "order_type": o.order_type,
                "amount": float(o.actual_amount or 0),
                "paid_at": o.paid_at.isoformat() if o.paid_at else None,
            }
            for o in orders
        ]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }


membership_service = MembershipService()
conversion_tracking_service = ConversionTrackingService()
