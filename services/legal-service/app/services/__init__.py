"""Legal service business logic layer."""
from .consultation_service import ConsultationService
from .lawyer_service import LawyerService
from .appointment_service import AppointmentService
from .document_service import DocumentService, TemplateService
from .review_service import ReviewService
from .schedule_service import ScheduleService
from .firm_service import FirmService
from .matching_service import MatchingService

__all__ = [
    "ConsultationService",
    "LawyerService",
    "AppointmentService",
    "DocumentService",
    "TemplateService",
    "ReviewService",
    "ScheduleService",
    "FirmService",
    "MatchingService",
]
