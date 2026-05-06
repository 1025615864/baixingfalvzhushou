"""律所状态机"""
from enum import Enum
from typing import Set, Dict
from app.shared.state_machines import StateMachine, TransitionError, TimestampedStateMachine


class FirmStatus(str, Enum):
    """律所状态"""
    DRAFT = "draft"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


FIRM_TRANSITIONS: Dict[FirmStatus, Set[FirmStatus]] = {
    FirmStatus.DRAFT: {FirmStatus.PENDING},
    FirmStatus.PENDING: {FirmStatus.UNDER_REVIEW, FirmStatus.DRAFT},
    FirmStatus.UNDER_REVIEW: {FirmStatus.APPROVED, FirmStatus.REJECTED},
    FirmStatus.REJECTED: {FirmStatus.PENDING},
    FirmStatus.APPROVED: {FirmStatus.SUSPENDED, FirmStatus.DEACTIVATED},
    FirmStatus.SUSPENDED: {FirmStatus.APPROVED, FirmStatus.DEACTIVATED},
    FirmStatus.DEACTIVATED: set(),
}


class FirmStateMachine(TimestampedStateMachine[FirmStatus]):
    """律所状态机"""

    @property
    def transitions(self) -> Dict[FirmStatus, Set[FirmStatus]]:
        return FIRM_TRANSITIONS

    @property
    def terminal_states(self) -> Set[FirmStatus]:
        return {FirmStatus.DEACTIVATED}

    def transition_to(
        self,
        firm,
        target: FirmStatus,
        operator_id: str = None,
        reason: str = None,
    ) -> None:
        """转换律所状态"""
        current = FirmStatus(firm.status)
        super().transition(current, target, operator_id, reason)
        firm.status = target.value

    @staticmethod
    def can_transition_from(current: str, target: str) -> bool:
        """静态检查方法"""
        try:
            current_enum = FirmStatus(current)
            target_enum = FirmStatus(target)
            allowed = FIRM_TRANSITIONS.get(current_enum, set())
            return target_enum in allowed
        except ValueError:
            return False