"""News subscriptions routes

Provides news subscription management endpoints
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...schemas.news import NewsSubscriptionCreate, NewsSubscriptionResponse
from ...services.news_service import news_subscription_service
from ...utils.deps import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["News Subscriptions"])


@router.get("", response_model=list[NewsSubscriptionResponse],
            summary="Get my news subscriptions")
async def get_my_news_subscriptions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get user's news subscriptions"""
    subs = await news_subscription_service.get_subscriptions(db, int(current_user.id))
    return [NewsSubscriptionResponse.model_validate(s) for s in subs]


@router.post("", response_model=NewsSubscriptionResponse,
             summary="Subscribe to news category")
async def create_news_subscription(
    data: NewsSubscriptionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Subscribe to a news category"""
    sub = await news_subscription_service.subscribe(db, int(current_user.id), data.value)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription failed")
    return NewsSubscriptionResponse.model_validate(sub)


@router.delete("/{category}", summary="Unsubscribe from news category")
async def delete_news_subscription(
    category: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Unsubscribe from a news category"""
    success = await news_subscription_service.unsubscribe_by_category(db, int(current_user.id), category)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found")
    return {"message": "Unsubscribed successfully"}


@router.get("/feed", response_model=dict, summary="Get subscribed news feed")
async def get_my_subscribed_news(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
):
    """Get news feed from subscribed categories"""
    news_list, total = await news_subscription_service.get_subscribed_news(
        db, int(current_user.id), page=page, page_size=page_size
    )
    return {
        "items": [
            dict(
                id=n.id,
                title=n.title,
                category=n.category) for n in news_list],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
