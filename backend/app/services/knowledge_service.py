"""知识库服务

⚠️ 已迁移到 services/knowledge/
⚠️ 本文件仅用于向后兼容，请使用新导入路径

迁移时间: 2026-01-22
"""
from .knowledge import (
    knowledge_service,
    KnowledgeService,
    get_knowledge_service,
)

__all__ = [
    "knowledge_service",
    "KnowledgeService",
    "get_knowledge_service",
]
