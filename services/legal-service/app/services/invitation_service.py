"""律所律师邀请服务"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models import LawFirmInvitation, Lawyer
from ..shared.invitation_state_machine import (
    InvitationStatus,
    InvitationStateMachine,
    INVITATION_TRANSITIONS,
)
from ..shared.state_machines import TransitionError


class InvitationService:
    """律所律师邀请服务"""

    INVITATION_EXPIRY_DAYS = 7
    FIRM_ROLES = ["partner", "associate", "intern", "assistant"]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_invitation(
        self,
        lawfirm_id: int,
        lawyer_id: int,
        invited_by_user_id: int,
        firm_role: str = "associate",
        message: Optional[str] = None,
    ) -> LawFirmInvitation:
        """创建律师邀请"""
        result = await self.db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        lawyer = result.scalar_one_or_none()

        if not lawyer:
            raise ValueError("律师不存在")

        if lawyer.status != "verified":
            raise ValueError("只能邀请已认证的律师")

        if lawyer.lawfirm_id is not None:
            raise ValueError("该律师已在其他律所")

        invitation = LawFirmInvitation(
            lawfirm_id=lawfirm_id,
            lawyer_id=lawyer_id,
            invited_by_user_id=invited_by_user_id,
            status="pending",
            firm_role=firm_role if firm_role in self.FIRM_ROLES else "associate",
            message=message,
            expires_at=datetime.utcnow() + timedelta(days=self.INVITATION_EXPIRY_DAYS),
        )
        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)
        return invitation

    async def accept_invitation(self, invitation_id: int) -> LawFirmInvitation:
        """接受邀请"""
        invitation = await self.get_invitation(invitation_id)
        if not invitation:
            raise ValueError("邀请不存在")

        if invitation.expires_at < datetime.utcnow():
            invitation.status = InvitationStatus.EXPIRED.value
            await self.db.commit()
            raise ValueError("邀请已过期")

        if not InvitationStateMachine.can_transition_from(invitation.status, InvitationStatus.ACCEPTED.value):
            raise TransitionError(
                current_state=invitation.status,
                target_state=InvitationStatus.ACCEPTED.value,
            )

        invitation.status = InvitationStatus.ACCEPTED.value
        invitation.responded_at = datetime.utcnow()

        lawyer_result = await self.db.execute(
            select(Lawyer).where(Lawyer.id == invitation.lawyer_id)
        )
        lawyer = lawyer_result.scalar_one()
        lawyer.lawfirm_id = invitation.lawfirm_id
        lawyer.firm_role = invitation.firm_role
        lawyer.joined_at = datetime.utcnow()
        lawyer.invited_by = invitation.invited_by_user_id

        await self.db.commit()
        await self.db.refresh(invitation)
        return invitation

    async def reject_invitation(self, invitation_id: int) -> LawFirmInvitation:
        """拒绝邀请"""
        invitation = await self.get_invitation(invitation_id)
        if not invitation:
            raise ValueError("邀请不存在")

        if not InvitationStateMachine.can_transition_from(invitation.status, InvitationStatus.REJECTED.value):
            raise TransitionError(
                current_state=invitation.status,
                target_state=InvitationStatus.REJECTED.value,
            )

        invitation.status = InvitationStatus.REJECTED.value
        invitation.responded_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(invitation)
        return invitation

    async def get_invitation(self, invitation_id: int) -> Optional[LawFirmInvitation]:
        """获取邀请"""
        result = await self.db.execute(
            select(LawFirmInvitation).where(LawFirmInvitation.id == invitation_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_invitations_by_lawyer(self, lawyer_id: int) -> List[LawFirmInvitation]:
        """获取律师待处理的邀请"""
        result = await self.db.execute(
            select(LawFirmInvitation).where(
                and_(
                    LawFirmInvitation.lawyer_id == lawyer_id,
                    LawFirmInvitation.status == "pending",
                )
            )
        )
        return list(result.scalars().all())

    async def get_invitations_by_firm(self, lawfirm_id: int, status: Optional[str] = None) -> List[LawFirmInvitation]:
        """获取律所的所有邀请"""
        query = select(LawFirmInvitation).where(
            LawFirmInvitation.lawfirm_id == lawfirm_id
        )
        if status:
            query = query.where(LawFirmInvitation.status == status)

        query = query.order_by(LawFirmInvitation.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def expire_old_invitations(self) -> int:
        """将过期的邀请标记为过期"""
        result = await self.db.execute(
            select(LawFirmInvitation).where(
                and_(
                    LawFirmInvitation.status == "pending",
                    LawFirmInvitation.expires_at < datetime.utcnow(),
                )
            )
        )
        invitations = result.scalars().all()

        count = 0
        for inv in invitations:
            inv.status = "expired"
            count += 1

        if count > 0:
            await self.db.commit()

        return count

    async def remove_lawyer_from_firm(self, lawyer_id: int, lawfirm_id: int) -> bool:
        """从律所移除律师"""
        lawyer_result = await self.db.execute(
            select(Lawyer).where(
                and_(
                    Lawyer.id == lawyer_id,
                    Lawyer.lawfirm_id == lawfirm_id,
                )
            )
        )
        lawyer = lawyer_result.scalar_one_or_none()

        if not lawyer:
            return False

        lawyer.lawfirm_id = None
        lawyer.firm_role = None
        lawyer.joined_at = None
        lawyer.invited_by = None
        await self.db.commit()
        return True
