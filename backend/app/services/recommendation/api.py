from __future__ import annotations

from . import RecommendationService

__all__ = ["RecommendationService", "get_personalized_recommendations_request"]

from . import (
    get_personalized_recommendations_request,
    get_onboarding_survey_request,
    complete_onboarding_request,
    check_should_onboarding_request,
    get_enhanced_recommendations_request,
    record_interaction_request,
    get_recommendation_weights_request,
    recommend_lawyers_request,
    recommend_forum_posts_request,
    recommend_news_request,
    recommend_similar_users_content_request,
)
