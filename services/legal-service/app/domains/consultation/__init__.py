"""咨询服务领域"""
from .services import ConsultationDomainService
from .routers import router as consultation_router

__all__ = ["ConsultationDomainService", "consultation_router"]