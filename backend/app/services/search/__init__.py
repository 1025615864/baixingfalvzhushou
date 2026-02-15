"""搜索服务模块

向后兼容导出（2026-01-22）
"""
from .core import search_service, SearchService
from .types import (
    SearchResults,
    NewsSearchItem,
    PostSearchItem,
    LawFirmSearchItem,
    LawyerSearchItem,
    KnowledgeSearchItem,
    HotKeyword,
)
from .suggestions import search_suggestion_service
from .history import search_history_service

__all__ = [
    "search_service",
    "SearchService",
    "SearchResults",
    "NewsSearchItem",
    "PostSearchItem",
    "LawFirmSearchItem",
    "LawyerSearchItem",
    "KnowledgeSearchItem",
    "HotKeyword",
    "search_suggestion_service",
    "search_history_service",
]
