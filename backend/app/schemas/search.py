from __future__ import annotations

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    q: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    id: int
    title: str
    snippet: str | None = None
    type: str
    url: str | None = None


class SearchResponse(BaseModel):
    news: list[SearchResultItem] = []
    posts: list[SearchResultItem] = []
    lawfirms: list[SearchResultItem] = []
    lawyers: list[SearchResultItem] = []
    knowledge: list[SearchResultItem] = []


class SearchSuggestion(BaseModel):
    suggestions: list[str] = []


class HotKeywords(BaseModel):
    keywords: list[str] = []


class SearchHistoryResponse(BaseModel):
    history: list[str] = []
