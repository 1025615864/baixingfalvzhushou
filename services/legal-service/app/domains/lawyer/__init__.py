"""律师服务领域"""
from .services import LawyerDomainService
from .routers import router as lawyer_router

__all__ = ["LawyerDomainService", "lawyer_router"]