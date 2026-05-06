"""InvitationService 单元测试"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.invitation_service import InvitationService
from app.services.firm_service import FirmService
from app.models import LawFirm, LawFirmInvitation, Lawyer


class TestInvitationService:
    """InvitationService 测试类"""

    @pytest.mark.asyncio
    async def test_create_invitation_valid_lawyer(self, db_session: AsyncSession):
        """测试向已认证律师创建邀请"""
        firm_service = FirmService(db_session)
        firm = await firm_service.create_firm(user_id=1, name="测试律所")

        lawyer = Lawyer(
            user_id=10,
            name="测试律师",
            status="verified",
            verified_at=datetime.utcnow(),
        )
        db_session.add(lawyer)
        await db_session.commit()
        await db_session.refresh(lawyer)

        service = InvitationService(db_session)
        invitation = await service.create_invitation(
            lawfirm_id=firm.id,
            lawyer_id=lawyer.id,
            invited_by_user_id=1,
            firm_role="associate",
            message="诚邀加入",
        )

        assert invitation.id is not None
        assert invitation.lawfirm_id == firm.id
        assert invitation.lawyer_id == lawyer.id
        assert invitation.status == "pending"
        assert invitation.firm_role == "associate"
        assert invitation.expires_at > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_create_invitation_unverified_lawyer(self, db_session: AsyncSession):
        """测试向未认证律师创建邀请应失败"""
        firm_service = FirmService(db_session)
        firm = await firm_service.create_firm(user_id=1, name="测试律所")

        lawyer = Lawyer(
            user_id=10,
            name="未认证律师",
            status="pending",
        )
        db_session.add(lawyer)
        await db_session.commit()
        await db_session.refresh(lawyer)

        service = InvitationService(db_session)
        with pytest.raises(ValueError, match="只能邀请已认证的律师"):
            await service.create_invitation(
                lawfirm_id=firm.id,
                lawyer_id=lawyer.id,
                invited_by_user_id=1,
            )

    @pytest.mark.asyncio
    async def test_create_invitation_already_in_firm(self, db_session: AsyncSession):
        """测试向已在其他律所的律师创建邀请应失败"""
        firm_service = FirmService(db_session)
        firm1 = await firm_service.create_firm(user_id=1, name="律所A")
        firm2 = await firm_service.create_firm(user_id=2, name="律所B")

        lawyer = Lawyer(
            user_id=10,
            name="已有律所律师",
            status="verified",
            verified_at=datetime.utcnow(),
            lawfirm_id=firm1.id,
        )
        db_session.add(lawyer)
        await db_session.commit()
        await db_session.refresh(lawyer)

        service = InvitationService(db_session)
        with pytest.raises(ValueError, match="该律师已在其他律所"):
            await service.create_invitation(
                lawfirm_id=firm2.id,
                lawyer_id=lawyer.id,
                invited_by_user_id=2,
            )

    @pytest.mark.asyncio
    async def test_accept_invitation(self, db_session: AsyncSession):
        """测试接受邀请"""
        firm_service = FirmService(db_session)
        firm = await firm_service.create_firm(user_id=1, name="测试律所")

        lawyer = Lawyer(
            user_id=10,
            name="测试律师",
            status="verified",
            verified_at=datetime.utcnow(),
        )
        db_session.add(lawyer)
        await db_session.commit()
        await db_session.refresh(lawyer)

        service = InvitationService(db_session)
        invitation = await service.create_invitation(
            lawfirm_id=firm.id,
            lawyer_id=lawyer.id,
            invited_by_user_id=1,
            firm_role="partner",
        )

        accepted = await service.accept_invitation(invitation.id)

        assert accepted.status == "accepted"
        assert accepted.responded_at is not None

        await db_session.refresh(lawyer)
        assert lawyer.lawfirm_id == firm.id
        assert lawyer.firm_role == "partner"
        assert lawyer.joined_at is not None

    @pytest.mark.asyncio
    async def test_accept_expired_invitation(self, db_session: AsyncSession):
        """测试接受已过期邀请应失败"""
        firm_service = FirmService(db_session)
        firm = await firm_service.create_firm(user_id=1, name="测试律所")

        lawyer = Lawyer(
            user_id=10,
            name="测试律师",
            status="verified",
            verified_at=datetime.utcnow(),
        )
        db_session.add(lawyer)
        await db_session.commit()
        await db_session.refresh(lawyer)

        invitation = LawFirmInvitation(
            lawfirm_id=firm.id,
            lawyer_id=lawyer.id,
            invited_by_user_id=1,
            status="pending",
            firm_role="associate",
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        db_session.add(invitation)
        await db_session.commit()
        await db_session.refresh(invitation)

        service = InvitationService(db_session)
        with pytest.raises(ValueError, match="邀请已过期"):
            await service.accept_invitation(invitation.id)

    @pytest.mark.asyncio
    async def test_reject_invitation(self, db_session: AsyncSession):
        """测试拒绝邀请"""
        firm_service = FirmService(db_session)
        firm = await firm_service.create_firm(user_id=1, name="测试律所")

        lawyer = Lawyer(
            user_id=10,
            name="测试律师",
            status="verified",
            verified_at=datetime.utcnow(),
        )
        db_session.add(lawyer)
        await db_session.commit()
        await db_session.refresh(lawyer)

        service = InvitationService(db_session)
        invitation = await service.create_invitation(
            lawfirm_id=firm.id,
            lawyer_id=lawyer.id,
            invited_by_user_id=1,
        )

        rejected = await service.reject_invitation(invitation.id)

        assert rejected.status == "rejected"
        assert rejected.responded_at is not None

    @pytest.mark.asyncio
    async def test_reject_non_pending_invitation(self, db_session: AsyncSession):
        """测试拒绝非待处理状态的邀请应失败"""
        firm_service = FirmService(db_session)
        firm = await firm_service.create_firm(user_id=1, name="测试律所")

        lawyer = Lawyer(
            user_id=10,
            name="测试律师",
            status="verified",
            verified_at=datetime.utcnow(),
        )
        db_session.add(lawyer)
        await db_session.commit()
        await db_session.refresh(lawyer)

        invitation = LawFirmInvitation(
            lawfirm_id=firm.id,
            lawyer_id=lawyer.id,
            invited_by_user_id=1,
            status="accepted",
            firm_role="associate",
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(invitation)
        await db_session.commit()
        await db_session.refresh(invitation)

        service = InvitationService(db_session)
        with pytest.raises(ValueError, match="邀请状态不是待处理"):
            await service.reject_invitation(invitation.id)

    @pytest.mark.asyncio
    async def test_expire_old_invitations(self, db_session: AsyncSession):
        """测试过期旧邀请"""
        firm_service = FirmService(db_session)
        firm = await firm_service.create_firm(user_id=1, name="测试律所")

        lawyer = Lawyer(
            user_id=10,
            name="测试律师",
            status="verified",
            verified_at=datetime.utcnow(),
        )
        db_session.add(lawyer)
        await db_session.commit()
        await db_session.refresh(lawyer)

        old_invitation = LawFirmInvitation(
            lawfirm_id=firm.id,
            lawyer_id=lawyer.id,
            invited_by_user_id=1,
            status="pending",
            firm_role="associate",
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        new_invitation = LawFirmInvitation(
            lawfirm_id=firm.id,
            lawyer_id=lawyer.id,
            invited_by_user_id=1,
            status="pending",
            firm_role="associate",
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(old_invitation)
        db_session.add(new_invitation)
        await db_session.commit()

        service = InvitationService(db_session)
        count = await service.expire_old_invitations()

        assert count == 1

        await db_session.refresh(old_invitation)
        await db_session.refresh(new_invitation)
        assert old_invitation.status == "expired"
        assert new_invitation.status == "pending"

    @pytest.mark.asyncio
    async def test_get_pending_invitations_by_lawyer(self, db_session: AsyncSession):
        """测试获取律师待处理邀请"""
        firm_service = FirmService(db_session)
        firm = await firm_service.create_firm(user_id=1, name="测试律所")

        lawyer = Lawyer(
            user_id=10,
            name="测试律师",
            status="verified",
            verified_at=datetime.utcnow(),
        )
        db_session.add(lawyer)
        await db_session.commit()
        await db_session.refresh(lawyer)

        service = InvitationService(db_session)
        await service.create_invitation(
            lawfirm_id=firm.id,
            lawyer_id=lawyer.id,
            invited_by_user_id=1,
        )

        pending = await service.get_pending_invitations_by_lawyer(lawyer.id)
        assert len(pending) >= 1
        assert all(inv.status == "pending" for inv in pending)
