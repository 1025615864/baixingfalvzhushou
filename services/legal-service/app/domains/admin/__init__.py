"""管理服务领域"""
from .services import AdminDomainService
from .routers import router as admin_router

__all__ = ["AdminDomainService", "admin_router"]