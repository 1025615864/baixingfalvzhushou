"""知识库服务模块

向后兼容导出（2026-01-22）
"""
from .core import KnowledgeService, get_knowledge_service, knowledge_service
from .templates import KnowledgeTemplateService, knowledge_template_service
from .vectorize import KnowledgeVectorizeService, knowledge_vectorize_service

__all__ = [
    "KnowledgeService",
    "get_knowledge_service",
    "knowledge_service",
    "KnowledgeTemplateService",
    "knowledge_template_service",
    "KnowledgeVectorizeService",
    "knowledge_vectorize_service",
]
