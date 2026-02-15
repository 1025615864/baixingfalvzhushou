"""个性化推荐相关Schema"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LawyerRecommendationItem(BaseModel):
    """律师推荐项"""
    lawyer_id: int = Field(..., description="律师ID")
    lawyer_name: str = Field(..., description="律师姓名")
    avatar: str | None = Field(None, description="头像URL")
    specialties: str | None = Field(None, description="专业领域")
    rating: float = Field(..., description="评分")
    review_count: int = Field(..., description="评价数量")
    consultation_count: int = Field(..., description="咨询数量")
    is_verified: bool = Field(..., description="是否认证")
    match_score: float = Field(..., description="匹配分数", ge=0, le=1)


class PostRecommendationItem(BaseModel):
    """帖子推荐项"""
    post_id: int = Field(..., description="帖子ID")
    title: str = Field(..., description="标题")
    content: str | None = Field(None, description="内容摘要")
    author_id: int = Field(..., description="作者ID")
    author_name: str = Field(..., description="作者名称")
    view_count: int = Field(..., description="浏览量")
    like_count: int = Field(..., description="点赞数")
    comment_count: int = Field(..., description="评论数")
    created_at: datetime = Field(..., description="创建时间")
    match_score: float = Field(..., description="匹配分数", ge=0, le=1)


class NewsRecommendationItem(BaseModel):
    """新闻推荐项"""
    news_id: int = Field(..., description="新闻ID")
    title: str = Field(..., description="标题")
    summary: str | None = Field(None, description="摘要")
    category: str | None = Field(None, description="分类")
    view_count: int = Field(..., description="浏览量")
    created_at: datetime = Field(..., description="创建时间")
    match_score: float = Field(..., description="匹配分数", ge=0, le=1)


class PersonalizedRecommendationsResponse(BaseModel):
    """个性化推荐响应"""
    user_id: int = Field(..., description="用户ID")
    lawyers: list[LawyerRecommendationItem] = Field(
        default_factory=list, description="律师推荐")
    posts: list[PostRecommendationItem] = Field(
        default_factory=list, description="帖子推荐")
    news: list[NewsRecommendationItem] = Field(
        default_factory=list, description="新闻推荐")
    similar_users_content: list[dict[str, Any]] = Field(
        default_factory=list, description="相似用户喜欢的内容")


class RecommendationRequest(BaseModel):
    """推荐请求"""
    lawyer_limit: int = Field(default=5, description="律师推荐数量", ge=1, le=20)
    post_limit: int = Field(default=5, description="帖子推荐数量", ge=1, le=20)
    news_limit: int = Field(default=5, description="新闻推荐数量", ge=1, le=20)


class OnboardingAnswer(BaseModel):
    """引导问卷答案"""

    answers: dict[str, Any] = Field(
        default_factory=dict, description="答案字典（key=问题ID）")


class InteractionRequest(BaseModel):
    """用户交互请求"""

    content_id: str = Field(..., description="内容ID")
    content_type: str = Field(..., description="内容类型")
    tags: list[str] = Field(default_factory=list, description="标签")
    interaction_type: str = Field(default="viewed", description="交互类型")
    weight: float = Field(default=1.0, description="权重")
