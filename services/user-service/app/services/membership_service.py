"""会员服务 - 会员等级管理"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models import User
from ..config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class MembershipTier:
    """会员等级定义"""
    FREE = "free"
    VIP = "vip"
    SVIP = "svip"
    ADMIN = "admin"


class MembershipService:
    """会员服务"""

    TIER_PERMISSIONS = {
        MembershipTier.FREE: {
            "ai_sessions": 5,
            "ai_messages_per_day": 20,
            "file_uploads": 2,
            "storage_mb": 100,
            "export_enabled": False,
        },
        MembershipTier.VIP: {
            "ai_sessions": 50,
            "ai_messages_per_day": 200,
            "file_uploads": 20,
            "storage_mb": 1024,
            "export_enabled": True,
        },
        MembershipTier.SVIP: {
            "ai_sessions": -1,
            "ai_messages_per_day": -1,
            "file_uploads": -1,
            "storage_mb": 10240,
            "export_enabled": True,
        },
        MembershipTier.ADMIN: {
            "ai_sessions": -1,
            "ai_messages_per_day": -1,
            "file_uploads": -1,
            "storage_mb": -1,
            "export_enabled": True,
        },
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_tier(self, user: User) -> str:
        """获取用户会员等级"""
        if user.role == "admin":
            return MembershipTier.ADMIN

        if user.vip_expires_at and user.vip_expires_at > datetime.now(timezone.utc):
            if user.role == "svip":
                return MembershipTier.SVIP
            return MembershipTier.VIP

        return MembershipTier.FREE

    def is_vip(self, user: User) -> bool:
        """检查用户是否是VIP会员"""
        tier = self.get_tier(user)
        return tier in (MembershipTier.VIP, MembershipTier.SVIP, MembershipTier.ADMIN)

    def get_permissions(self, user: User) -> dict:
        """获取用户权限"""
        tier = self.get_tier(user)
        return self.TIER_PERMISSIONS.get(tier, self.TIER_PERMISSIONS[MembershipTier.FREE])

    def get_vip_remaining_days(self, user: User) -> int:
        """获取VIP剩余天数"""
        if not user.vip_expires_at:
            return 0
        if user.vip_expires_at <= datetime.now(timezone.utc):
            return 0
        delta = user.vip_expires_at - datetime.now(timezone.utc)
        return delta.days

    async def upgrade_to_vip(self, user_id: int, days: int, tier: str = MembershipTier.VIP) -> bool:
        """升级用户到VIP

        Args:
            user_id: 用户ID
            days: 升级天数
            tier: 会员等级 (vip/svip)
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False

        old_level = self.get_tier(user)
        now = datetime.now(timezone.utc)
        if user.vip_expires_at and user.vip_expires_at > now:
            user.vip_expires_at = user.vip_expires_at + timedelta(days=days)
        else:
            user.vip_expires_at = now + timedelta(days=days)

        user.role = tier
        await self.db.commit()
        logger.info(f"User {user_id} upgraded to {tier} for {days} days")

        try:
            from ..events.kafka_producer import publish_membership_upgraded
            await publish_membership_upgraded(
                user_id=str(user_id),
                old_level=old_level,
                new_level=tier,
                expire_at=user.vip_expires_at.isoformat() if user.vip_expires_at else None,
            )
        except Exception as e:
            logger.warning(f"Failed to publish membership upgraded event: {e}")

        return True

    async def cancel_vip(self, user_id: int) -> bool:
        """取消用户VIP会员资格"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False

        old_level = self.get_tier(user)
        user.vip_expires_at = datetime.now(timezone.utc)
        user.role = "user"
        await self.db.commit()
        logger.info(f"User {user_id} VIP cancelled")

        try:
            from ..events.kafka_producer import publish_membership_expired
            await publish_membership_expired(
                user_id=str(user_id),
                expired_level=old_level,
            )
        except Exception as e:
            logger.warning(f"Failed to publish membership expired event: {e}")

        return True

    async def check_permission(self, user_id: int, permission: str) -> bool:
        """检查用户是否有特定权限"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False

        permissions = self.get_permissions(user)
        value = permissions.get(permission, 0)
        return value == -1 or value > 0


membership_service = MembershipService
