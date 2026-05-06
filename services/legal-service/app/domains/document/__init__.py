"""文书服务领域"""
from .services import DocumentDomainService, TemplateDomainService
from .routers import router as document_router

__all__ = ["DocumentDomainService", "TemplateDomainService", "document_router"]