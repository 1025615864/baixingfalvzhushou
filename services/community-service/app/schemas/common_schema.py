"""通用 Schema"""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationBase(BaseModel):
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=20)


class ListResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int


class CursorPaginationResponse(BaseModel, Generic[T]):
    items: List[T]
    next_cursor: Optional[str] = None
    has_more: bool = False


class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "操作成功"


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str = None
