from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..services.notification_service import NotificationService
from ..services.cache_service import cache_service
from ..utils.deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notification"])


class BatchIdsBody(BaseModel):
    ids: list[int]


class CreateSystemNotificationBody(BaseModel):
    title: str
    content: str
    target_type: str = "all"
    target_ids: Optional[list[str]] = None
    expires_at: Optional[str] = None


class UpdateSystemNotificationBody(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_type: Optional[str] = None
    target_ids: Optional[list[str]] = None
    is_published: Optional[bool] = None
    expires_at: Optional[str] = None


def get_notification_service(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationService:
    return NotificationService(db, user)


@router.get("")
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    notification_type: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db, user)
    return await svc.get_notifications(
        user_id=user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
        notification_type=notification_type,
    )


@router.get("/unread-count")
async def get_unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"notification:unread_count:{user.id}"
    cached = await cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    svc = NotificationService(db, user)
    count = await svc.get_unread_count(user_id=user.id)
    result = {"count": count}
    await cache_service.set_json(cache_key, result, expire=60)
    return result


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db, user)
    result = await svc.mark_as_read(user_id=user.id, notification_id=notification_id)
    await cache_service.delete(f"notification:unread_count:{user.id}")
    return result


@router.patch("/read-all")
async def mark_all_as_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db, user)
    result = await svc.mark_all_as_read(user_id=user.id)
    await cache_service.delete(f"notification:unread_count:{user.id}")
    return result


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db, user)
    result = await svc.delete_notification(user_id=user.id, notification_id=notification_id)
    await cache_service.delete(f"notification:unread_count:{user.id}")
    return result


@router.post("/batch-read")
async def batch_mark_read(
    body: BatchIdsBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db, user)
    result = await svc.batch_mark_read(user_id=user.id, ids=body.ids)
    await cache_service.delete(f"notification:unread_count:{user.id}")
    return result


@router.post("/batch-delete")
async def batch_delete(
    body: BatchIdsBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db, user)
    result = await svc.batch_delete(user_id=user.id, ids=body.ids)
    await cache_service.delete(f"notification:unread_count:{user.id}")
    return result


@router.get("/types")
async def get_notification_types(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db, user)
    return await svc.get_notification_types(user_id=user.id)


admin_router = APIRouter(prefix="/v1/admin/notifications", tags=["System-Notifications"])


@admin_router.get("")
async def get_system_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_published: Optional[bool] = Query(None),
    keyword: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db, user)
    return await svc.get_system_notifications(
        page=page,
        page_size=page_size,
        is_published=is_published,
        keyword=keyword,
    )


@admin_router.post("")
async def create_system_notification(
    body: CreateSystemNotificationBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db, user)
    data = {
        "title": body.title,
        "content": body.content,
        "link": None,
    }
    return await svc.create_system_notification(data)


@admin_router.put("/{notification_id}")
async def update_system_notification(
    notification_id: int,
    body: UpdateSystemNotificationBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db, user)
    data = body.model_dump(exclude_none=True)
    return await svc.update_system_notification(notification_id, data)


@admin_router.delete("/{notification_id}")
async def delete_system_notification(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db, user)
    return await svc.delete_system_notification(notification_id)
