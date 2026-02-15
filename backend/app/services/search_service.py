"""搜索服务

⚠️ 已迁移到 services/search/
⚠️ 本文件仅用于向后兼容，请使用新导入路径

迁移时间: 2026-01-22
"""
from .search import (
    search_service,
    SearchService,
    SearchResults,
    NewsSearchItem,
    PostSearchItem,
    LawFirmSearchItem,
    LawyerSearchItem,
    KnowledgeSearchItem,
    HotKeyword,
    search_suggestion_service,
    search_history_service,
)

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
