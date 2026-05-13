from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    title: str = Field(max_length=200)
    content: str
    category: str = "general"
    cover_image: str | None = None


class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    cover_image: str | None = None


class CommentCreate(BaseModel):
    content: str
    parent_id: int | None = None
    images: list[str] | None = None


class NewsToForumPostRequest(BaseModel):
    news_id: int
    title: str | None = None
    content: str | None = None
    category: str = "general"


class NewsToForumPostResponse(BaseModel):
    post_id: int
    post_title: str
    post_url: str
    message: str
