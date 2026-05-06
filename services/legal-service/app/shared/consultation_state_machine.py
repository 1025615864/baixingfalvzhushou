"""咨询状态机"""
from enum import Enum
from typing import Set, Dict
from app.shared.state_machines import StateMachine, TimestampedStateMachine


class ConsultationStatus(str, Enum):
    """咨询状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    ANSWERED = "answered"
    CLOSED = "closed"
    CANCELLED = "cancelled"


CONSULTATION_TRANSITIONS: Dict[ConsultationStatus, Set[ConsultationStatus]] = {
    ConsultationStatus.PENDING: {
        ConsultationStatus.PROCESSING,
        ConsultationStatus.CANCELLED,
    },
    ConsultationStatus.PROCESSING: {
        ConsultationStatus.ANSWERED,
        ConsultationStatus.CANCELLED,
    },
    ConsultationStatus.ANSWERED: {
        ConsultationStatus.CLOSED,
    },
    ConsultationStatus.CLOSED: set(),
    ConsultationStatus.CANCELLED: set(),
}


class ConsultationStateMachine(TimestampedStateMachine[ConsultationStatus]):
    """咨询状态机"""

    @property
    def transitions(self) -> Dict[ConsultationStatus, Set[ConsultationStatus]]:
        return CONSULTATION_TRANSITIONS

    @property
    def terminal_states(self) -> Set[ConsultationStatus]:
        return {
            ConsultationStatus.CLOSED,
            ConsultationStatus.CANCELLED,
        }

    def transition_to(
        self,
        consultation,
        target: ConsultationStatus,
        operator_id: str = None,
        reason: str = None,
    ) -> None:
        """转换咨询状态"""
        current = ConsultationStatus(consultation.status)
        super().transition(current, target, operator_id, reason)
        consultation.status = target.value

    @staticmethod
    def can_transition_from(current: str, target: str) -> bool:
        """静态检查方法"""
        try:
            current_enum = ConsultationStatus(current)
            target_enum = ConsultationStatus(target)
            allowed = CONSULTATION_TRANSITIONS.get(current_enum, set())
            return target_enum in allowed
        except ValueError:
            return False

    @staticmethod
    def get_allowed_transitions(current: str) -> Set[str]:
        """获取当前状态允许的转换目标"""
        try:
            current_enum = ConsultationStatus(current)
            return {s.value for s in CONSULTATION_TRANSITIONS.get(current_enum, set())}
        except ValueError:
            return set()
