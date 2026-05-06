"""帖子 Schema"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class PostCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category: Optional[str] = "general"
    tags: Optional[List[str]] = None


class PostUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None


class PostResponse(BaseModel):
    id: int
    user_id: int
    author_name: str
    author_avatar: Optional[str] = None
    is_lawyer: bool = False
    title: str
    content: str
    category: Optional[str] = None
    status: str
    is_pinned: bool = False
    is_featured: bool = False
    is_best_answer: bool = False
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    share_count: int = 0
    hot_score: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    items: List[PostResponse]
    total: int
    page: int
    page_size: int


class LikeResponse(BaseModel):
    action: str
    like_count: int


class FavoriteResponse(BaseModel):
    action: str
    favorite_count: int
