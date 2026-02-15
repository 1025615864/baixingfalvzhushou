"""文书服务模块

提供法律文书生成、模板管理、PDF导出等功能。
"""
from __future__ import annotations

from .core import DocumentGenerationService, document_generation_service
from .templates import DocumentTemplateService, document_template_service
from .pdf import generate_document_pdf, DocumentPdfConfig, create_pdf_response
from .storage import DocumentStorageService, document_storage_service

__all__ = [
    "DocumentGenerationService",
    "document_generation_service",
    "DocumentTemplateService",
    "document_template_service",
    "generate_document_pdf",
    "DocumentPdfConfig",
    "create_pdf_response",
    "DocumentStorageService",
    "document_storage_service",
]
