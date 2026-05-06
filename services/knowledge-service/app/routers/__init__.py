"""知识库路由"""
from .stats import router as stats_router
from .knowledge import router as knowledge_router
from .categories import router as categories_router
from .search import router as search_router
from .vector_ops import router as vector_ops_router
from .vector_search import router as vector_search_router
from .batch import router as batch_router

__all__ = ["stats_router", "knowledge_router", "categories_router", "search_router", "vector_ops_router", "vector_search_router", "batch_router"]