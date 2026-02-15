"""社交裂变服务 (兼容性封装)

提供邀请有礼、分享有礼等社交裂变功能。

此模块为兼容性层，实际实现已迁移到 referral_manager 模块。
"""
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .referral_manager import (
    get_referral_manager,
    create_invite_code,
    accept_invite,
    claim_invite_reward,
    get_invite_stats,
    ReferralStatus as NewReferralStatus,
    ShareChannel as NewShareChannel,
)

logger = logging.getLogger(__name__)


class ReferralStatus:
    """邀请状态 - 已迁移"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ShareChannel:
    """分享渠道 - 已迁移"""

    WECHAT = "wechat"
    WECHAT_MOMENTS = "wechat_moments"
    QRCODE = "qrcode"
    LINK = "link"


class ShareService:
    """分享服务 - 已迁移至 referral_manager"""

    def __init__(self):
        logger.warning(
            "ShareService is deprecated, use get_referral_manager() instead"
        )
        self._share_records = {}

    async def create_share_link(self, user_id: int, resource_type: str, resource_id: str) -> dict[str, Any]:
        """创建分享链接"""
        share_id = f"SHARE-{user_id}-{resource_type}-{resource_id}"
        share_link = f"https://baixing-law.com/share/{share_id}"
        self._share_records[share_id] = {
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "clicks": 0,
            "conversions": 0,
        }
        return {"share_id": share_id, "share_link": share_link}

    async def track_click(self, share_id: str) -> bool:
        """追踪点击"""
        if share_id in self._share_records:
            self._share_records[share_id]["clicks"] += 1
            return True
        return False

    async def track_conversion(self, share_id: str, user_id: int) -> dict[str, Any]:
        """追踪转化"""
        if share_id in self._share_records:
            self._share_records[share_id]["conversions"] += 1
            return {"success": True}
        return {"success": False}

    def get_share_stats(self, user_id: int) -> dict[str, Any]:
        """获取分享统计"""
        total_shares = 0
        total_clicks = 0
        total_conversions = 0
        for record in self._share_records.values():
            if record["user_id"] == user_id:
                total_shares += 1
                total_clicks += record["clicks"]
                total_conversions += record["conversions"]
        conversion_rate = f"{total_conversions / total_clicks * 100:.1f}%" if total_clicks > 0 else "0.0%"
        return {
            "total_shares": total_shares,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "conversion_rate": conversion_rate,
        }


class ReferralRewardConfig:
    """邀请奖励配置 - 已迁移"""

    def __init__(self):
        logger.warning(
            "ReferralRewardConfig is deprecated, use get_referral_manager() instead"
        )
        self._rewards = {
            "referrer": {"points": 100},
            "invitee": {"points": 50},
        }

    def get_reward(self, role: str) -> dict[str, Any]:
        """获取奖励配置"""
        return self._rewards.get(role, {"points": 0})

    def set_reward(self, role: str, points: int) -> None:
        """设置奖励配置"""
        self._rewards[role] = {"points": points}


class ReferralService:
    """邀请服务 - 已迁移至 referral_manager"""

    def __init__(self):
        logger.warning(
            "ReferralService is deprecated, use get_referral_manager() instead"
        )
        self._referrals = {}
        self._claimed_rewards = set()

    async def create_referral_code(
        self,
        user_id: int,
        expires_in_hours: int = 72,
    ) -> dict[str, Any]:
        """创建邀请码"""
        code = f"REF-{user_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self._referrals[code] = {
            "user_id": user_id,
            "status": ReferralStatus.PENDING,
            "expires_at": datetime.now(timezone.utc).timestamp() + expires_in_hours * 3600,
        }
        return {"code": code, "share_url": f"https://baixing-law.com/register?ref={code}"}

    async def accept_referral(
        self,
        code: str,
        invitee_id: int,
    ) -> dict[str, Any]:
        """接受邀请"""
        if code not in self._referrals:
            return {"success": False, "error": "邀请码不存在"}
        
        referral = self._referrals[code]
        
        if referral["status"] != ReferralStatus.PENDING:
            return {"success": False, "error": "邀请码已被使用"}
        
        if datetime.now(timezone.utc).timestamp() > referral["expires_at"]:
            return {"success": False, "error": "邀请码已过期"}
        
        referral["status"] = ReferralStatus.ACCEPTED
        referral["invitee_id"] = invitee_id
        return {"success": True, "referrer_id": referral["user_id"]}

    async def claim_reward(
        self,
        user_id: int,
        code: str,
    ) -> dict[str, Any]:
        """领取奖励"""
        if code not in self._referrals:
            return {"success": False, "error": "邀请码不存在"}
        
        referral = self._referrals[code]
        
        if referral["user_id"] != user_id:
            return {"success": False, "error": "无权限领取此奖励"}
        
        if referral["status"] != ReferralStatus.ACCEPTED:
            return {"success": False, "error": "邀请未被接受"}
        
        reward_key = f"{user_id}-{code}"
        if reward_key in self._claimed_rewards:
            return {"success": False, "error": "奖励已领取"}
        
        self._claimed_rewards.add(reward_key)
        return {"success": True, "reward": {"points": 100}}

    def get_referral_stats(self, user_id: int) -> dict[str, Any]:
        """获取推荐统计"""
        total_codes = 0
        accepted = 0
        pending = 0
        for referral in self._referrals.values():
            if referral["user_id"] == user_id:
                total_codes += 1
                if referral["status"] == ReferralStatus.ACCEPTED:
                    accepted += 1
                elif referral["status"] == ReferralStatus.PENDING:
                    pending += 1
        success_rate = f"{accepted / total_codes * 100:.1f}%" if total_codes > 0 else "0.0%"
        return {
            "total_codes": total_codes,
            "accepted": accepted,
            "pending": pending,
            "success_rate": success_rate,
        }


def get_referral_service() -> ReferralService:
    """获取推荐服务（兼容）"""
    return ReferralService()


async def create_referral_code(
    user_id: int,
    expires_in_hours: int = 72,
) -> dict[str, Any]:
    """便捷函数：创建邀请码 - 已弃用"""
    logger.warning("create_referral_code is deprecated, use create_invite_code instead")
    return {"deprecated": True, "message": "请使用新接口"}


async def accept_referral(code: str, invitee_id: int) -> dict[str, Any]:
    """便捷函数：接受邀请 - 已弃用"""
    logger.warning("accept_referral is deprecated")
    return {"deprecated": True, "message": "请使用新接口"}
