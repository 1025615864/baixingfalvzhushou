"""News topics routes

Provides news topic list and detail endpoints
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...schemas.news import (
    NewsTopicListResponse, NewsTopicResponse,
    NewsTopicDetailResponse, NewsListItem,
)
from ...services.news_service import news_service
from ...utils.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/topics", tags=["News Topics"])


@router.get("", response_model=NewsTopicListResponse,
            summary="Get news topic list")
async def list_news_topics(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get list of active news topics"""
    topics = await news_service.list_topics(db, active_only=True)
    items = [NewsTopicResponse.model_validate(t) for t in topics]
    return NewsTopicListResponse(items=items)


@router.get("/{topic_id}", response_model=NewsTopicDetailResponse,
            summary="Get topic detail")
async def get_news_topic_detail(
    topic_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Get topic detail with news list"""
    topic = await news_service.get_topic(db, topic_id)
    if not topic or not bool(getattr(topic, "is_active", True)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found")

    news_list, total = await news_service.get_topic_news(
        db, topic_id, page=page, page_size=page_size, published_only=True
    )

    ids = [int(n.id) for n in news_list]
    user_id = current_user.id if current_user else None
    fav_stats = await news_service.get_favorite_stats(db, ids, int(user_id) if user_id is not None else None)

    items: list[NewsListItem] = []
    for news in news_list:
        item = NewsListItem.model_validate(news)
        fav_count, is_fav = fav_stats.get(int(news.id), (0, False))
        item.favorite_count = int(fav_count)
        item.is_favorited = bool(is_fav)
        items.append(item)

    return NewsTopicDetailResponse(
        topic=NewsTopicResponse.model_validate(topic),
        items=items,
        total=int(total),
        page=int(page),
        page_size=int(page_size),
    )


@router.post("/{topic_id}/subscribe", summary="Subscribe to a news topic")
async def subscribe_news_topic(
    topic_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Subscribe to a news topic"""
    topic = await news_service.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found")

    from ...schemas.news import NewsSubscriptionCreate, NewsSubscriptionResponse
    from ...services.news_service import news_subscription_service

    # Subscribe using topic name as category
    sub = await news_subscription_service.subscribe(
        db, int(current_user.id), f"topic:{topic.name}"
    )
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription failed")
    return NewsSubscriptionResponse.model_validate(sub)


@router.delete("/{topic_id}/subscribe", summary="Unsubscribe from a news topic")
async def unsubscribe_news_topic(
    topic_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Unsubscribe from a news topic"""
    topic = await news_service.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found")

    from ...services.news_service import news_subscription_service

    success = await news_subscription_service.unsubscribe_by_category(
        db, int(current_user.id), f"topic:{topic.name}"
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found")
    return {"message": "Unsubscribed successfully"}
