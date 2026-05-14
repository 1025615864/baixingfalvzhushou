"""会员服务测试"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.services.membership_service import MembershipService, MembershipTier
from app.models import User


class TestMembershipService:
    """会员服务测试"""

    @pytest.mark.asyncio
    async def test_get_tier_free(self, db_session):
        """测试免费用户等级"""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "user"
        user.vip_expires_at = None

        service = MembershipService(db_session)
        tier = service.get_tier(user)

        assert tier == MembershipTier.FREE

    @pytest.mark.asyncio
    async def test_get_tier_vip(self, db_session):
        """测试VIP用户等级"""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "vip"
        user.vip_expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        service = MembershipService(db_session)
        tier = service.get_tier(user)

        assert tier == MembershipTier.VIP

    @pytest.mark.asyncio
    async def test_get_tier_admin(self, db_session):
        """测试管理员等级"""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "admin"
        user.vip_expires_at = None

        service = MembershipService(db_session)
        tier = service.get_tier(user)

        assert tier == MembershipTier.ADMIN

    @pytest.mark.asyncio
    async def test_is_vip(self, db_session):
        """测试VIP检查"""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "vip"
        user.vip_expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        service = MembershipService(db_session)
        assert service.is_vip(user) is True

    @pytest.mark.asyncio
    async def test_is_not_vip(self, db_session):
        """测试非VIP检查"""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "user"
        user.vip_expires_at = None

        service = MembershipService(db_session)
        assert service.is_vip(user) is False

    @pytest.mark.asyncio
    async def test_get_permissions_free(self, db_session):
        """测试免费用户权限"""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "user"
        user.vip_expires_at = None

        service = MembershipService(db_session)
        permissions = service.get_permissions(user)

        assert permissions["ai_sessions"] == 5
        assert permissions["ai_messages_per_day"] == 20
        assert permissions["export_enabled"] is False

    @pytest.mark.asyncio
    async def test_get_permissions_vip(self, db_session):
        """测试VIP用户权限"""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "vip"
        user.vip_expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        service = MembershipService(db_session)
        permissions = service.get_permissions(user)

        assert permissions["ai_sessions"] == 50
        assert permissions["ai_messages_per_day"] == 200
        assert permissions["export_enabled"] is True

    @pytest.mark.asyncio
    async def test_get_permissions_svip(self, db_session):
        """测试SVIP用户权限"""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "svip"
        user.vip_expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        service = MembershipService(db_session)
        permissions = service.get_permissions(user)

        assert permissions["ai_sessions"] == -1
        assert permissions["ai_messages_per_day"] == -1
        assert permissions["storage_mb"] == 10240
        assert permissions["export_enabled"] is True

    @pytest.mark.asyncio
    async def test_get_vip_remaining_days(self, db_session):
        """测试VIP剩余天数计算"""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "vip"
        user.vip_expires_at = datetime.now(timezone.utc) + timedelta(days=15)

        service = MembershipService(db_session)
        remaining = service.get_vip_remaining_days(user)

        assert remaining == 15

    @pytest.mark.asyncio
    async def test_get_vip_remaining_days_expired(self, db_session):
        """测试过期VIP"""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "vip"
        user.vip_expires_at = datetime.now(timezone.utc) - timedelta(days=1)

        service = MembershipService(db_session)
        remaining = service.get_vip_remaining_days(user)

        assert remaining == 0


class TestMembershipTier:
    """会员等级常量测试"""

    def test_tier_constants(self):
        assert MembershipTier.FREE == "free"
        assert MembershipTier.VIP == "vip"
        assert MembershipTier.SVIP == "svip"
        assert MembershipTier.ADMIN == "admin"

    def test_permission_differences(self):
        """验证不同等级权限差异"""
        service = MembershipService(MagicMock())

        free_perms = service.TIER_PERMISSIONS[MembershipTier.FREE]
        vip_perms = service.TIER_PERMISSIONS[MembershipTier.VIP]
        svip_perms = service.TIER_PERMISSIONS[MembershipTier.SVIP]

        assert free_perms["ai_sessions"] < vip_perms["ai_sessions"]
        assert vip_perms["ai_sessions"] < svip_perms["ai_sessions"]

        assert free_perms["export_enabled"] is False
        assert vip_perms["export_enabled"] is True
        assert svip_perms["export_enabled"] is True
