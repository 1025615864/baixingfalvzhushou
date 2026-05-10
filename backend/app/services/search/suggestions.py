"""Search suggestions service."""
from __future__ import annotations
from typing import Optional, TypedDict


class HotKeyword(TypedDict):
    keyword: str
    count: int


class SearchSuggestionService:
    def __init__(self):
        self._suggestion_index: dict[str, list[str]] = {}
        self._popular_queries: dict[str, int] = {}

    def _escape_like(self, value: Optional[str], escape: str = "\\") -> str:
        if value is None:
            return ""
        result = value.replace(escape, escape + escape)
        result = result.replace("%", escape + "%")
        result = result.replace("_", escape + "_")
        return result

    async def get_search_suggestions(self, db=None, query: str = "", limit: int = 10) -> list[str]:
        if not query:
            return []
        query_lower = query.lower()
        suggestions = []
        for prefix, items in self._suggestion_index.items():
            if prefix.startswith(query_lower) or query_lower.startswith(prefix):
                suggestions.extend(items)
        for pq in self._popular_queries:
            if pq.startswith(query_lower):
                suggestions.append(pq)
        seen = set()
        unique = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        return unique[:limit]

    async def get_hot_keywords(self, db=None, limit: int = 10) -> list[HotKeyword]:
        sorted_queries = sorted(self._popular_queries.items(), key=lambda x: x[1], reverse=True)
        return [HotKeyword(keyword=q, count=c) for q, c in sorted_queries[:limit]]

    async def record_query(self, query: str) -> None:
        self._popular_queries[query] = self._popular_queries.get(query, 0) + 1

    def add_suggestion(self, prefix: str, suggestion: str) -> None:
        if prefix not in self._suggestion_index:
            self._suggestion_index[prefix] = []
        if suggestion not in self._suggestion_index[prefix]:
            self._suggestion_index[prefix].append(suggestion)

    def get_popular_queries(self, limit: int = 10) -> list[str]:
        sorted_queries = sorted(self._popular_queries.items(), key=lambda x: x[1], reverse=True)
        return [q for q, _ in sorted_queries[:limit]]


search_suggestion_service = SearchSuggestionService()
