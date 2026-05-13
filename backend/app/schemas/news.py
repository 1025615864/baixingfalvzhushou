from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NewsListItem(BaseModel):
    id: int
    title: str
    summary: str | None = None
    cover_image: str | None = None
    category: str | None = None
    source: str | None = None
    source_url: str | None = None
    is_published: bool = True
    published_at: datetime | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NewsTopicResponse(BaseModel):
    id: int
    title: str
    slug: str | None = None
    description: str | None = None
    cover_image: str | None = None
    is_active: bool = True
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NewsTopicDetailResponse(BaseModel):
    id: int
    title: str
    slug: str | None = None
    description: str | None = None
    cover_image: str | None = None
    is_active: bool = True
    items: list[NewsListItem] = []
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NewsTopicCreate(BaseModel):
    title: str
    slug: str | None = None
    description: str | None = None
    cover_image: str | None = None
    is_active: bool = True
    auto_category: str | None = None
    auto_keyword: str | None = None


class NewsTopicUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    cover_image: str | None = None
    is_active: bool | None = None
    auto_category: str | None = None
    auto_keyword: str | None = None


class NewsCreate(BaseModel):
    title: str
    content: str | None = None
    category: str | None = None
    source: str | None = None
    source_url: str | None = None
    cover_image: str | None = None
    author: str | None = None
    is_published: bool = False
    is_top: bool = False


class NewsUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    source: str | None = None
    source_url: str | None = None
    cover_image: str | None = None
    author: str | None = None
    is_published: bool | None = None
    is_top: bool | None = None
