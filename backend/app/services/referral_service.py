"""邀请裂变服务 (兼容性封装)

提供邀请码生成、邀请统计、奖励领取等功能。

此模块为兼容性层，实际实现已迁移到 referral_manager 模块。
"""
import secrets
from datetime import datetime
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .referral_manager import get_referral_manager

logger = __import__("logging").getLogger(__name__)


class ReferralService:
    """邀请服务 - 已迁移至 referral_manager"""

    def __init__(self):
        logger.warning(
            "ReferralService in referral_service.py is deprecated, "
            "use referral_manager.get_referral_manager() instead"
        )

    async def generate_invite_code(self, db: AsyncSession, user_id: int) -> str:
        manager = get_referral_manager()
        result = await manager.create_invite_code(db, user_id)
        return result.get("code", "")

    async def get_invite_stats(self, db: AsyncSession, user_id: int) -> dict[str, Any]:
        manager = get_referral_manager()
        return await manager.get_invite_stats(db, user_id)

    async def get_invite_history(
        self, db: AsyncSession, user_id: int, page: int, page_size: int
    ) -> dict[str, Any]:
        manager = get_referral_manager()
        return await manager.get_invite_history(db, user_id, page, page_size)

    async def claim_reward(self, db: AsyncSession, user_id: int, invite_code: str) -> dict[str, Any]:
        manager = get_referral_manager()
        return await manager.claim_reward(db, user_id, invite_code)

    async def get_analytics(self, db: AsyncSession, user_id: int) -> dict[str, Any]:
        manager = get_referral_manager()
        return await manager.get_analytics(db, user_id)

    async def get_ranking(self, db: AsyncSession, limit: int) -> dict[str, Any]:
        manager = get_referral_manager()
        return await manager.get_ranking(db, limit)


referral_service = ReferralService()
