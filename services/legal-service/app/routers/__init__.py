"""routers package"""
from .consultation import router as consultation_router
from .lawyer import router as lawyer_router
from .firm import router as firm_router
from .firm_admin import router as firm_admin_router
from .review import router as review_router
from .appointment import router as appointment_router
from .schedule import router as schedule_router
from .admin import router as admin_router
from .cache_admin import router as cache_admin_router
from .metrics import router as metrics_router
from .document import router as document_router
from .invitation import router as invitation_router
from .payment import router as payment_router
from .wallet import router as wallet_router
from .matching import router as matching_router
from .dispatch import router as dispatch_router
from .case import router as case_router
from .analytics import router as analytics_router
from .video import router as video_router
from .document_template import router as document_template_router
from .agent import router as agent_router

__all__ = [
    "consultation_router",
    "lawyer_router",
    "firm_router",
    "firm_admin_router",
    "review_router",
    "appointment_router",
    "schedule_router",
    "admin_router",
    "cache_admin_router",
    "metrics_router",
    "document_router",
    "invitation_router",
    "payment_router",
    "wallet_router",
    "matching_router",
    "dispatch_router",
    "case_router",
    "analytics_router",
    "video_router",
    "document_template_router",
    "agent_router",
]