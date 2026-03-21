"""推荐路由"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/lawyers")
async def recommend_lawyers(user_id: int, limit: int = 10):
    return {"items": []}


@router.get("/news")
async def recommend_news(user_id: int, limit: int = 10):
    return {"items": []}


@router.get("/posts")
async def recommend_posts(user_id: int, limit: int = 10):
    return {"items": []}
