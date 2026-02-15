import pytest
from app.services.referral import (
    ReferralService,
    ReferralStatus,
    ShareService,
    ReferralRewardConfig,
)
import time

@pytest.mark.asyncio
class TestReferralService:
    async def test_create_referral_code(self):
        service = ReferralService()
        result = await service.create_referral_code(user_id=1, expires_in_hours=1)
        
        assert result["code"].startswith("REF-")
        assert "share_url" in result
        
        # Verify stored state
        code = result["code"]
        assert code in service._referrals
        assert service._referrals[code]["user_id"] == 1
        assert service._referrals[code]["status"] == ReferralStatus.PENDING

    async def test_accept_referral_flow(self):
        service = ReferralService()
        # Create code by user 1
        res = await service.create_referral_code(1)
        code = res["code"]
        
        # Accept by user 2
        accept_res = await service.accept_referral(code, invitee_id=2)
        assert accept_res["success"] is True
        assert accept_res["referrer_id"] == 1
        
        # Verify status
        ref = service._referrals[code]
        assert ref["status"] == ReferralStatus.ACCEPTED
        assert ref["invitee_id"] == 2

    async def test_accept_referral_errors(self):
        service = ReferralService()
        await service.create_referral_code(1)
        
        # Invalid code
        res1 = await service.accept_referral("INVALID", 2)
        assert res1["success"] is False
        assert res1["error"] == "邀请码不存在"
        
        # Expired code (mock time or set low expiry? set low expiry)
        res_exp = await service.create_referral_code(1, expires_in_hours=-1) # Already expired
        code_exp = res_exp["code"]
        res2 = await service.accept_referral(code_exp, 2)
        assert res2["success"] is False
        assert "过期" in res2["error"]

    async def test_claim_reward(self):
        service = ReferralService()
        res = await service.create_referral_code(1)
        code = res["code"]
        
        # Try claim before accept
        wrong = await service.claim_reward(1, code)
        assert wrong["success"] is False
        
        # Accept
        await service.accept_referral(code, 2)
        
        # Valid claim
        claim = await service.claim_reward(1, code)
        assert claim["success"] is True
        assert "points" in claim["reward"]
        
        # Double claim
        claim2 = await service.claim_reward(1, code)
        assert claim2["success"] is False
        assert claim2["error"] == "奖励已领取"

    def test_get_referral_stats(self):
        service = ReferralService()
        # Mock referrals directly for stats
        service._referrals = {
            "c1": {"user_id": 1, "status": ReferralStatus.ACCEPTED},
            "c2": {"user_id": 1, "status": ReferralStatus.PENDING},
            "c3": {"user_id": 2, "status": ReferralStatus.PENDING}, # Other user
        }
        
        stats = service.get_referral_stats(1)
        assert stats["total_codes"] == 2
        assert stats["accepted"] == 1
        assert stats["pending"] == 1
        assert stats["success_rate"] == "50.0%"

@pytest.mark.asyncio
class TestShareService:
    async def test_create_share_link(self):
        service = ShareService()
        res = await service.create_share_link(1, "article", "123")
        
        assert res["share_id"].startswith("SHARE-")
        assert "baixing-law.com/share/" in res["share_link"]
        assert len(service._share_records) == 1

    async def test_track_click_and_conversion(self):
        service = ShareService()
        res = await service.create_share_link(1, "a", "1")
        sid = res["share_id"]
        
        # Track click
        assert await service.track_click(sid) is True
        assert await service.track_click(sid) is True
        
        # Track conversion
        conv = await service.track_conversion(sid, 2)
        assert conv["success"] is True
        
        # Stats
        stats = service.get_share_stats(1)
        assert stats["total_shares"] == 1
        assert stats["total_clicks"] == 2
        assert stats["total_conversions"] == 1
        assert stats["conversion_rate"] == "50.0%"

class TestReferralRewardConfig:
    def test_config(self):
        config = ReferralRewardConfig()
        reward = config.get_reward("referrer")
        assert reward["points"] == 100
        
        config.set_reward("referrer", points=200)
        assert config.get_reward("referrer")["points"] == 200
