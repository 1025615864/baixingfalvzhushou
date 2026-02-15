"""新闻推荐 API 路由

提供个性化推荐、用户行为追踪、相似新闻等功能
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..utils.deps import get_current_user, get_current_user_optional
from ..services.news_recommendation_service import news_recommendation_service
from ..services.news_quality_service import news_quality_service
from ..services.news_service import news_service

router = APIRouter(prefix="/news/recommendations", tags=["新闻推荐"])


class NewsRecommendationItem(BaseModel):
    """推荐新闻项"""
    news_id: int
    title: str
    category: str
    score: float
    reason: str
    is_new: bool
    is_high_quality: bool


class RecommendationResponse(BaseModel):
    """推荐结果响应"""
    items: list[NewsRecommendationItem]
    total: int


class QualityAssessmentResponse(BaseModel):
    """质量评估响应"""
    legal_professional: dict
    content_quality: dict
    summary: dict


class TrendingNewsResponse(BaseModel):
    """热门新闻响应"""
    items: list[NewsRecommendationItem]
    period_hours: int


class UserInterestResponse(BaseModel):
    """用户兴趣响应"""
    user_id: int
    interest_tags: dict[str, float]
    preferred_content_types: list[str]
    interaction_count: int
    recent_behaviors: list[dict]


class BehaviorTrackRequest(BaseModel):
    """行为追踪请求"""
    news_id: int
    behavior_type: str = "viewed"
    weight: float = 1.0


# ============ 公开接口（可选登录） ============

@router.get("", response_model=RecommendationResponse, summary="获取个性化新闻推荐")
async def get_recommendations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    exclude_viewed: bool = True,
):
    """获取个性化新闻推荐

    - 根据用户的浏览历史和兴趣标签进行个性化推荐
    - 未登录用户返回空列表
    """
    if not current_user:
        return RecommendationResponse(items=[], total=0)

    recommendations = await news_recommendation_service.get_recommendations(
        db=db,
        user_id=int(current_user.id),
        limit=limit,
        offset=offset,
        exclude_viewed=exclude_viewed,
    )

    return RecommendationResponse(
        items=[
            NewsRecommendationItem(
                news_id=r.news_id,
                title=r.title,
                category=r.category,
                score=r.score,
                reason=r.reason,
                is_new=r.is_new,
                is_high_quality=r.is_high_quality,
            )
            for r in recommendations
        ],
        total=len(recommendations),
    )


@router.get("/similar/{news_id}",
            response_model=RecommendationResponse, summary="获取相似新闻")
async def get_similar_news(
    news_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
):
    """获取与指定新闻相似的内容

    - 基于关键词和分类进行相似度匹配
    - 返回按相似度排序的新闻列表
    """
    # 检查新闻是否存在
    news = await news_service.get_by_id(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在",
        )

    similar = await news_recommendation_service.get_similar_news(
        db=db,
        news_id=news_id,
        limit=limit,
    )

    return RecommendationResponse(
        items=[
            NewsRecommendationItem(
                news_id=r.news_id,
                title=r.title,
                category=r.category,
                score=r.score,
                reason=r.reason,
                is_new=r.is_new,
                is_high_quality=r.is_high_quality,
            )
            for r in similar
        ],
        total=len(similar),
    )


@router.get("/trending", response_model=TrendingNewsResponse, summary="获取热门新闻")
async def get_trending_news(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    hours: Annotated[int, Query(ge=1, le=168)] = 24,  # 最多7天
):
    """获取热门新闻

    - 按浏览量和发布时间综合排序
    - 可指定时间范围（小时）
    """
    trending = await news_recommendation_service.get_trending_news(
        db=db,
        limit=limit,
        hours=hours,
    )

    return TrendingNewsResponse(
        items=[
            NewsRecommendationItem(
                news_id=r.news_id,
                title=r.title,
                category=r.category,
                score=r.score,
                reason=r.reason,
                is_new=r.is_new,
                is_high_quality=r.is_high_quality,
            )
            for r in trending
        ],
        period_hours=hours,
    )


@router.get("/quality/{news_id}",
            response_model=QualityAssessmentResponse, summary="获取新闻质量评估")
async def get_news_quality_assessment(
    news_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取新闻质量评估

    - 法律专业性分析
    - 内容质量评分
    - 综合摘要
    """
    news = await news_service.get_by_id(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在",
        )

    assessment = news_quality_service.get_quality_summary(news)

    return QualityAssessmentResponse(**assessment)


# ============ 需要登录的接口 ============

@router.get("/interests", response_model=UserInterestResponse,
            summary="获取用户兴趣画像")
async def get_user_interests(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取当前用户的兴趣画像

    - 返回用户的兴趣标签及权重
    - 返回最近的行为记录
    """
    profile = await news_recommendation_service.get_user_interest_profile(
        db=db,
        user_id=int(current_user.id),
    )

    return UserInterestResponse(
        user_id=profile.user_id,
        interest_tags=profile.interest_tags,
        preferred_content_types=profile.preferred_content_types,
        interaction_count=profile.interaction_count,
        recent_behaviors=profile.recent_behaviors,
    )


@router.post("/track", summary="追踪用户行为")
async def track_behavior(
    request: BehaviorTrackRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """手动追踪用户行为

    - 用于记录用户的特定交互行为
    - 配合个性化推荐系统使用
    """
    await news_recommendation_service.track_user_behavior(
        db=db,
        user_id=int(current_user.id),
        behavior_type=request.behavior_type,
        content_id=request.news_id,
        content_type="news",
        interaction_type=request.behavior_type,
        weight=request.weight,
    )

    return {"status": "ok", "message": "行为已记录"}


@router.post("/view/{news_id}", summary="记录新闻浏览")
async def record_news_view(
    news_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """记录用户浏览新闻

    - 自动追踪用户的新闻浏览行为
    - 用于更新兴趣画像和推荐
    """
    await news_recommendation_service.track_news_view(
        db=db,
        user_id=int(current_user.id),
        news_id=news_id,
    )

    return {"status": "ok", "message": "浏览记录已保存"}


@router.post("/favorite/{news_id}", summary="记录新闻收藏")
async def record_news_favorite(
    news_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    is_favorite: bool = True,
):
    """记录用户收藏/取消收藏新闻

    - 收藏行为会增加相关内容的推荐权重
    """
    await news_recommendation_service.track_news_favorite(
        db=db,
        user_id=int(current_user.id),
        news_id=news_id,
        is_favorite=is_favorite,
    )

    return {"status": "ok", "message": "收藏记录已更新"}
