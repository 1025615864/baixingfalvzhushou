"""邀请裂变服务测试"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.referral_service import ReferralService, referral_service


class TestReferralService:
    @pytest.fixture
    def service(self):
        return ReferralService()

    @pytest.mark.asyncio
    async def test_generate_invite_code(self, service):
        with patch("app.services.referral_service.secrets.token_urlsafe") as mock_token:
            mock_token.return_value = "abcd1234efgh"
            code = await service.generate_invite_code(
                AsyncMock(spec=AsyncSession),
                user_id=1,
            )

        # 邀请码现在包含前缀 "REF-"
        assert code == "REF-ABCD1234"
        assert len(code) == 12

    @pytest.mark.asyncio
    async def test_get_invite_stats(self, service):
        stats = await service.get_invite_stats(
            AsyncMock(spec=AsyncSession),
            user_id=1,
        )
        assert stats["total_invites"] == 0
        assert stats["successful_invites"] == 0
        assert stats["conversion_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_invite_history(self, service):
        history = await service.get_invite_history(
            AsyncMock(spec=AsyncSession),
            user_id=1,
            page=2,
            page_size=20,
        )
        assert history["items"] == []
        assert history["page"] == 2
        assert history["page_size"] == 20

    @pytest.mark.asyncio
    async def test_claim_reward(self, service):
        result = await service.claim_reward(
            AsyncMock(spec=AsyncSession),
            user_id=1,
            invite_code="INV123",
        )
        assert result["success"] is True
        assert result["reward_points"] == 100
        assert "奖励" in result["message"]

    @pytest.mark.asyncio
    async def test_get_analytics(self, service):
        analytics = await service.get_analytics(
            AsyncMock(spec=AsyncSession),
            user_id=1,
        )
        assert "daily_invites" in analytics
        assert "conversion_trend" in analytics
        assert "top_channels" in analytics

    @pytest.mark.asyncio
    async def test_get_ranking(self, service):
        ranking = await service.get_ranking(
            AsyncMock(spec=AsyncSession),
            limit=10,
        )
        assert "ranking" in ranking
        assert ranking["total_participants"] == 0

    def test_referral_service_singleton(self):
        assert referral_service is referral_service
