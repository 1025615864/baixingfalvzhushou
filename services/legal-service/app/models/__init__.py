"""models package"""
from app.database import Base
from .consultation import Consultation, ChatMessage
from .lawyer import Lawyer, LawyerSchedule
from .firm import LawFirm
from .appointment import LawyerConsultation
from .review import Review
from .document import LegalDocument, DocumentTemplate
from .outbox import OutboxEvent
from .verification import LawFirmVerification
from .invitation import LawFirmInvitation
from .firm_admin import LawFirmAdmin

__all__ = [
    "Base",
    "Consultation",
    "ChatMessage",
    "Lawyer",
    "LawyerSchedule",
    "LawFirm",
    "LawyerConsultation",
    "Review",
    "LegalDocument",
    "DocumentTemplate",
    "OutboxEvent",
    "LawFirmInvitation",
    "LawFirmAdmin",
]