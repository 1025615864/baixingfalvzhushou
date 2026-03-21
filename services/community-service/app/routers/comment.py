"""评论路由"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/{post_id}/comments")
async def list_comments(post_id: int):
    return {"items": []}


@router.post("/{post_id}/comments")
async def create_comment(post_id: int, content: str, user_id: int):
    return {"id": 1, "post_id": post_id, "content": content, "user_id": user_id}
