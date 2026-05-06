"""shared package - 跨领域共享代码"""
from .permissions import (
    Permission,
    ROLE_PERMISSIONS,
    get_permissions_for_role,
    has_permission,
)
from .state_machines import (
    StateMachine,
    TimestampedStateMachine,
    TransitionError,
)
from .firm_state_machine import (
    FirmStatus,
    FirmStateMachine,
)
from .invitation_state_machine import (
    InvitationStatus,
    InvitationStateMachine,
)
from .appointment_state_machine import (
    AppointmentStatus,
    AppointmentStateMachine,
)
from .consultation_state_machine import (
    ConsultationStatus,
    ConsultationStateMachine,
)

__all__ = [
    "Permission",
    "ROLE_PERMISSIONS",
    "get_permissions_for_role",
    "has_permission",
    "StateMachine",
    "TimestampedStateMachine",
    "TransitionError",
    "FirmStatus",
    "FirmStateMachine",
    "InvitationStatus",
    "InvitationStateMachine",
    "AppointmentStatus",
    "AppointmentStateMachine",
    "ConsultationStatus",
    "ConsultationStateMachine",
]