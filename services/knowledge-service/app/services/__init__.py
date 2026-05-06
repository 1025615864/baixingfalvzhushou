"""知识库服务模块"""
from .knowledge_vector_store import (
    search_knowledge,
    add_knowledge,
    delete_knowledge,
    get_collection_count
)
from .knowledge_service import KnowledgeService

__all__ = ["search_knowledge", "add_knowledge", "delete_knowledge", "get_collection_count", "KnowledgeService"]