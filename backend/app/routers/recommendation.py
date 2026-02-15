"""个性化推荐API路由"""
from typing import Any, Annotated
from typing_extensions import TypedDict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..schemas.recommendation import (
    InteractionRequest,
    OnboardingAnswer,
    PersonalizedRecommendationsResponse,
)
from ..services.recommendation_service import RecommendationService
from ..services.recommendation import (
    get_enhanced_recommendation_service,
    get_cold_start_service,
    record_user_interaction,
)
from ..database import get_db
from ..utils.deps import get_current_user

router = APIRouter(prefix="/recommendation", tags=["个性化推荐"])


class OnboardingSurveyResponse(TypedDict):
    survey: list[dict[str, Any]]


class OnboardingProfileResponse(TypedDict):
    success: bool
    profile: dict


class ShouldOnboardingResponse(TypedDict):
    should_show: bool


class EnhancedRecommendationItem(TypedDict):
    id: str
    type: str
    title: str
    score: float
    reason: str
    metadata: Any


class EnhancedRecommendationsResponse(TypedDict):
    items: list[EnhancedRecommendationItem]
    total: int
    source: str


@router.get(
    "/personalized",
    response_model=PersonalizedRecommendationsResponse,
    summary="个性化推荐",
)
async def get_personalized_recommendations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    lawyer_limit: Annotated[int, Query(description="律师推荐数量", ge=1, le=20)] = 5,
    post_limit: Annotated[int, Query(description="帖子推荐数量", ge=1, le=20)] = 5,
    news_limit: Annotated[int, Query(description="新闻推荐数量", ge=1, le=20)] = 5,
):
    """
    获取个性化推荐

    根据用户兴趣标签推荐律师、论坛帖子和新闻
    """
    recommendations = await RecommendationService.get_personalized_recommendations(
        db=db,
        user_id=current_user.id,
        lawyer_limit=lawyer_limit,
        post_limit=post_limit,
        news_limit=news_limit,
    )

    return PersonalizedRecommendationsResponse(
        user_id=current_user.id,
        lawyers=recommendations.get("lawyers", []),
        posts=recommendations.get("posts", []),
        news=recommendations.get("news", []),
        similar_users_content=recommendations.get("similar_users_content", []),
    )


@router.get("/survey", summary="获取引导问卷")
async def get_onboarding_survey() -> OnboardingSurveyResponse:
    """获取引导问卷"""
    service = get_cold_start_service()
    return {
        "survey": service.get_onboarding_survey(),
    }


@router.post("/onboarding", summary="完成引导问卷")
async def complete_onboarding(
    body: OnboardingAnswer,
    current_user: Annotated[User, Depends(get_current_user)],
) -> OnboardingProfileResponse:
    """完成引导问卷，构建用户画像"""
    service = get_cold_start_service()
    profile = service.process_onboarding_answers(
        user_id=current_user.id,
        answers=body.answers,
    )
    return {
        "success": True,
        "profile": {
            "interest_tags": profile.interest_tags,
            "interest_weights": profile.interest_weights,
            "preferred_content_types": profile.preferred_content_types,
            "usage_frequency": profile.usage_frequency,
            "onboarding_completed": profile.onboarding_completed,
        },
    }


@router.get("/should-onboarding", summary="检查是否需要引导")
async def check_should_onboarding(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """检查是否应该显示引导"""
    service = get_cold_start_service()
    return {
        "should_show": service.should_show_onboarding(current_user.id),
    }


@router.get("/enhanced", summary="增强个性化推荐")
async def get_enhanced_recommendations(
    current_user: Annotated[User, Depends(get_current_user)],
    recommendation_type: str = "hybrid",
    limit: int = 10,
) -> EnhancedRecommendationsResponse:
    """获取增强版个性化推荐"""
    service = get_enhanced_recommendation_service()
    result = await service.get_recommendations(
        user_id=current_user.id,
        recommendation_type=recommendation_type,
        limit=limit,
    )
    return {
        "items": [
            {
                "id": item.item_id,
                "type": item.item_type,
                "title": item.title,
                "score": item.score,
                "reason": item.reason,
                # pyright: ignore[reportUnknownMemberType]
                "metadata": item.metadata,
            }
            for item in result.items
        ],
        "total": result.total,
        "source": result.source,
    }


@router.post("/interaction", summary="记录用户交互")
async def record_interaction(
    request: InteractionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """记录用户交互"""
    record_user_interaction(
        user_id=current_user.id,
        content_id=request.content_id,
        content_type=request.content_type,
        tags=request.tags,
        interaction_type=request.interaction_type,
        weight=request.weight,
    )
    return {"success": True}


@router.get("/weights", summary="获取推荐权重")
async def get_recommendation_weights(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取推荐权重"""
    service = get_cold_start_service()
    return {
        "weights": service.get_recommendation_weights(current_user.id),
    }


@router.get(
    "/lawyers",
    summary="推荐律师",
)
async def recommend_lawyers(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(description="推荐数量", ge=1, le=20)] = 10,
):
    """
    推荐律师

    根据用户兴趣标签推荐律师
    """
    lawyers = await RecommendationService.recommend_lawyers(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )
    return {"lawyers": lawyers}


@router.get(
    "/posts",
    summary="推荐论坛帖子",
)
async def recommend_forum_posts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(description="推荐数量", ge=1, le=20)] = 10,
):
    """
    推荐论坛帖子

    根据用户兴趣标签推荐论坛帖子
    """
    posts = await RecommendationService.recommend_forum_posts(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )
    return {"posts": posts}


@router.get(
    "/news",
    summary="推荐新闻",
)
async def recommend_news(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(description="推荐数量", ge=1, le=20)] = 10,
):
    """
    推荐新闻

    根据用户兴趣标签推荐新闻
    """
    news = await RecommendationService.recommend_news(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )
    return {"news": news}


@router.get(
    "/similar-users-content",
    summary="推荐相似用户喜欢的内容",
)
async def recommend_similar_users_content(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(description="推荐数量", ge=1, le=20)] = 10,
):
    """
    推荐相似用户喜欢的内容

    基于协同过滤，推荐与当前用户兴趣相似的用户喜欢的内容
    """
    content = await RecommendationService.recommend_similar_users_content(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )
    return {"content": content}
