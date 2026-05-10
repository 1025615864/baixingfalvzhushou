"""Search types and data structures."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, TypedDict, Literal


class NewsSearchItem(TypedDict, total=False):
    id: int
    title: str
    summary: Optional[str]
    snippet: Optional[str]
    type: Literal["news"]


class PostSearchItem(TypedDict, total=False):
    id: int
    title: str
    content: str
    type: Literal["post"]


class LawFirmSearchItem(TypedDict, total=False):
    id: int
    name: str
    address: Optional[str]
    type: Literal["lawfirm"]


class LawyerSearchItem(TypedDict, total=False):
    id: int
    name: str
    specialties: Optional[str]
    type: Literal["lawyer"]


class KnowledgeSearchItem(TypedDict, total=False):
    id: int
    title: str
    category: Optional[str]
    type: Literal["knowledge"]


class SearchResults(TypedDict, total=False):
    news: list[NewsSearchItem]
    posts: list[PostSearchItem]
    lawfirms: list[LawFirmSearchItem]
    lawyers: list[LawyerSearchItem]
    knowledge: list[KnowledgeSearchItem]


class HotKeyword(TypedDict):
    keyword: str
    count: int


@dataclass
class SearchFilter:
    category: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    source: Optional[str] = None
    tags: list[str] = field(default_factory=list)


@dataclass
class SearchQuery:
    text: str
    filters: Optional[SearchFilter] = None
    limit: int = 20
    offset: int = 0


@dataclass
class SearchResult:
    id: str
    title: str
    content: str
    category: str = "general"
    score: float = 0.0
    highlights: list[str] = field(default_factory=list)
