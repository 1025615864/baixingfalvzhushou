from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass


class RecommendationService:
    async def get_personalized_recommendations(self, db, user_id, lawyer_limit=5, post_limit=5, news_limit=5):
        return {"lawyers": [], "posts": [], "news": [], "similar_users_content": []}

    @staticmethod
    async def recommend_lawyers(db, user_id, limit=10):
        return []

    @staticmethod
    async def recommend_forum_posts(db, user_id, limit=10):
        return []

    @staticmethod
    async def recommend_news(db, user_id, limit=10):
        return []

    @staticmethod
    async def recommend_similar_users_content(db, user_id, limit=10):
        return []


@dataclass
class PersonalizedRecommendationsResponse:
    user_id: int
    lawyers: list = None
    posts: list = None
    news: list = None

    def __post_init__(self):
        if self.lawyers is None:
            self.lawyers = []
        if self.posts is None:
            self.posts = []
        if self.news is None:
            self.news = []


@dataclass
class LawyerRecommendation:
    lawyer_id: int
    lawyer_name: str = ""
    rating: float = 0.0
    review_count: int = 0
    consultation_count: int = 0
    is_verified: bool = False
    match_score: float = 0.0


@dataclass
class PostRecommendation:
    post_id: int
    title: str = ""
    author_id: int = 0
    author_name: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    created_at: Any = None
    match_score: float = 0.0


@dataclass
class NewsRecommendation:
    news_id: int
    title: str = ""
    view_count: int = 0
    created_at: Any = None
    match_score: float = 0.0


def _convert_lawyers(raw_lawyers):
    return [LawyerRecommendation(
        lawyer_id=l.get("lawyer_id", 0),
        lawyer_name=l.get("lawyer_name", ""),
        rating=l.get("rating", 0.0),
        review_count=l.get("review_count", 0),
        consultation_count=l.get("consultation_count", 0),
        is_verified=l.get("is_verified", False),
        match_score=l.get("match_score", 0.0),
    ) for l in raw_lawyers]


def _convert_posts(raw_posts):
    return [PostRecommendation(
        post_id=p.get("post_id", 0),
        title=p.get("title", ""),
        author_id=p.get("author_id", 0),
        author_name=p.get("author_name", ""),
        view_count=p.get("view_count", 0),
        like_count=p.get("like_count", 0),
        comment_count=p.get("comment_count", 0),
        created_at=p.get("created_at"),
        match_score=p.get("match_score", 0.0),
    ) for p in raw_posts]


def _convert_news(raw_news):
    return [NewsRecommendation(
        news_id=n.get("news_id", 0),
        title=n.get("title", ""),
        view_count=n.get("view_count", 0),
        created_at=n.get("created_at"),
        match_score=n.get("match_score", 0.0),
    ) for n in raw_news]


async def get_personalized_recommendations_request(current_user=None, db=None, lawyer_limit=5, post_limit=5, news_limit=5):
    data = await RecommendationService.get_personalized_recommendations(
        db=db, user_id=current_user.id, lawyer_limit=lawyer_limit, post_limit=post_limit, news_limit=news_limit
    )
    return PersonalizedRecommendationsResponse(
        user_id=current_user.id,
        lawyers=_convert_lawyers(data.get("lawyers", [])),
        posts=_convert_posts(data.get("posts", [])),
        news=_convert_news(data.get("news", [])),
    )


async def get_onboarding_survey_request():
    from app.services.recommendation.api import get_cold_start_service
    try:
        service = get_cold_start_service()
        survey = service.get_onboarding_survey()
    except Exception:
        survey = []
    return {"survey": survey}


async def complete_onboarding_request(body=None, current_user=None):
    from app.services.recommendation.api import get_cold_start_service
    try:
        service = get_cold_start_service()
        answers = body.answers if body else {}
        profile = service.process_onboarding_answers(user_id=current_user.id, answers=answers)
        return {
            "success": True,
            "profile": {
                "interest_tags": getattr(profile, 'interest_tags', []),
                "interest_weights": getattr(profile, 'interest_weights', {}),
                "preferred_content_types": getattr(profile, 'preferred_content_types', []),
                "usage_frequency": getattr(profile, 'usage_frequency', ''),
                "onboarding_completed": getattr(profile, 'onboarding_completed', True),
            }
        }
    except Exception:
        return {"success": False, "profile": {}}


async def check_should_onboarding_request(current_user=None):
    from app.services.recommendation.api import get_cold_start_service
    try:
        service = get_cold_start_service()
        should_show = service.should_show_onboarding(current_user.id)
    except Exception:
        should_show = False
    return {"should_show": should_show}


async def get_enhanced_recommendations_request(current_user=None, recommendation_type="hybrid", limit=10):
    from app.services.recommendation.api import get_enhanced_recommendation_service
    try:
        service = get_enhanced_recommendation_service()
        result = await service.get_recommendations(user_id=current_user.id, recommendation_type=recommendation_type, limit=limit)
        items = []
        for item in getattr(result, 'items', []):
            items.append({
                "id": getattr(item, 'item_id', 0),
                "type": getattr(item, 'item_type', ''),
                "title": getattr(item, 'title', ''),
                "score": getattr(item, 'score', 0.0),
                "reason": getattr(item, 'reason', ''),
                "metadata": getattr(item, 'metadata', {}),
            })
        return {
            "items": items,
            "total": getattr(result, 'total', len(items)),
        }
    except Exception:
        return {"items": [], "total": 0}


async def record_interaction_request(payload=None, current_user=None):
    from app.services.recommendation.api import record_user_interaction
    try:
        await record_user_interaction(
            user_id=current_user.id,
            content_id=str(payload.content_id) if payload else "",
            content_type=payload.content_type if payload else "",
            tags=payload.tags if payload else [],
            interaction_type=payload.interaction_type if payload else "",
            weight=payload.weight if payload else 1.0,
        )
    except Exception:
        pass
    return {"success": True}


async def get_recommendation_weights_request(current_user=None):
    from app.services.recommendation.api import get_cold_start_service
    try:
        service = get_cold_start_service()
        weights = service.get_recommendation_weights()
    except Exception:
        weights = {}
    return {"weights": weights}


async def recommend_lawyers_request(current_user=None, db=None, limit=10):
    result = await RecommendationService.recommend_lawyers(db=db, user_id=current_user.id, limit=limit)
    return {"lawyers": result}


async def recommend_forum_posts_request(current_user=None, db=None, limit=10):
    result = await RecommendationService.recommend_forum_posts(db=db, user_id=current_user.id, limit=limit)
    return {"posts": result}


async def recommend_news_request(current_user=None, db=None, limit=10):
    result = await RecommendationService.recommend_news(db=db, user_id=current_user.id, limit=limit)
    return {"news": result}


async def recommend_similar_users_content_request(current_user=None, db=None, limit=10):
    result = await RecommendationService.recommend_similar_users_content(db=db, user_id=current_user.id, limit=limit)
    return {"content": result}


def get_cold_start_service():
    return None


def get_enhanced_recommendation_service():
    return None


async def record_user_interaction(user_id, content_id="", content_type="", tags=None, interaction_type="", weight=1.0):
    pass
