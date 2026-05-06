"""评价服务领域"""
from .services import ReviewDomainService
from .routers import router as review_router

__all__ = ["ReviewDomainService", "review_router"]