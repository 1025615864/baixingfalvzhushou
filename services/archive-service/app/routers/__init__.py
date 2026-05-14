"""档案库路由"""
from .stats import router as stats_router
from .archive import router as archive_router
from .case_categories import router as case_categories_router
from .search import router as search_router
from .vector_ops import router as vector_ops_router
from .vector_search import router as vector_search_router
from .batch import router as batch_router
from .recommendations import router as recommendations_router
from .admin import router as admin_router

__all__ = ["stats_router", "archive_router", "case_categories_router", "search_router", "vector_ops_router", "vector_search_router", "batch_router", "recommendations_router", "admin_router"]