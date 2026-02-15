"""论坛助手路由 - 提供智能回复建议和内容推荐"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...utils.deps import get_current_user_optional
from ...models.user import User
from ...services.forum_ai_service import forum_ai_service

router = APIRouter(prefix="/assistant", tags=["论坛助手"])


# ============ 请求/响应模型 ============

class SmartReplySuggestionResponse(BaseModel):
    """智能回复建议响应"""
    id: str = Field(..., description="建议ID")
    content: str = Field(..., description="建议内容")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    category: str = Field(..., description="类别")
    context: str = Field(..., description="上下文")
    tags: list[str] = Field(default_factory=list, description="标签")
    created_at: str = Field(..., description="创建时间")


class GetSmartRepliesRequest(BaseModel):
    """获取智能回复请求"""
    post_id: str = Field(..., description="帖子ID")
    context: dict | None = Field(None, description="上下文信息")
    count: int = Field(default=3, ge=1, le=10, description="建议数量")


class GetSmartRepliesResponse(BaseModel):
    """获取智能回复响应"""
    suggestions: list[SmartReplySuggestionResponse]
    total: int


class AdoptSmartReplyRequest(BaseModel):
    """采纳智能回复请求"""
    suggestion_id: str = Field(..., description="建议ID")
    post_id: str = Field(..., description="帖子ID")
    modified_content: str | None = Field(None, description="修改后的内容")


class AdoptSmartReplyResponse(BaseModel):
    """采纳智能回复响应"""
    success: bool
    message: str
    reply_id: str | None = None


class ContentRecommendationItem(BaseModel):
    """内容推荐项"""
    id: str
    type: str = Field(..., description="类型: post/article/question/expert")
    title: str
    summary: str
    author: dict | None = None
    tags: list[str] = Field(default_factory=list)
    relevance_score: float = Field(..., ge=0, le=1)
    view_count: int = Field(default=0)
    like_count: int = Field(default=0)
    reply_count: int = Field(default=0)
    created_at: str
    thumbnail_url: str | None = None


class RecommendationReason(BaseModel):
    """推荐原因"""
    type: str = Field(..., description="similar_content/trending/expert_recommendation/user_interest/related_topic")
    description: str
    matched_tags: list[str] | None = None


class EnhancedRecommendation(BaseModel):
    """增强的内容推荐"""
    item: ContentRecommendationItem
    reason: RecommendationReason
    rank: int


class GetRecommendationsResponse(BaseModel):
    """获取推荐响应"""
    recommendations: list[EnhancedRecommendation]
    total: int
    has_more: bool


class FeedbackRecommendationRequest(BaseModel):
    """反馈推荐请求"""
    recommendation_id: str
    feedback: str = Field(..., description="useful/not_useful/irrelevant")
    reason: str | None = None


class FeedbackRecommendationResponse(BaseModel):
    """反馈推荐响应"""
    success: bool
    message: str


class AssistantConfigResponse(BaseModel):
    """助手配置响应"""
    enabled: bool
    auto_suggest: bool
    suggestion_count: int = Field(..., ge=1, le=10)
    min_confidence: float = Field(..., ge=0, le=1)
    preferred_categories: list[str] = Field(default_factory=list)


class UpdateAssistantConfigRequest(BaseModel):
    """更新助手配置请求"""
    enabled: bool | None = None
    auto_suggest: bool | None = None
    suggestion_count: int | None = Field(None, ge=1, le=10)
    min_confidence: float | None = Field(None, ge=0, le=1)
    preferred_categories: list[str] | None = None


class UpdateAssistantConfigResponse(BaseModel):
    """更新助手配置响应"""
    success: bool
    config: AssistantConfigResponse


class TrendingTopic(BaseModel):
    """热门话题"""
    id: str
    name: str
    hot_score: float
    post_count: int


class GetTrendingTopicsResponse(BaseModel):
    """获取热门话题响应"""
    topics: list[TrendingTopic]


class RelatedExpert(BaseModel):
    """相关专家"""
    id: str
    name: str
    avatar: str | None = None
    title: str
    specialty: list[str] = Field(default_factory=list)
    follower_count: int = Field(default=0)
    reply_count: int = Field(default=0)
    satisfaction_rate: float = Field(default=0.0, ge=0, le=1)


class GetRelatedExpertsResponse(BaseModel):
    """获取相关专家响应"""
    experts: list[RelatedExpert]


# ============ 路由端点 ============

@router.post("/replies", response_model=GetSmartRepliesResponse)
async def get_smart_reply_suggestions(
    request: GetSmartRepliesRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> GetSmartRepliesResponse:
    """获取智能回复建议"""
    try:
        # 使用论坛AI服务生成智能回复建议
        suggestions_data = await forum_ai_service.generate_smart_reply_suggestions(
            db=db,
            post_id=int(request.post_id),
            count=request.count
        )

        # 转换为响应模型
        suggestions = [
            SmartReplySuggestionResponse(
                id=s["id"],
                content=s["content"],
                confidence=s["confidence"],
                category=s["category"],
                context=s["context"],
                tags=s["tags"],
                created_at=s["created_at"],
            )
            for s in suggestions_data
        ]

        return GetSmartRepliesResponse(
            suggestions=suggestions,
            total=len(suggestions),
        )
    except Exception as e:
        # 如果出错，返回默认建议
        suggestions = [
            SmartReplySuggestionResponse(
                id=f"suggestion-{i}",
                content=f"根据您的描述，建议您可以参考相关法律法规。如有需要，建议咨询专业律师获取针对性建议。",
                confidence=0.8 - i * 0.05,
                category="general",
                context="用户咨询法律问题",
                tags=["法律", "咨询"],
                created_at="2024-01-15T10:00:00Z",
            )
            for i in range(min(request.count, 3))
        ]

        return GetSmartRepliesResponse(
            suggestions=suggestions,
            total=len(suggestions),
        )


@router.post("/replies/adopt", response_model=AdoptSmartReplyResponse)
async def adopt_smart_reply(
    request: AdoptSmartReplyRequest,
    db=Depends(get_db),
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> AdoptSmartReplyResponse:
    """采纳智能回复"""
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    
    # TODO: 实际业务逻辑 - 创建回复记录
    return AdoptSmartReplyResponse(
        success=True,
        message="采纳成功",
        reply_id=f"reply-{request.suggestion_id}",
    )


@router.get("/recommendations", response_model=GetRecommendationsResponse)
async def get_content_recommendations(
    category: str | None = None,
    limit: int = 10,
    offset: int = 0,
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    db: AsyncSession = Depends(get_db),
) -> GetRecommendationsResponse:
    """获取内容推荐"""
    try:
        # 使用论坛AI服务获取推荐
        user_id = current_user.id if current_user else None
        recommendations_data = await forum_ai_service.get_content_recommendations(
            db=db,
            user_id=user_id,
            category=category,
            limit=limit,
            offset=offset
        )

        # 转换为响应模型
        recommendations = [
            EnhancedRecommendation(
                item=ContentRecommendationItem(
                    id=item["item"]["id"],
                    type=item["item"]["type"],
                    title=item["item"]["title"],
                    summary=item["item"]["summary"],
                    author=item["item"].get("author"),
                    tags=item["item"].get("tags", []),
                    relevance_score=item["item"]["relevance_score"],
                    view_count=item["item"].get("view_count", 0),
                    like_count=item["item"].get("like_count", 0),
                    reply_count=item["item"].get("reply_count", 0),
                    created_at=item["item"]["created_at"],
                ),
                reason=RecommendationReason(
                    type=item["reason"]["type"],
                    description=item["reason"]["description"],
                    matched_tags=item["reason"].get("matched_tags"),
                ),
                rank=item["rank"],
            )
            for item in recommendations_data
        ]

        return GetRecommendationsResponse(
            recommendations=recommendations,
            total=len(recommendations) + offset + (1 if len(recommendations) == limit else 0),
            has_more=len(recommendations) == limit,
        )
    except Exception as e:
        # 如果出错，返回空列表
        return GetRecommendationsResponse(
            recommendations=[],
            total=0,
            has_more=False,
        )


@router.post("/recommendations/feedback", response_model=FeedbackRecommendationResponse)
async def feedback_recommendation(
    request: FeedbackRecommendationRequest,
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    db: AsyncSession = Depends(get_db),
) -> FeedbackRecommendationResponse:
    """反馈推荐内容"""
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")

    try:
        # 使用论坛AI服务记录反馈
        await forum_ai_service.record_feedback(
            db=db,
            user_id=current_user.id,
            recommendation_id=request.recommendation_id,
            feedback=request.feedback,
            reason=request.reason
        )

        return FeedbackRecommendationResponse(
            success=True,
            message="反馈已提交",
        )
    except Exception as e:
        return FeedbackRecommendationResponse(
            success=False,
            message=f"反馈提交失败: {str(e)}",
        )


@router.get("/config", response_model=AssistantConfigResponse)
async def get_assistant_config(
    db=Depends(get_db),
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> AssistantConfigResponse:
    """获取助手配置"""
    # TODO: 从数据库或缓存获取用户配置
    return AssistantConfigResponse(
        enabled=True,
        auto_suggest=True,
        suggestion_count=3,
        min_confidence=0.7,
        preferred_categories=["trending", "related", "expert"],
    )


@router.put("/config", response_model=UpdateAssistantConfigResponse)
async def update_assistant_config(
    request: UpdateAssistantConfigRequest,
    db=Depends(get_db),
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> UpdateAssistantConfigResponse:
    """更新助手配置"""
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    
    # TODO: 保存配置到数据库
    config = AssistantConfigResponse(
        enabled=request.enabled if request.enabled is not None else True,
        auto_suggest=request.auto_suggest if request.auto_suggest is not None else True,
        suggestion_count=request.suggestion_count or 3,
        min_confidence=request.min_confidence or 0.7,
        preferred_categories=request.preferred_categories or ["trending", "related"],
    )
    
    return UpdateAssistantConfigResponse(
        success=True,
        config=config,
    )


@router.get("/trending-topics", response_model=GetTrendingTopicsResponse)
async def get_trending_topics(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> GetTrendingTopicsResponse:
    """获取热门话题"""
    try:
        # 使用论坛AI服务获取热门话题
        topics_data = await forum_ai_service.get_trending_topics(db=db, limit=limit)

        # 转换为响应模型
        topics = [
            TrendingTopic(
                id=t["id"],
                name=t["name"],
                hot_score=t["hot_score"],
                post_count=t["post_count"],
            )
            for t in topics_data
        ]

        return GetTrendingTopicsResponse(topics=topics)
    except Exception as e:
        # 如果出错，返回空列表
        return GetTrendingTopicsResponse(topics=[])


@router.get("/related-experts", response_model=GetRelatedExpertsResponse)
async def get_related_experts(
    topic: str | None = None,
    limit: int = 5,
    db=Depends(get_db),
) -> GetRelatedExpertsResponse:
    """获取相关专家"""
    # TODO: 从律师服务获取相关专家
    experts = [
        RelatedExpert(
            id=f"expert-{i}",
            name=f"专家{i}",
            title="资深律师",
            specialty=["劳动法", "合同法"],
            follower_count=100 + i * 20,
            reply_count=50 + i * 10,
            satisfaction_rate=0.95 - i * 0.02,
        )
        for i in range(min(limit, 3))
    ]
    
    return GetRelatedExpertsResponse(experts=experts)