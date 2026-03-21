"""会员体系服务测试"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.membership_service import (
    MembershipService,
    MembershipTier,
    membership_service,
    ConversionTrackingService,
    conversion_tracking_service,
)
from app.models.payment import PaymentOrder, PaymentStatus
from app.models.user import User


class TestMembershipService:
    @pytest.fixture
    def service(self):
        return MembershipService()

    def test_get_benefits(self, service):
        benefits = service.get_benefits(MembershipTier.FREE.value)
        assert benefits is not None
        assert benefits["tier"] == MembershipTier.FREE.value
        assert benefits["daily_ai_chat_limit"] == 3

    def test_get_benefits_unknown(self, service):
        assert service.get_benefits("unknown") is None

    def test_list_benefits(self, service):
        benefits = service.list_benefits()
        tiers = {b["tier"] for b in benefits}
        assert MembershipTier.FREE.value in tiers
        assert MembershipTier.MONTHLY.value in tiers

    @pytest.mark.asyncio
    async def test_get_user_tier_with_vip_expires(self, service, db):
        user = MagicMock(spec=User)
        user.id = 1
        user.vip_expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        user.vip_level = None

        # Mock 数据库查询返回 None（无会员记录）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        tier = await service.get_user_tier(db, user)
        assert tier == MembershipTier.MONTHLY.value

    @pytest.mark.asyncio
    async def test_get_user_tier_with_vip_level(self, service, db):
        user = MagicMock(spec=User)
        user.id = 1
        user.vip_expires_at = None
        user.vip_level = MembershipTier.ANNUAL.value

        # Mock 数据库查询返回 None（无会员记录）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        tier = await service.get_user_tier(db, user)
        assert tier == MembershipTier.ANNUAL.value

    @pytest.mark.asyncio
    async def test_get_user_tier_free(self, service, db):
        user = MagicMock(spec=User)
        user.id = 1
        user.vip_expires_at = None
        user.vip_level = None

        # Mock 数据库查询返回 None（无会员记录）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        tier = await service.get_user_tier(db, user)
        assert tier == MembershipTier.FREE.value

    @pytest.mark.asyncio
    async def test_get_user_benefits(self, service, db, monkeypatch):
        quota_info = {
            "ai_chat_limit": 5,
            "ai_chat_used": 1,
            "ai_chat_remaining": 4,
            "document_generate_limit": 10,
            "document_generate_used": 2,
            "document_generate_remaining": 8,
            "is_vip_active": True,
        }

        async def fake_quota(_db, _user):
            return quota_info

        monkeypatch.setattr(
            "app.services.membership_service.quota_service.get_today_quota",
            fake_quota,
        )

        user = MagicMock(spec=User)
        user.id = 1
        user.vip_expires_at = None
        user.vip_level = MembershipTier.MONTHLY.value

        # Mock 数据库查询返回 None（无会员记录）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_user_benefits(db, user)
        assert result["tier"] == MembershipTier.MONTHLY.value
        assert result["quota"]["ai_chat"]["limit"] == 5
        assert result["is_vip"] is True

    def test_membership_service_singleton(self):
        assert membership_service is membership_service


class TestConversionTrackingService:
    @pytest.fixture
    def service(self):
        return ConversionTrackingService()

    @pytest.mark.asyncio
    async def test_track_conversion(self, service):
        result = await service.track_conversion(
            AsyncMock(spec=AsyncSession),
            user_id=1,
            order_no="ORD1",
            amount=99.0,
            conversion_type="purchase",
            source="web",
        )
        assert result["tracked"] is True
        assert result["conversion_id"].startswith("conv_")
        assert len(service._conversion_events) == 1

    @pytest.mark.asyncio
    async def test_get_conversion_stats(self, service):
        await service.track_conversion(
            AsyncMock(spec=AsyncSession),
            user_id=1,
            order_no="ORD1",
            amount=50.0,
            conversion_type="purchase",
        )
        await service.track_conversion(
            AsyncMock(spec=AsyncSession),
            user_id=2,
            order_no="ORD2",
            amount=100.0,
            conversion_type="upgrade",
        )

        stats = await service.get_conversion_stats(AsyncMock(spec=AsyncSession))
        assert stats["total_conversions"] == 2
        assert stats["total_amount"] == 150.0
        assert stats["conversion_types"]["purchase"] == 1
        assert stats["conversion_types"]["upgrade"] == 1

    @pytest.mark.asyncio
    async def test_get_revenue_stats(self, service):
        order_a = MagicMock(spec=PaymentOrder)
        order_a.actual_amount = 50
        order_a.order_type = "ai_pack"
        order_a.paid_at = datetime.now(timezone.utc)
        order_a.status = PaymentStatus.PAID

        order_b = MagicMock(spec=PaymentOrder)
        order_b.actual_amount = 100
        order_b.order_type = "vip"
        order_b.paid_at = datetime.now(timezone.utc)
        order_b.status = PaymentStatus.PAID

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [order_a, order_b]
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)

        stats = await service.get_revenue_stats(mock_db)
        assert stats["total_revenue"] == 150.0
        assert stats["order_count"] == 2
        assert stats["by_order_type"]["vip"]["count"] == 1

    @pytest.mark.asyncio
    async def test_get_user_conversion_history(self, service):
        order_a = MagicMock(spec=PaymentOrder)
        order_a.order_no = "ORD1"
        order_a.order_type = "vip"
        order_a.actual_amount = 50
        order_a.paid_at = datetime.now(timezone.utc)
        order_a.status = PaymentStatus.PAID

        order_b = MagicMock(spec=PaymentOrder)
        order_b.order_no = "ORD2"
        order_b.order_type = "ai_pack"
        order_b.actual_amount = 100
        order_b.paid_at = datetime.now(timezone.utc)
        order_b.status = PaymentStatus.PAID

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [order_a, order_b]

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.scalar = AsyncMock(return_value=2)

        result = await service.get_user_conversion_history(mock_db, user_id=1)
        assert result["total"] == 2
        assert result["page"] == 1
        assert len(result["items"]) == 2

    def test_conversion_tracking_service_singleton(self):
        assert conversion_tracking_service is conversion_tracking_service


class TestMembershipBenefit:
    """会员权益配置测试"""

    def test_membership_benefit_initialization(self):
        """测试会员权益初始化"""
        from app.services.membership_service import MembershipBenefit
        
        benefit = MembershipBenefit(
            tier="test",
            name="测试会员",
            daily_ai_chat_limit=10,
            video_consultation_discount=0.5,
            free_video_consultations_per_month=5,
        )
        
        assert benefit.tier == "test"
        assert benefit.name == "测试会员"
        assert benefit.daily_ai_chat_limit == 10
        assert benefit.video_consultation_discount == 0.5
        assert benefit.free_video_consultations_per_month == 5


class TestMembershipPricing:
    """会员价格配置测试"""

    def test_get_pricing(self):
        """测试获取会员价格"""
        from app.services.membership_service import membership_service
        
        pricing = membership_service.get_pricing("monthly")
        
        assert pricing is not None
        assert pricing["name"] == "月度会员"
        assert pricing["monthly_price"] == 29
        assert pricing["annual_price"] == 299
        assert pricing["lifetime_price"] == 999

    def test_get_pricing_unknown(self):
        """测试获取未知会员价格"""
        from app.services.membership_service import membership_service
        
        pricing = membership_service.get_pricing("unknown")
        
        assert pricing is None

    def test_list_pricing(self):
        """测试列出所有会员价格"""
        from app.services.membership_service import membership_service
        
        pricing_list = membership_service.list_pricing()
        
        assert len(pricing_list) == 4  # free, monthly, annual, lifetime
        
        tier_names = [p["tier"] for p in pricing_list]
        assert "free" in tier_names
        assert "monthly" in tier_names
        assert "annual" in tier_names
        assert "lifetime" in tier_names


class TestMembershipServiceCreate:
    """会员创建测试"""

    @pytest.mark.asyncio
    async def test_create_membership_monthly(self):
        """测试创建月度会员"""
        from app.services.membership_service import membership_service
        from app.models.membership import Membership
        
        mock_membership = MagicMock(spec=Membership)
        mock_membership.user_id = 1
        mock_membership.level = "monthly"
        mock_membership.start_date = datetime.now(timezone.utc)
        mock_membership.end_date = datetime.now(timezone.utc) + timedelta(days=30)
        mock_membership.auto_renew = True
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with patch.object(mock_db, 'commit', AsyncMock()):
            with patch.object(mock_db, 'refresh', AsyncMock()):
                result = await membership_service.create_membership(
                    mock_db, user_id=1, tier="monthly", duration="monthly"
                )
        
        assert result is not None
        assert result.level == "monthly"

    @pytest.mark.asyncio
    async def test_create_membership_annual(self):
        """测试创建年度会员"""
        from app.services.membership_service import membership_service
        from app.models.membership import Membership
        
        mock_membership = MagicMock(spec=Membership)
        mock_membership.user_id = 1
        mock_membership.level = "annual"
        mock_membership.start_date = datetime.now(timezone.utc)
        mock_membership.end_date = datetime.now(timezone.utc) + timedelta(days=365)
        mock_membership.auto_renew = False
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with patch.object(mock_db, 'commit', AsyncMock()):
            with patch.object(mock_db, 'refresh', AsyncMock()):
                result = await membership_service.create_membership(
                    mock_db, user_id=1, tier="annual", duration="annual"
                )
        
        assert result is not None
        assert result.level == "annual"

    @pytest.mark.asyncio
    async def test_create_membership_lifetime(self):
        """测试创建终身会员"""
        from app.services.membership_service import membership_service
        from app.models.membership import Membership
        
        mock_membership = MagicMock(spec=Membership)
        mock_membership.user_id = 1
        mock_membership.level = "lifetime"
        mock_membership.start_date = datetime.now(timezone.utc)
        mock_membership.end_date = None  # 终身会员无结束日期
        mock_membership.auto_renew = False
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with patch.object(mock_db, 'commit', AsyncMock()):
            with patch.object(mock_db, 'refresh', AsyncMock()):
                result = await membership_service.create_membership(
                    mock_db, user_id=1, tier="lifetime", duration="lifetime"
                )
        
        assert result is not None
        assert result.level == "lifetime"
        assert result.end_date is None

    @pytest.mark.asyncio
    async def test_create_membership_update_existing(self):
        """测试更新现有会员"""
        from app.services.membership_service import membership_service
        from app.models.membership import Membership
        
        existing_membership = MagicMock(spec=Membership)
        existing_membership.user_id = 1
        existing_membership.level = "free"
        existing_membership.start_date = datetime.now(timezone.utc) - timedelta(days=30)
        existing_membership.end_date = datetime.now(timezone.utc)
        existing_membership.auto_renew = False
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_membership
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with patch.object(mock_db, 'commit', AsyncMock()):
            with patch.object(mock_db, 'refresh', AsyncMock()):
                result = await membership_service.create_membership(
                    mock_db, user_id=1, tier="annual", duration="annual"
                )
        
        assert result is not None
        assert result.level == "annual"  # 应更新为新等级


class TestMembershipServiceCalculatePrice:
    """会员价格计算测试"""

    @pytest.mark.asyncio
    async def test_calculate_price_monthly(self):
        """测试计算月度会员价格"""
        from app.services.membership_service import membership_service
        
        price = await membership_service.calculate_price("monthly", "monthly")
        
        assert price == 29.0

    @pytest.mark.asyncio
    async def test_calculate_price_annual(self):
        """测试计算年度会员价格"""
        from app.services.membership_service import membership_service
        
        price = await membership_service.calculate_price("annual", "annual")
        
        assert price == 299.0

    @pytest.mark.asyncio
    async def test_calculate_price_lifetime(self):
        """测试计算终身会员价格"""
        from app.services.membership_service import membership_service
        
        price = await membership_service.calculate_price("lifetime", "lifetime")
        
        assert price == 999.0

    @pytest.mark.asyncio
    async def test_calculate_price_unknown_tier(self):
        """测试计算未知会员价格"""
        from app.services.membership_service import membership_service
        
        price = await membership_service.calculate_price("unknown", "monthly")
        
        assert price == 0.0


class TestConversionTrackingServiceExtended:
    """转化追踪服务扩展测试"""

    @pytest.mark.asyncio
    async def test_track_conversion_with_source(self):
        """测试追踪转化事件（带来源）"""
        from app.services.membership_service import conversion_tracking_service
        
        result = await conversion_tracking_service.track_conversion(
            AsyncMock(spec=AsyncSession),
            user_id=1,
            order_no="ORD001",
            amount=299.0,
            conversion_type="upgrade",
            source="mobile",
        )
        
        assert result["tracked"] is True
        assert result["conversion_id"].startswith("conv_")

    @pytest.mark.asyncio
    async def test_get_conversion_stats_with_user_filter(self):
        """测试获取转化统计（带用户过滤）"""
        from app.services.membership_service import conversion_tracking_service
        
        # 先添加一些数据
        await conversion_tracking_service.track_conversion(
            AsyncMock(spec=AsyncSession),
            user_id=1,
            order_no="ORD001",
            amount=100.0,
            conversion_type="purchase",
        )
        await conversion_tracking_service.track_conversion(
            AsyncMock(spec=AsyncSession),
            user_id=2,
            order_no="ORD002",
            amount=200.0,
            conversion_type="purchase",
        )
        
        # 获取用户 1 的统计
        stats = await conversion_tracking_service.get_conversion_stats(
            AsyncMock(spec=AsyncSession), user_id=1
        )
        
        assert stats["total_conversions"] == 1
        assert stats["total_amount"] == 100.0

    @pytest.mark.asyncio
    async def test_get_revenue_stats_with_date_range(self):
        """测试获取收入统计（带日期范围）"""
        from app.services.membership_service import conversion_tracking_service
        from app.models.payment import PaymentOrder, PaymentStatus
        
        order_a = MagicMock(spec=PaymentOrder)
        order_a.actual_amount = 50
        order_a.order_type = "vip"
        order_a.paid_at = datetime.now(timezone.utc)
        order_a.status = PaymentStatus.PAID
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [order_a]
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)
        
        stats = await conversion_tracking_service.get_revenue_stats(
            mock_db, start_date=start_date, end_date=end_date
        )
        
        assert stats["total_revenue"] == 50.0
        assert stats["order_count"] == 1
