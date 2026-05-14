"""订阅路由"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import logging

from ..database import get_db
from ..models import NewsSubscription
from ..services.subscription_service import subscription_service
from ..events.kafka_producer import publish_subscription_created

logger = logging.getLogger(__name__)

router = APIRouter()


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    category_id: int
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    items: List[SubscriptionResponse]
    total: int


class SubscriptionCreateRequest(BaseModel):
    user_id: int
    category_id: int


@router.get("/", response_model=SubscriptionListResponse)
async def list_subscriptions(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取用户订阅列表"""
    subscriptions = await subscription_service.get_subscriptions(db, user_id, enabled_only=False)
    return SubscriptionListResponse(
        items=[SubscriptionResponse.model_validate(s) for s in subscriptions],
        total=len(subscriptions)
    )


@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    request: SubscriptionCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建订阅"""
    subscription = await subscription_service.subscribe(db, request.user_id, request.category_id)
    await db.commit()
    await db.refresh(subscription)
    try:
        await publish_subscription_created(
            subscription_id=str(subscription.id),
            user_id=str(request.user_id),
            category=str(request.category_id),
        )
    except Exception as e:
        logger.error(f"Failed to publish subscription event: {e}")
    return SubscriptionResponse.model_validate(subscription)


@router.patch("/{subscription_id}/toggle")
async def toggle_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db)
):
    """切换订阅状态"""
    result = await db.execute(
        select(NewsSubscription).where(NewsSubscription.id == subscription_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    new_enabled = not sub.enabled
    await subscription_service.update_subscription(db, sub.user_id, sub.category_id, new_enabled)
    await db.commit()
    return {"success": True, "enabled": new_enabled}


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除订阅"""
    result = await db.execute(
        select(NewsSubscription).where(NewsSubscription.id == subscription_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await subscription_service.unsubscribe(db, sub.user_id, sub.category_id)
    await db.commit()
    return {"success": True}
