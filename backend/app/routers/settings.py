from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..services.settings_service import SettingsService
from ..utils.deps import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    email_visible: Optional[bool] = None


class NotificationUpdateRequest(BaseModel):
    email: Optional[bool] = None
    sms: Optional[bool] = None
    push: Optional[bool] = None
    consultation_reminder: Optional[bool] = None
    payment_notice: Optional[bool] = None
    promotion: Optional[bool] = None
    system_notice: Optional[bool] = None


class PrivacyUpdateRequest(BaseModel):
    profile_visible: Optional[bool] = None
    search_visible: Optional[bool] = None
    show_online_status: Optional[bool] = None
    allow_messages_from_strangers: Optional[bool] = None


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


@router.get("/profile", summary="获取个人资料设置")
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    service = SettingsService(db)
    return await service.get_profile(current_user.id)


@router.put("/profile", summary="更新个人资料设置")
async def update_profile(
    data: ProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    updated_fields = data.model_dump(exclude_none=True)
    if not updated_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要提供一个待更新字段",
        )
    service = SettingsService(db)
    return await service.update_profile(current_user.id, updated_fields)


@router.get("/notification", summary="获取通知偏好设置")
async def get_notification(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    service = SettingsService(db)
    return await service.get_notification_settings(current_user.id)


@router.put("/notification", summary="更新通知偏好设置")
async def update_notification(
    data: NotificationUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    updated_fields = data.model_dump(exclude_none=True)
    if not updated_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要提供一个待更新字段",
        )
    service = SettingsService(db)
    return await service.update_notification_settings(current_user.id, updated_fields)


@router.get("/privacy", summary="获取隐私设置")
async def get_privacy(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    service = SettingsService(db)
    return await service.get_privacy_settings(current_user.id)


@router.put("/privacy", summary="更新隐私设置")
async def update_privacy(
    data: PrivacyUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    updated_fields = data.model_dump(exclude_none=True)
    if not updated_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要提供一个待更新字段",
        )
    service = SettingsService(db)
    return await service.update_privacy_settings(current_user.id, updated_fields)


@router.get("/api-keys", summary="获取 API 密钥列表")
async def list_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    service = SettingsService(db)
    return await service.list_api_keys(current_user.id)


@router.post("/api-keys", status_code=status.HTTP_201_CREATED, summary="创建 API 密钥")
async def create_api_key(
    data: ApiKeyCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    service = SettingsService(db)
    return await service.create_api_key(current_user.id, data.name)


@router.delete("/api-keys/{key_id}", summary="删除（吊销）API 密钥")
async def delete_api_key(
    key_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    service = SettingsService(db)
    return await service.delete_api_key(current_user.id, key_id)
