from app.database import Base
from .lawyer import Lawyer
from .firm import LawFirm, LawFirmVerification
from .review import Review
from .consultation import Consultation
from .schedule import Schedule
from .appointment import Appointment
from .invitation import FirmInvitation
from .lawyer_profile import LawyerHomepage, LawyerPromotionLink, LawyerReplyTemplate
from .verification import LawyerVerification
from .payment import ConsultationPayment, LawyerWallet, WalletTransaction
from .case import LawCase, DispatchRecord
from .review_appeal import ReviewAppeal
from .video import VideoConsultation
from .document_template import DocumentTemplate

__all__ = [
    "Base",
    "Lawyer",
    "LawFirm",
    "LawFirmVerification",
    "Review",
    "Consultation",
    "Schedule",
    "Appointment",
    "FirmInvitation",
    "LawyerHomepage",
    "LawyerPromotionLink",
    "LawyerReplyTemplate",
    "LawyerVerification",
    "ConsultationPayment",
    "LawyerWallet",
    "WalletTransaction",
    "LawCase",
    "DispatchRecord",
    "ReviewAppeal",
    "VideoConsultation",
    "DocumentTemplate",
]