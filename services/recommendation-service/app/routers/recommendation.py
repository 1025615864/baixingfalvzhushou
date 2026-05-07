"""推荐路由"""
from typing import List, Optional

from fastapi import APIRouter, Query, Depends

from app.services.recommendation_service import recommendation_service
from app.database import get_db, AsyncSession

router = APIRouter()


@router.get("/lawyers")
async def recommend_lawyers(
    user_id: int = Query(..., description="用户ID"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """推荐律师"""
    items = await recommendation_service.recommend_lawyers(db, user_id, limit)
    return {"items": items}


@router.get("/news")
async def recommend_news(
    user_id: int = Query(..., description="用户ID"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """推荐新闻"""
    items = await recommendation_service.recommend_news(db, user_id, limit)
    return {"items": items}


@router.get("/posts")
async def recommend_posts(
    user_id: int = Query(..., description="用户ID"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """推荐帖子"""
    items = await recommendation_service.recommend_posts(db, user_id, limit)
    return {"items": items}


@router.get("/feed")
async def get_personalized_feed(
    user_id: int = Query(..., description="用户ID"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """个性化推荐信息流（混合推荐）"""
    items = await recommendation_service.get_personalized_feed(db, user_id, limit)
    return {"items": items}


@router.post("/user/{user_id}/features")
async def update_user_features(
    user_id: int,
    features: dict,
    db: AsyncSession = Depends(get_db),
):
    """更新用户特征"""
    user_feature = await recommendation_service.update_user_features(
        db, user_id, features
    )
    return {
        "user_id": user_feature.user_id,
        "features": user_feature.features,
        "updated_at": user_feature.updated_at.isoformat(),
    }


@router.post("/items/{item_type}/{item_id}/features")
async def update_item_features(
    item_type: str,
    item_id: int,
    features: dict,
    score: float = 0.0,
    db: AsyncSession = Depends(get_db),
):
    """更新物品特征"""
    item_feature = await recommendation_service.update_item_features(
        db, item_type, item_id, features, score
    )
    return {
        "item_type": item_feature.item_type,
        "item_id": item_feature.item_id,
        "features": item_feature.features,
        "score": item_feature.score,
        "updated_at": item_feature.updated_at.isoformat(),
    }
