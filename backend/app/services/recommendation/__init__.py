from __future__ import annotations


class RecommendationService:
    async def get_personalized_recommendations(self, db, user_id, lawyer_limit=5):
        raise NotImplementedError


async def get_personalized_recommendations_request(current_user=None, db=None, lawyer_limit=5):
    raise NotImplementedError


async def get_onboarding_survey_request(current_user=None, db=None):
    raise NotImplementedError


async def complete_onboarding_request(current_user=None, db=None, answers=None):
    raise NotImplementedError


async def check_should_onboarding_request(current_user=None, db=None):
    raise NotImplementedError


async def get_enhanced_recommendations_request(current_user=None, db=None):
    raise NotImplementedError


async def record_interaction_request(current_user=None, db=None, data=None):
    raise NotImplementedError


async def get_recommendation_weights_request(current_user=None, db=None):
    raise NotImplementedError


async def recommend_lawyers_request(current_user=None, db=None):
    raise NotImplementedError


async def recommend_forum_posts_request(current_user=None, db=None):
    raise NotImplementedError


async def recommend_news_request(current_user=None, db=None):
    raise NotImplementedError


async def recommend_similar_users_content_request(current_user=None, db=None):
    raise NotImplementedError
