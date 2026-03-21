"""通知路由"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ..database import get_db
from ..models import Notification, NotificationSettings

router = APIRouter()


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    content: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationCreateRequest(BaseModel):
    user_id: int
    type: str
    title: str
    content: Optional[str] = None


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取用户通知列表"""
    query = select(Notification).where(Notification.user_id == user_id)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    unread_query = select(func.count()).where(
        Notification.user_id == user_id,
        Notification.is_read == False
    )
    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar() or 0
    
    query = query.order_by(desc(Notification.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread_count
    )


@router.post("/", response_model=NotificationResponse)
async def create_notification(
    request: NotificationCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建通知（内部使用）"""
    notification = Notification(
        user_id=request.user_id,
        type=request.type,
        title=request.title,
        content=request.content,
        is_read=False,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    
    return NotificationResponse.model_validate(notification)


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db)
):
    """标记通知为已读"""
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    await db.commit()
    
    return {"success": True}


@router.patch("/read-all")
async def mark_all_as_read(user_id: int, db: AsyncSession = Depends(get_db)):
    """标记所有通知为已读"""
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
    )
    notifications = result.scalars().all()
    
    for n in notifications:
        n.is_read = True
    
    await db.commit()
    
    return {"success": True, "count": len(notifications)}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除通知"""
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    await db.delete(notification)
    await db.commit()
    
    return {"success": True}


class SettingsResponse(BaseModel):
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool


class SettingsUpdateRequest(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(user_id: int, db: AsyncSession = Depends(get_db)):
    """获取通知设置"""
    result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        return SettingsResponse(
            email_enabled=True,
            sms_enabled=True,
            push_enabled=True
        )
    
    return SettingsResponse(
        email_enabled=settings.email_enabled,
        sms_enabled=settings.sms_enabled,
        push_enabled=settings.push_enabled
    )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    user_id: int,
    request: SettingsUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新通知设置"""
    result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = NotificationSettings(user_id=user_id)
        db.add(settings)
    
    if request.email_enabled is not None:
        settings.email_enabled = request.email_enabled
    if request.sms_enabled is not None:
        settings.sms_enabled = request.sms_enabled
    if request.push_enabled is not None:
        settings.push_enabled = request.push_enabled
    
    await db.commit()
    
    return SettingsResponse(
        email_enabled=settings.email_enabled,
        sms_enabled=settings.sms_enabled,
        push_enabled=settings.push_enabled
    )
