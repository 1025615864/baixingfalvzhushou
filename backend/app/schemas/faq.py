"""FAQ知识库相关Schema"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FAQCreate(BaseModel):
    """创建FAQ请求"""
    question: str = Field(..., description="问题", min_length=1, max_length=500)
    answer: str = Field(..., description="答案", min_length=1)
    category: str | None = Field(None, description="分类", max_length=100)
    tags: list[str] | None = Field(None, description="标签列表")
    priority: int = Field(default=0, description="优先级，数字越大越靠前", ge=0)
    is_active: bool = Field(default=True, description="是否激活")


class FAQUpdate(BaseModel):
    """更新FAQ请求"""
    question: str | None = Field(
        None,
        description="问题",
        min_length=1,
        max_length=500)
    answer: str | None = Field(None, description="答案", min_length=1)
    category: str | None = Field(None, description="分类", max_length=100)
    tags: list[str] | None = Field(None, description="标签列表")
    priority: int | None = Field(None, description="优先级，数字越大越靠前", ge=0)
    is_active: bool | None = Field(None, description="是否激活")


class FAQResponse(BaseModel):
    """FAQ响应"""
    id: int
    question: str
    answer: str
    category: str | None
    tags: list[str] | None
    priority: int
    is_active: bool
    view_count: int
    created_at: datetime
    updated_at: datetime


class FAQListResponse(BaseModel):
    """FAQ列表响应"""
    items: list[FAQResponse]
    total: int
    page: int
    page_size: int


class FAQSearchRequest(BaseModel):
    """FAQ搜索请求"""
    keyword: str | None = Field(None, description="搜索关键词")
    category: str | None = Field(None, description="分类筛选")
    tags: list[str] | None = Field(None, description="标签筛选")
    page: int = Field(default=1, description="页码", ge=1)
    page_size: int = Field(default=20, description="每页数量", ge=1, le=100)


class FAQCategoryResponse(BaseModel):
    """FAQ分类响应"""
    categories: list[str]


class FAQPopularResponse(BaseModel):
    """热门FAQ响应"""
    items: list[FAQResponse]


class FAQSmartSearchRequest(BaseModel):
    """FAQ智能搜索请求（用于智能客服）"""
    question: str = Field(..., description="用户问题", min_length=1)
    category: str | None = Field(None, description="分类筛选")
    limit: int = Field(default=5, description="返回数量", ge=1, le=10)


class FAQSmartSearchResponse(BaseModel):
    """FAQ智能搜索响应"""
    matched: bool = Field(..., description="是否匹配到FAQ")
    answer: str | None = Field(None, description="匹配的答案")
    faq_id: int | None = Field(None, description="匹配的FAQ ID")
    confidence: float = Field(..., description="匹配置信度", ge=0, le=1)
    suggestions: list[FAQResponse] = Field(
        default_factory=list, description="相关建议")
