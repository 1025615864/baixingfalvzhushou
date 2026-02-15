from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ...models.user import User
from ...schemas.recommendation import (
    InteractionRequest,
    OnboardingAnswer,
    PersonalizedRecommendationsResponse,
)
from ...services.recommendation import (
    get_cold_start_service,
    get_enhanced_recommendation_service,
    record_user_interaction,
)
from ...services.recommendation_service import RecommendationService


async def get_personalized_recommendations_request(
    *,
    current_user: User,
    db: AsyncSession,
    lawyer_limit: int = 5,
    post_limit: int = 5,
    news_limit: int = 5,
) -> PersonalizedRecommendationsResponse:
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


async def get_onboarding_survey_request() -> dict[str, Any]:
    service = get_cold_start_service()
    return {
        "survey": service.get_onboarding_survey(),
    }


async def complete_onboarding_request(
    *,
    body: OnboardingAnswer,
    current_user: User,
) -> dict[str, Any]:
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


async def check_should_onboarding_request(
    *,
    current_user: User,
) -> dict[str, bool]:
    service = get_cold_start_service()
    return {
        "should_show": service.should_show_onboarding(current_user.id),
    }


async def get_enhanced_recommendations_request(
    *,
    current_user: User,
    recommendation_type: str = "hybrid",
    limit: int = 10,
) -> dict[str, Any]:
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
                "metadata": item.metadata,
            }
            for item in result.items
        ],
        "total": result.total,
        "source": result.source,
    }


async def record_interaction_request(
    *,
    payload: InteractionRequest,
    current_user: User,
) -> dict[str, bool]:
    record_user_interaction(
        user_id=current_user.id,
        content_id=payload.content_id,
        content_type=payload.content_type,
        tags=payload.tags,
        interaction_type=payload.interaction_type,
        weight=payload.weight,
    )
    return {"success": True}


async def get_recommendation_weights_request(
    *,
    current_user: User,
) -> dict[str, dict[str, float]]:
    service = get_cold_start_service()
    return {
        "weights": service.get_recommendation_weights(current_user.id),
    }


async def recommend_lawyers_request(
    *,
    current_user: User,
    db: AsyncSession,
    limit: int = 10,
) -> dict[str, Any]:
    lawyers = await RecommendationService.recommend_lawyers(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )
    return {"lawyers": lawyers}


async def recommend_forum_posts_request(
    *,
    current_user: User,
    db: AsyncSession,
    limit: int = 10,
) -> dict[str, Any]:
    posts = await RecommendationService.recommend_forum_posts(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )
    return {"posts": posts}


async def recommend_news_request(
    *,
    current_user: User,
    db: AsyncSession,
    limit: int = 10,
) -> dict[str, Any]:
    news = await RecommendationService.recommend_news(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )
    return {"news": news}


async def recommend_similar_users_content_request(
    *,
    current_user: User,
    db: AsyncSession,
    limit: int = 10,
) -> dict[str, Any]:
    content = await RecommendationService.recommend_similar_users_content(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )
    return {"content": content}
