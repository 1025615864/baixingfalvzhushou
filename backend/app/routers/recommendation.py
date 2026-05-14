from datetime import datetime, timezone
from hashlib import md5
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..services.recommendation import RecommendationService
from ..services.cache_service import cache_service
from ..schemas.recommendation import (
    InteractionRequest,
    OnboardingRequest,
    FeedbackRequest,
)
from ..utils.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/recommendation", tags=["Recommendation"])


def _get_recommendation_service(
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
) -> RecommendationService:
    return RecommendationService(db, user)


def _map_lawyer_item(lawyer: dict) -> dict:
    return {
        "lawyer_id": lawyer.get("id"),
        "lawyer_name": lawyer.get("name"),
        "avatar": lawyer.get("avatar"),
        "specialties": lawyer.get("specialties"),
        "rating": lawyer.get("rating", 0),
        "review_count": lawyer.get("review_count", 0),
        "consultation_count": lawyer.get("consultation_count", 0),
        "is_verified": lawyer.get("is_verified", False),
        "match_score": lawyer.get("match_score", 0),
    }


def _map_post_item(post: dict) -> dict:
    return {
        "post_id": post.get("id"),
        "title": post.get("title", ""),
        "content": post.get("content"),
        "author_id": post.get("author_id"),
        "author_name": post.get("author_name", ""),
        "view_count": post.get("view_count", 0),
        "like_count": post.get("like_count", 0),
        "comment_count": post.get("comment_count", 0),
        "created_at": post.get("created_at", ""),
        "match_score": post.get("match_score", 0),
    }


def _map_news_item(news: dict) -> dict:
    return {
        "news_id": news.get("id"),
        "title": news.get("title", ""),
        "summary": news.get("summary"),
        "category": news.get("category"),
        "view_count": news.get("view_count", 0),
        "created_at": news.get("created_at", ""),
        "match_score": news.get("match_score", 0),
    }


def _map_knowledge_item(knowledge: dict) -> dict:
    return {
        "knowledge_id": knowledge.get("id"),
        "title": knowledge.get("title", ""),
        "category": knowledge.get("category"),
        "summary": knowledge.get("summary"),
        "view_count": knowledge.get("view_count", 0),
        "score": knowledge.get("match_score", knowledge.get("score", 0)),
    }


def _cache_key(user_id: Optional[int], endpoint: str, **params) -> str:
    uid = str(user_id) if user_id else "anon"
    params_hash = md5(str(sorted(params.items())).encode()).hexdigest()[:8]
    return f"rec:{uid}:{endpoint}:{params_hash}"


@router.get("/personalized")
async def get_personalized(
    lawyer_limit: int = Query(default=5, ge=1, le=20),
    post_limit: int = Query(default=5, ge=1, le=20),
    news_limit: int = Query(default=5, ge=1, le=20),
    svc: RecommendationService = Depends(_get_recommendation_service),
):
    user_id = svc.user.id if svc.user else None
    ck = _cache_key(user_id, "personalized", lawyer_limit=lawyer_limit, post_limit=post_limit, news_limit=news_limit)
    cached = await cache_service.get_json(ck)
    if cached is not None:
        return cached

    result = await svc.get_personalized_recommendations(
        user_id=user_id,
        lawyer_limit=lawyer_limit,
        post_limit=post_limit,
        news_limit=news_limit,
    )

    data = {
        "user_id": user_id,
        "lawyers": [_map_lawyer_item(l) for l in result.get("lawyers", [])],
        "posts": [_map_post_item(p) for p in result.get("posts", [])],
        "news": [_map_news_item(n) for n in result.get("news", [])],
        "similar_users_content": result.get("similar_users_content", []),
    }

    await cache_service.set_json(ck, data, expire=300)
    return data


@router.get("/enhanced")
async def get_enhanced(
    recommendation_type: str = Query(default="hybrid"),
    limit: int = Query(default=10, ge=1, le=50),
    svc: RecommendationService = Depends(_get_recommendation_service),
):
    user_id = svc.user.id if svc.user else None
    ck = _cache_key(user_id, "enhanced", recommendation_type=recommendation_type, limit=limit)
    cached = await cache_service.get_json(ck)
    if cached is not None:
        return cached

    result = await svc.get_enhanced_recommendations(
        recommendation_type=recommendation_type,
        limit=limit,
    )

    items = result.get("items", [])
    for item in items:
        if item.get("type") == "lawyer" and "metadata" in item:
            item["metadata"] = _map_lawyer_item(item["metadata"])
        elif item.get("type") == "post" and "metadata" in item:
            item["metadata"] = _map_post_item(item["metadata"])
        elif item.get("type") == "news" and "metadata" in item:
            item["metadata"] = _map_news_item(item["metadata"])
        elif item.get("type") == "knowledge" and "metadata" in item:
            item["metadata"] = _map_knowledge_item(item["metadata"])
        if "reason" not in item:
            item["reason"] = ""

    data = {
        "items": items,
        "total": result.get("total", len(items)),
        "source": result.get("source", "hybrid"),
    }

    await cache_service.set_json(ck, data, expire=600)
    return data


@router.get("/enhanced/personalized-home")
async def get_enhanced_personalized_home(
    lawyer_limit: int = Query(default=5, ge=1, le=20),
    post_limit: int = Query(default=5, ge=1, le=20),
    news_limit: int = Query(default=5, ge=1, le=20),
    knowledge_limit: int = Query(default=5, ge=1, le=20),
    svc: RecommendationService = Depends(_get_recommendation_service),
):
    user_id = svc.user.id if svc.user else None
    ck = _cache_key(
        user_id, "enhanced_home",
        lawyer_limit=lawyer_limit, post_limit=post_limit,
        news_limit=news_limit, knowledge_limit=knowledge_limit,
    )
    cached = await cache_service.get_json(ck)
    if cached is not None:
        return cached

    result = await svc.get_enhanced_home(
        user_id=user_id,
        lawyer_limit=lawyer_limit,
        post_limit=post_limit,
        news_limit=news_limit,
        knowledge_limit=knowledge_limit,
    )

    is_cold_start = user_id is None or not result.get("lawyers") and not result.get("knowledge")

    data = {
        "user_id": user_id,
        "is_cold_start": is_cold_start,
        "profile": {
            "interests": list((svc.user and hasattr(svc.user, "interest_tags")) and getattr(svc.user, "interest_tags", []) or []),
            "history_count": 0,
        },
        "lawyers": [_map_lawyer_item(l) for l in result.get("lawyers", [])],
        "posts": [_map_post_item(p) for p in result.get("posts", [])],
        "news": [_map_news_item(n) for n in result.get("news", [])],
        "knowledge": [_map_knowledge_item(k) for k in result.get("knowledge", [])],
        "hot_content": result.get("hot_content", []),
        "reason": "personalized" if user_id and not is_cold_start else "popular",
        "recommendation_source": "hybrid_v1" if user_id else "popular_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    await cache_service.set_json(ck, data, expire=300)
    return data


@router.get("/survey")
async def get_survey(
    svc: RecommendationService = Depends(_get_recommendation_service),
):
    survey = await svc.get_survey()
    return {"survey": survey}


@router.post("/onboarding")
async def complete_onboarding(
    body: OnboardingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = RecommendationService(db, user)
    result = await svc.complete_onboarding(user_id=user.id, answers=body.answers)
    return result


@router.get("/should-onboarding")
async def should_show_onboarding(
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    if not user:
        return {"should_show": True}
    svc = RecommendationService(db, user)
    should = await svc.should_show_onboarding(user_id=user.id)
    return {"should_show": should}


@router.get("/weights")
async def get_weights(
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    if not user:
        return {"weights": {}}
    svc = RecommendationService(db, user)
    result = await svc.get_weights(user_id=user.id)
    return result


@router.get("/lawyers")
async def get_lawyers(
    limit: int = Query(default=10, ge=1, le=50),
    svc: RecommendationService = Depends(_get_recommendation_service),
):
    user_id = svc.user.id if svc.user else None
    ck = _cache_key(user_id, "lawyers", limit=limit)
    cached = await cache_service.get_json(ck)
    if cached is not None:
        return cached

    lawyers = await svc.get_lawyer_recommendations(limit=limit)
    data = {"lawyers": [_map_lawyer_item(l) for l in lawyers]}

    await cache_service.set_json(ck, data, expire=300)
    return data


@router.get("/posts")
async def get_posts(
    limit: int = Query(default=10, ge=1, le=50),
    svc: RecommendationService = Depends(_get_recommendation_service),
):
    user_id = svc.user.id if svc.user else None
    ck = _cache_key(user_id, "posts", limit=limit)
    cached = await cache_service.get_json(ck)
    if cached is not None:
        return cached

    posts = await svc.get_post_recommendations(limit=limit)
    data = {"posts": [_map_post_item(p) for p in posts]}

    await cache_service.set_json(ck, data, expire=300)
    return data


@router.get("/news")
async def get_news(
    limit: int = Query(default=10, ge=1, le=50),
    svc: RecommendationService = Depends(_get_recommendation_service),
):
    user_id = svc.user.id if svc.user else None
    ck = _cache_key(user_id, "news", limit=limit)
    cached = await cache_service.get_json(ck)
    if cached is not None:
        return cached

    news = await svc.get_news_recommendations(limit=limit)
    data = {"news": [_map_news_item(n) for n in news]}

    await cache_service.set_json(ck, data, expire=300)
    return data


@router.post("/interaction")
async def record_interaction(
    body: InteractionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = RecommendationService(db, user)
    result = await svc.record_interaction(
        user_id=user.id,
        content_id=body.content_id,
        content_type=body.content_type,
        tags=body.tags,
        interaction_type=body.interaction_type,
        weight=body.weight,
    )
    return result


@router.get("/lawyers/by-consultation")
async def get_lawyers_by_consultation(
    limit: int = Query(default=10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = RecommendationService(db, user)
    ck = _cache_key(user.id, "lawyers_by_consultation", limit=limit)
    cached = await cache_service.get_json(ck)
    if cached is not None:
        return cached

    lawyers = await svc.get_lawyers_by_consultation(user_id=user.id, limit=limit)
    data = {"lawyers": [_map_lawyer_item(l) for l in lawyers]}

    await cache_service.set_json(ck, data, expire=300)
    return data


@router.get("/lawyers/by-location")
async def get_lawyers_by_location(
    city: str = Query(default="北京"),
    limit: int = Query(default=10, ge=1, le=50),
    svc: RecommendationService = Depends(_get_recommendation_service),
):
    user_id = svc.user.id if svc.user else None
    ck = _cache_key(user_id, "lawyers_by_location", city=city, limit=limit)
    cached = await cache_service.get_json(ck)
    if cached is not None:
        return cached

    lawyers = await svc.get_lawyers_by_location(city=city, limit=limit)
    data = {"lawyers": [_map_lawyer_item(l) for l in lawyers]}

    await cache_service.set_json(ck, data, expire=600)
    return data


@router.get("/knowledge/by-interests")
async def get_knowledge_by_interests(
    limit: int = Query(default=10, ge=1, le=50),
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    svc = RecommendationService(db, user)
    user_id = user.id if user else None

    if not user_id:
        return {"knowledge": []}

    ck = _cache_key(user_id, "knowledge_by_interests", limit=limit)
    cached = await cache_service.get_json(ck)
    if cached is not None:
        return cached

    knowledge = await svc.get_knowledge_recommendations(user_id=user_id, limit=limit)
    data = {"knowledge": [_map_knowledge_item(k) for k in knowledge]}

    await cache_service.set_json(ck, data, expire=300)
    return data


@router.get("/home")
async def get_home(
    recommendation_limit: int = Query(default=10, ge=1, le=50),
    svc: RecommendationService = Depends(_get_recommendation_service),
):
    user_id = svc.user.id if svc.user else None
    ck = _cache_key(user_id, "home", recommendation_limit=recommendation_limit)
    cached = await cache_service.get_json(ck)
    if cached is not None:
        return cached

    result = await svc.get_home_recommendations(recommendation_limit=recommendation_limit)

    data = {
        "lawyers": [_map_lawyer_item(l) for l in result.get("lawyers", [])],
        "posts": [_map_post_item(p) for p in result.get("posts", [])],
        "news": [_map_news_item(n) for n in result.get("news", [])],
        "knowledge": [_map_knowledge_item(k) for k in result.get("knowledge", [])],
    }

    await cache_service.set_json(ck, data, expire=300)
    return data


@router.post("/feedback")
async def submit_feedback(
    body: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = RecommendationService(db, user)
    await svc.submit_feedback(
        user_id=user.id,
        recommendation_id=body.recommendation_id,
        rating=int(body.rating),
        reason=body.reason,
    )
    return {
        "success": True,
        "message": "反馈已记录，感谢您帮助改进推荐系统" if body.rating >= 3 else "反馈已记录，我们会持续优化推荐效果",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
