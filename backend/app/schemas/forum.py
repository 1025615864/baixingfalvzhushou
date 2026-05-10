from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    title: str
    content: str
    category: str = "general"
    cover_image: str | None = None


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
