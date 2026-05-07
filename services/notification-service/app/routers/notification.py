"""通知路由"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services import notification_service, template_service

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


class SettingsResponse(BaseModel):
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class SettingsUpdateRequest(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    user_id: int,
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取用户通知列表"""
    notifications, total, unread_count = await notification_service.list_notifications(
        db, user_id, page=page, page_size=page_size, unread_only=unread_only
    )

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread_count,
    )


@router.post("/", response_model=NotificationResponse)
async def create_notification(
    request: NotificationCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """创建通知（内部使用）"""
    notification = await notification_service.create_notification(
        db,
        user_id=request.user_id,
        type=request.type,
        title=request.title,
        content=request.content,
    )

    return NotificationResponse.model_validate(notification)


@router.post("/batch")
async def create_batch_notifications(
    user_ids: List[int],
    type: str,
    title: str,
    content: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """批量创建通知（系统通知）"""
    count = await notification_service.create_batch_notifications(
        db,
        user_ids=user_ids,
        type=type,
        title=title,
        content=content,
    )

    return {"success": True, "count": count}


@router.get("/unread-count")
async def get_unread_count(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取未读通知数量"""
    count = await notification_service.get_unread_count(db, user_id)
    return {"user_id": user_id, "unread_count": count}


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取通知详情"""
    notification = await notification_service.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return NotificationResponse.model_validate(notification)


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    """标记通知为已读"""
    success = await notification_service.mark_as_read(db, notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"success": True}


@router.patch("/read-all")
async def mark_all_as_read(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """标记所有通知为已读"""
    count = await notification_service.mark_all_as_read(db, user_id)
    return {"success": True, "count": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除通知"""
    success = await notification_service.delete_notification(db, notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"success": True}


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取通知设置"""
    settings = await notification_service.get_settings(db, user_id)

    return SettingsResponse(
        email_enabled=settings.email_enabled,
        sms_enabled=settings.sms_enabled,
        push_enabled=settings.push_enabled,
        quiet_hours_start=settings.quiet_hours_start,
        quiet_hours_end=settings.quiet_hours_end,
    )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    user_id: int,
    request: SettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """更新通知设置"""
    updates = request.model_dump(exclude_unset=True)
    settings = await notification_service.update_settings(db, user_id, updates)

    return SettingsResponse(
        email_enabled=settings.email_enabled,
        sms_enabled=settings.sms_enabled,
        push_enabled=settings.push_enabled,
        quiet_hours_start=settings.quiet_hours_start,
        quiet_hours_end=settings.quiet_hours_end,
    )


@router.post("/template/{template_name}/render")
async def render_template(
    template_name: str,
    variables: dict,
):
    """渲染通知模板"""
    result = template_service.render(template_name, variables)
    if not result:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")

    return result


@router.get("/templates")
async def list_templates():
    """列出所有通知模板"""
    return {"templates": template_service.list_templates()}
