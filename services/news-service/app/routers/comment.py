"""评论路由"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/{news_id}/comments")
async def list_comments(news_id: int):
    return {"items": []}


@router.post("/{news_id}/comments")
async def create_comment(news_id: int, content: str, user_id: int):
    return {"id": 1, "news_id": news_id, "content": content}
