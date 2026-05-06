"""评论 Schema"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    parent_id: Optional[int] = None
    reply_to_user_id: Optional[int] = None


class CommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    author_name: str
    author_avatar: Optional[str] = None
    is_lawyer: bool = False
    content: str
    parent_id: Optional[int] = None
    reply_to_user_id: Optional[int] = None
    reply_to_user_name: Optional[str] = None
    floor_number: Optional[int] = None
    like_count: int = 0
    created_at: datetime
    replies: List["CommentResponse"] = []

    class Config:
        from_attributes = True


CommentResponse.model_rebuild()


class CommentListResponse(BaseModel):
    items: List[CommentResponse]
    total: int
    page: int
    page_size: int


class NestedCommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    author_name: str
    author_avatar: Optional[str] = None
    is_lawyer: bool = False
    content: str
    floor_number: Optional[int] = None
    like_count: int = 0
    created_at: datetime
    replies: List[dict] = []

    class Config:
        from_attributes = True
