"""邀请状态机"""
from enum import Enum
from typing import Set, Dict
from app.shared.state_machines import StateMachine, TimestampedStateMachine


class InvitationStatus(str, Enum):
    """邀请状态"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


INVITATION_TRANSITIONS: Dict[InvitationStatus, Set[InvitationStatus]] = {
    InvitationStatus.PENDING: {
        InvitationStatus.ACCEPTED,
        InvitationStatus.REJECTED,
        InvitationStatus.EXPIRED,
        InvitationStatus.CANCELLED,
    },
    InvitationStatus.REJECTED: {InvitationStatus.PENDING},
    InvitationStatus.EXPIRED: {InvitationStatus.PENDING},
    InvitationStatus.ACCEPTED: set(),
    InvitationStatus.CANCELLED: set(),
}


class InvitationStateMachine(TimestampedStateMachine[InvitationStatus]):
    """邀请状态机"""

    @property
    def transitions(self) -> Dict[InvitationStatus, Set[InvitationStatus]]:
        return INVITATION_TRANSITIONS

    @property
    def terminal_states(self) -> Set[InvitationStatus]:
        return {InvitationStatus.ACCEPTED, InvitationStatus.CANCELLED}

    def transition_to(
        self,
        invitation,
        target: InvitationStatus,
        operator_id: str = None,
        reason: str = None,
    ) -> None:
        """转换邀请状态"""
        current = InvitationStatus(invitation.status)
        super().transition(current, target, operator_id, reason)
        invitation.status = target.value

    @staticmethod
    def can_transition_from(current: str, target: str) -> bool:
        """静态检查方法"""
        try:
            current_enum = InvitationStatus(current)
            target_enum = InvitationStatus(target)
            allowed = INVITATION_TRANSITIONS.get(current_enum, set())
            return target_enum in allowed
        except ValueError:
            return False