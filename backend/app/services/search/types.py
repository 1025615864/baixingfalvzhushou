"""搜索服务类型定义

提供全局搜索的类型定义
"""
from typing import Literal
from typing_extensions import TypedDict


class NewsSearchItem(TypedDict):
    id: int
    title: str
    summary: str | None
    snippet: str | None
    type: Literal["news"]


class PostSearchItem(TypedDict):
    id: int
    title: str
    content: str
    type: Literal["post"]


class LawFirmSearchItem(TypedDict):
    id: int
    name: str
    address: str | None
    type: Literal["lawfirm"]


class LawyerSearchItem(TypedDict):
    id: int
    name: str
    specialties: str | None
    type: Literal["lawyer"]


class KnowledgeSearchItem(TypedDict):
    id: int
    title: str
    category: str | None
    type: Literal["knowledge"]


class SearchResults(TypedDict):
    news: list[NewsSearchItem]
    posts: list[PostSearchItem]
    lawfirms: list[LawFirmSearchItem]
    lawyers: list[LawyerSearchItem]
    knowledge: list[KnowledgeSearchItem]


class HotKeyword(TypedDict):
    keyword: str
    count: int
