"""帖子路由"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_posts(page: int = 1, page_size: int = 20):
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.post("/")
async def create_post(title: str, content: str, user_id: int, category: str = "general"):
    return {"id": 1, "title": title, "content": content, "user_id": user_id, "category": category}


@router.get("/{post_id}")
async def get_post(post_id: int):
    return {"id": post_id, "title": "Post", "content": "", "view_count": 0}
