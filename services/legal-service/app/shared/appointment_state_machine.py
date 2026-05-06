"""预约状态机"""
from enum import Enum
from typing import Set, Dict
from app.shared.state_machines import StateMachine, TimestampedStateMachine


class AppointmentStatus(str, Enum):
    """预约状态"""
    PENDING_PAYMENT = "pending_payment"
    CONFIRMED = "confirmed"
    REMINDER_SENT = "reminder_sent"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED_BY_USER = "cancelled_by_user"
    CANCELLED_BY_LAWYER = "cancelled_by_lawyer"
    CANCELLED_BY_SYSTEM = "cancelled_by_system"
    NO_SHOW = "no_show"
    EXPIRED = "expired"


APPOINTMENT_TRANSITIONS: Dict[AppointmentStatus, Set[AppointmentStatus]] = {
    AppointmentStatus.PENDING_PAYMENT: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.EXPIRED,
        AppointmentStatus.CANCELLED_BY_USER,
    },
    AppointmentStatus.CONFIRMED: {
        AppointmentStatus.REMINDER_SENT,
        AppointmentStatus.IN_PROGRESS,
        AppointmentStatus.CANCELLED_BY_USER,
        AppointmentStatus.CANCELLED_BY_LAWYER,
        AppointmentStatus.CANCELLED_BY_SYSTEM,
    },
    AppointmentStatus.REMINDER_SENT: {
        AppointmentStatus.IN_PROGRESS,
        AppointmentStatus.CANCELLED_BY_USER,
        AppointmentStatus.CANCELLED_BY_LAWYER,
    },
    AppointmentStatus.IN_PROGRESS: {
        AppointmentStatus.COMPLETED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED_BY_USER: set(),
    AppointmentStatus.CANCELLED_BY_LAWYER: set(),
    AppointmentStatus.CANCELLED_BY_SYSTEM: set(),
    AppointmentStatus.NO_SHOW: set(),
    AppointmentStatus.EXPIRED: set(),
}


class AppointmentStateMachine(TimestampedStateMachine[AppointmentStatus]):
    """预约状态机"""

    @property
    def transitions(self) -> Dict[AppointmentStatus, Set[AppointmentStatus]]:
        return APPOINTMENT_TRANSITIONS

    @property
    def terminal_states(self) -> Set[AppointmentStatus]:
        return {
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED_BY_USER,
            AppointmentStatus.CANCELLED_BY_LAWYER,
            AppointmentStatus.CANCELLED_BY_SYSTEM,
            AppointmentStatus.NO_SHOW,
            AppointmentStatus.EXPIRED,
        }

    def transition_to(
        self,
        appointment,
        target: AppointmentStatus,
        operator_id: str = None,
        reason: str = None,
    ) -> None:
        """转换预约状态"""
        current = AppointmentStatus(appointment.status)
        super().transition(current, target, operator_id, reason)
        appointment.status = target.value

    @staticmethod
    def can_transition_from(current: str, target: str) -> bool:
        """静态检查方法"""
        try:
            current_enum = AppointmentStatus(current)
            target_enum = AppointmentStatus(target)
            allowed = APPOINTMENT_TRANSITIONS.get(current_enum, set())
            return target_enum in allowed
        except ValueError:
            return False