from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.forum import NewsToForumPostRequest, NewsToForumPostResponse

router = APIRouter(tags=["News Core"], prefix="")


class _NewsService:
    async def get_published(self, db, news_id):
        raise NotImplementedError

news_service = _NewsService()


class _ForumService:
    async def create_post(self, db, user_id, post_data):
        raise NotImplementedError

forum_service = _ForumService()


async def news_to_forum_post(
    data: NewsToForumPostRequest,
    current_user=Depends(lambda: None),
    db: AsyncSession = Depends(lambda: None),
) -> NewsToForumPostResponse:
    raise NotImplementedError


@router.get("/")
async def list_news():
    raise NotImplementedError


@router.get("/{news_id}")
async def get_news(news_id: int):
    raise NotImplementedError


@router.get("/{news_id}/comments")
async def get_news_comments(news_id: int):
    raise NotImplementedError


@router.post("/{news_id}/comments")
async def create_news_comment(news_id: int):
    raise NotImplementedError


@router.delete("/{news_id}/comments/{comment_id}")
async def delete_news_comment(news_id: int, comment_id: int):
    raise NotImplementedError


@router.post("/{news_id}/favorite")
async def toggle_news_favorite(news_id: int):
    raise NotImplementedError


@router.get("/subscriptions")
async def get_subscriptions():
    raise NotImplementedError


@router.post("/subscriptions")
async def create_subscription():
    raise NotImplementedError


@router.delete("/subscriptions/{category}")
async def delete_subscription(category: str):
    raise NotImplementedError


@router.get("/subscriptions/feed")
async def get_subscription_feed():
    raise NotImplementedError


@router.post("/to-forum")
async def news_to_forum(data: NewsToForumPostRequest):
    raise NotImplementedError
