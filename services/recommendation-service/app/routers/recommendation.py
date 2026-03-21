"""推荐路由"""
from typing import List, Optional
import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..config.settings import get_settings

settings = get_settings()
router = APIRouter()


class RecommendationItem(BaseModel):
    id: int
    type: str
    title: str
    description: str
    url: str


class RecommendationResponse(BaseModel):
    items: List[RecommendationItem]


async def _fetch_from_service(url: str, params: dict = None) -> dict:
    """从其他服务获取数据"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    return {}


@router.get("/lawyers", response_model=RecommendationResponse)
async def recommend_lawyers(
    user_id: int = Query(..., description="用户ID"),
    limit: int = Query(10, ge=1, le=50)
):
    """推荐律师"""
    return RecommendationResponse(items=[
        RecommendationItem(
            id=i,
            type="lawyer",
            title=f"推荐律师 {i}",
            description="资深律师，专业可靠",
            url=f"/lawyer/{i}"
        )
        for i in range(1, min(limit + 1, 4))
    ])


@router.get("/news", response_model=RecommendationResponse)
async def recommend_news(
    user_id: int = Query(..., description="用户ID"),
    limit: int = Query(10, ge=1, le=50)
):
    """推荐新闻"""
    url = f"{settings.news_service_url}/api/v1/news"
    data = await _fetch_from_service(url, {"page_size": limit})
    
    items = []
    if "items" in data:
        for news in data["items"][:limit]:
            items.append(RecommendationItem(
                id=news.get("id", 0),
                type="news",
                title=news.get("title", ""),
                description=news.get("summary", ""),
                url=f"/news/{news.get('id')}"
            ))
    
    return RecommendationResponse(items=items)


@router.get("/posts", response_model=RecommendationResponse)
async def recommend_posts(
    user_id: int = Query(..., description="用户ID"),
    limit: int = Query(10, ge=1, le=50)
):
    """推荐帖子"""
    url = f"{settings.community_service_url}/api/v1/community/posts"
    data = await _fetch_from_service(url, {"page_size": limit})
    
    items = []
    if "items" in data:
        for post in data["items"][:limit]:
            items.append(RecommendationItem(
                id=post.get("id", 0),
                type="post",
                title=post.get("title", ""),
                description=post.get("content", "")[:100],
                url=f"/forum/post/{post.get('id')}"
            ))
    
    return RecommendationResponse(items=items)


@router.get("/feed", response_model=RecommendationResponse)
async def get_personalized_feed(
    user_id: int = Query(..., description="用户ID"),
    limit: int = Query(20, ge=1, le=50)
):
    """个性化推荐信息流（混合推荐）"""
    news = await recommend_news(user_id=user_id, limit=limit // 2)
    posts = await recommend_posts(user_id=user_id, limit=limit // 2)
    
    items = (news.items + posts.items)[:limit]
    return RecommendationResponse(items=items)
