from __future__ import annotations

from .recommendation import RecommendationService

recommendation_service = RecommendationService()


def _generate_lawyer_reason(lawyer) -> str:
    raise NotImplementedError


def _generate_post_reason(post) -> str:
    raise NotImplementedError


def _generate_news_reason(news) -> str:
    raise NotImplementedError


__all__ = [
    "RecommendationService",
    "recommendation_service",
    "_generate_lawyer_reason",
    "_generate_post_reason",
    "_generate_news_reason",
]
