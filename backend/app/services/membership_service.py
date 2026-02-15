"""会员体系服务

提供会员权益配置、付费转化统计功能。
"""
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.system import SystemConfig
from ..models.payment import PaymentOrder, PaymentStatus
from ..models.user import User
from .quota_service import quota_service

logger = logging.getLogger(__name__)


class MembershipTier(Enum):
    """会员等级"""

    FREE = "free"
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class MembershipBenefit:
    """会员权益配置"""

    def __init__(
        self,
        tier: str,
        name: str,
        daily_ai_chat_limit: int,
        daily_document_limit: int,
        priority_support: bool = False,
        advanced_features: bool = False,
        api_access: bool = False,
        custom_branding: bool = False,
    ):
        self.tier = tier
        self.name = name
        self.daily_ai_chat_limit = daily_ai_chat_limit
        self.daily_document_limit = daily_document_limit
        self.priority_support = priority_support
        self.advanced_features = advanced_features
        self.api_access = api_access
        self.custom_branding = custom_branding


class MembershipService:
    """会员服务"""

    def __init__(self):
        self._benefits: dict[str, MembershipBenefit] = {}
        self._init_default_benefits()

    def _init_default_benefits(self):
        """初始化默认权益配置"""
        self._benefits = {
            MembershipTier.FREE.value: MembershipBenefit(
                tier=MembershipTier.FREE.value,
                name="免费用户",
                daily_ai_chat_limit=5,
                daily_document_limit=10,
                priority_support=False,
                advanced_features=False,
                api_access=False,
                custom_branding=False,
            ),
            MembershipTier.BASIC.value: MembershipBenefit(
                tier=MembershipTier.BASIC.value,
                name="基础会员",
                daily_ai_chat_limit=20,
                daily_document_limit=30,
                priority_support=False,
                advanced_features=False,
                api_access=False,
                custom_branding=False,
            ),
            MembershipTier.STANDARD.value: MembershipBenefit(
                tier=MembershipTier.STANDARD.value,
                name="标准会员",
                daily_ai_chat_limit=50,
                daily_document_limit=50,
                priority_support=True,
                advanced_features=True,
                api_access=False,
                custom_branding=False,
            ),
            MembershipTier.PREMIUM.value: MembershipBenefit(
                tier=MembershipTier.PREMIUM.value,
                name="高级会员",
                daily_ai_chat_limit=100,
                daily_document_limit=100,
                priority_support=True,
                advanced_features=True,
                api_access=True,
                custom_branding=False,
            ),
            MembershipTier.ENTERPRISE.value: MembershipBenefit(
                tier=MembershipTier.ENTERPRISE.value,
                name="企业会员",
                daily_ai_chat_limit=10**9,
                daily_document_limit=10**9,
                priority_support=True,
                advanced_features=True,
                api_access=True,
                custom_branding=True,
            ),
        }

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
                "daily_document_limit": benefit.daily_document_limit,
                "priority_support": benefit.priority_support,
                "advanced_features": benefit.advanced_features,
                "api_access": benefit.api_access,
                "custom_branding": benefit.custom_branding,
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
                "daily_document_limit": v.daily_document_limit,
                "priority_support": v.priority_support,
                "advanced_features": v.advanced_features,
                "api_access": v.api_access,
                "custom_branding": v.custom_branding,
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
        vip_expires = getattr(user, "vip_expires_at", None)
        if vip_expires and isinstance(vip_expires, datetime):
            if vip_expires.tzinfo is None:
                vip_expires = vip_expires.replace(tzinfo=timezone.utc)
            if vip_expires > datetime.now(timezone.utc):
                return MembershipTier.STANDARD.value

        vip_level = getattr(user, "vip_level", None)
        if vip_level:
            return str(vip_level)

        return MembershipTier.FREE.value

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
