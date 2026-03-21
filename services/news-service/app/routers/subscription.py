"""订阅路由"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from ..models import NewsSubscription

router = APIRouter()


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    category: str
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    items: List[SubscriptionResponse]
    total: int


class SubscriptionCreateRequest(BaseModel):
    user_id: int
    category: str


@router.get("/", response_model=SubscriptionListResponse)
async def list_subscriptions(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取用户订阅列表"""
    query = select(NewsSubscription).where(NewsSubscription.user_id == user_id)
    
    result = await db.execute(query)
    subscriptions = result.scalars().all()
    
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
    existing = await db.execute(
        select(NewsSubscription).where(
            NewsSubscription.user_id == request.user_id,
            NewsSubscription.category == request.category
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Subscription already exists")
    
    subscription = NewsSubscription(
        user_id=request.user_id,
        category=request.category,
        enabled=True,
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    
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
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    subscription.enabled = not subscription.enabled
    await db.commit()
    
    return {"success": True, "enabled": subscription.enabled}


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除订阅"""
    result = await db.execute(
        select(NewsSubscription).where(NewsSubscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    await db.delete(subscription)
    await db.commit()
    
    return {"success": True}
