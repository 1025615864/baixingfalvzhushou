from __future__ import annotations

from pydantic import BaseModel, Field


class InteractionRequest(BaseModel):
    content_id: str
    content_type: str
    tags: list[str] = []
    interaction_type: str = "viewed"
    weight: float = 1.0


class OnboardingRequest(BaseModel):
    answers: dict = {}


class FeedbackRequest(BaseModel):
    recommendation_id: str
    rating: float
    reason: str | None = None


class LawyerRecommendationItem(BaseModel):
    lawyer_id: int
    lawyer_name: str
    avatar: str | None = None
    specialties: str | None = None
    rating: float
    review_count: int
    consultation_count: int
    is_verified: bool
    match_score: float


class PostRecommendationItem(BaseModel):
    post_id: int
    title: str
    content: str | None = None
    author_id: int
    author_name: str
    view_count: int
    like_count: int
    comment_count: int
    created_at: str
    match_score: float


class NewsRecommendationItem(BaseModel):
    news_id: int
    title: str
    summary: str | None = None
    category: str | None = None
    view_count: int
    created_at: str
    match_score: float


class KnowledgeRecommendationItem(BaseModel):
    knowledge_id: int
    title: str
    category: str | None = None
    summary: str | None = None
    view_count: int
    score: float


class EnhancedRecommendationItem(BaseModel):
    id: str
    type: str
    title: str
    score: float
    reason: str
    metadata: dict


class PersonalizedRecommendationsResponse(BaseModel):
    user_id: int
    lawyers: list[LawyerRecommendationItem] = []
    posts: list[PostRecommendationItem] = []
    news: list[NewsRecommendationItem] = []
    similar_users_content: list[dict] = []


class EnhancedRecommendationsResponse(BaseModel):
    items: list[EnhancedRecommendationItem] = []
    total: int = 0
    source: str = ""


class EnhancedHomeResponse(BaseModel):
    user_id: int
    is_cold_start: bool = False
    profile: dict = {}
    lawyers: list[dict] = []
    posts: list[dict] = []
    news: list[dict] = []
    knowledge: list[dict] = []
    hot_content: list[dict] = []
    reason: str = ""
    recommendation_source: str = ""
    generated_at: str = ""


class HomeRecommendationsResponse(BaseModel):
    lawyers: list[dict] = []
    posts: list[dict] = []
    news: list[dict] = []
    knowledge: list[dict] = []


class SurveyResponse(BaseModel):
    survey: list[dict] = []


class OnboardingProfileResponse(BaseModel):
    success: bool
    profile: dict = {}


class ShouldOnboardingResponse(BaseModel):
    should_show: bool


class WeightsResponse(BaseModel):
    weights: dict = {}


class LawyerListResponse(BaseModel):
    lawyers: list[LawyerRecommendationItem] = []
    total: int = 0
    recommendation_source: str = ""
    generated_at: str = ""


class PostListResponse(BaseModel):
    posts: list[PostRecommendationItem] = []
    total: int = 0
    recommendation_source: str = ""
    generated_at: str = ""


class NewsListResponse(BaseModel):
    news: list[NewsRecommendationItem] = []
    total: int = 0
    recommendation_source: str = ""
    generated_at: str = ""


class KnowledgeListResponse(BaseModel):
    knowledge: list[KnowledgeRecommendationItem] = []


class InteractionResponse(BaseModel):
    success: bool


class FeedbackResponse(BaseModel):
    success: bool
    message: str = ""
    recorded_at: str = ""