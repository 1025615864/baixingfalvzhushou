"""Search service core."""
from __future__ import annotations
from typing import Optional
from app.services.search.types import SearchQuery, SearchResult, SearchFilter


class SearchService:
    def __init__(self):
        self._index: dict[str, list[dict]] = {}

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        text = query.text.lower()
        results = []
        for category, items in self._index.items():
            if query.filters and query.filters.category and category != query.filters.category:
                continue
            for item in items:
                if text in item.get("title", "").lower() or text in item.get("content", "").lower():
                    results.append(SearchResult(
                        id=item.get("id", ""),
                        title=item.get("title", ""),
                        content=item.get("content", ""),
                        category=category,
                        score=1.0 if text in item.get("title", "").lower() else 0.5,
                    ))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:query.limit]

    async def index_document(self, doc_id: str, title: str, content: str, category: str = "general") -> dict:
        if category not in self._index:
            self._index[category] = []
        self._index[category].append({"id": doc_id, "title": title, "content": content})
        return {"indexed": True, "doc_id": doc_id}

    async def remove_document(self, doc_id: str) -> dict:
        for category in self._index:
            self._index[category] = [d for d in self._index[category] if d["id"] != doc_id]
        return {"removed": True}
