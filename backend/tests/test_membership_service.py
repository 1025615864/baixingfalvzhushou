"""会员体系服务测试"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

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
        assert benefits["daily_ai_chat_limit"] == 5

    def test_get_benefits_unknown(self, service):
        assert service.get_benefits("unknown") is None

    def test_list_benefits(self, service):
        benefits = service.list_benefits()
        tiers = {b["tier"] for b in benefits}
        assert MembershipTier.FREE.value in tiers
        assert MembershipTier.ENTERPRISE.value in tiers

    @pytest.mark.asyncio
    async def test_get_user_tier_with_vip_expires(self, service):
        user = MagicMock(spec=User)
        user.vip_expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        user.vip_level = None

        tier = await service.get_user_tier(AsyncMock(spec=AsyncSession), user)
        assert tier == MembershipTier.STANDARD.value

    @pytest.mark.asyncio
    async def test_get_user_tier_with_vip_level(self, service):
        user = MagicMock(spec=User)
        user.vip_expires_at = None
        user.vip_level = MembershipTier.PREMIUM.value

        tier = await service.get_user_tier(AsyncMock(spec=AsyncSession), user)
        assert tier == MembershipTier.PREMIUM.value

    @pytest.mark.asyncio
    async def test_get_user_tier_free(self, service):
        user = MagicMock(spec=User)
        user.vip_expires_at = None
        user.vip_level = None

        tier = await service.get_user_tier(AsyncMock(spec=AsyncSession), user)
        assert tier == MembershipTier.FREE.value

    @pytest.mark.asyncio
    async def test_get_user_benefits(self, service, monkeypatch):
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
        user.vip_expires_at = None
        user.vip_level = MembershipTier.BASIC.value

        result = await service.get_user_benefits(AsyncMock(spec=AsyncSession), user)
        assert result["tier"] == MembershipTier.BASIC.value
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
