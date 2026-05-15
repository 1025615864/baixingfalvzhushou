from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.settings import UserSettings, UserApiKey


_DEFAULT_PROFILE = {
    "display_name": "",
    "bio": "",
    "phone": "",
    "email_visible": False,
}

_DEFAULT_NOTIFICATION = {
    "email": True,
    "sms": False,
    "push": True,
    "consultation_reminder": True,
    "payment_notice": True,
    "promotion": False,
    "system_notice": True,
}

_DEFAULT_PRIVACY = {
    "profile_visible": True,
    "search_visible": True,
    "show_online_status": False,
    "allow_messages_from_strangers": True,
}


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create_settings(self, user_id: int) -> UserSettings:
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.db.execute(stmt)
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = UserSettings(
                user_id=user_id,
                profile_data=dict(_DEFAULT_PROFILE),
                notification_settings=dict(_DEFAULT_NOTIFICATION),
                privacy_settings=dict(_DEFAULT_PRIVACY),
            )
            self.db.add(settings)
            await self.db.flush()
        return settings

    async def get_profile(self, user_id: int) -> dict:
        settings = await self._get_or_create_settings(user_id)
        return {
            "data": settings.profile_data or dict(_DEFAULT_PROFILE),
            "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
        }

    async def update_profile(self, user_id: int, data: dict) -> dict:
        try:
            settings = await self._get_or_create_settings(user_id)
            current = settings.profile_data or {}
            current.update(data)
            settings.profile_data = current
            await self.db.commit()
            await self.db.refresh(settings)
            return {
                "message": "个人资料更新成功",
                "data": settings.profile_data,
                "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
            }
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def get_notification_settings(self, user_id: int) -> dict:
        settings = await self._get_or_create_settings(user_id)
        return {
            "data": settings.notification_settings or dict(_DEFAULT_NOTIFICATION),
            "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
        }

    async def update_notification_settings(self, user_id: int, data: dict) -> dict:
        try:
            settings = await self._get_or_create_settings(user_id)
            current = settings.notification_settings or {}
            current.update(data)
            settings.notification_settings = current
            await self.db.commit()
            await self.db.refresh(settings)
            return {
                "message": "通知偏好更新成功",
                "data": settings.notification_settings,
                "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
            }
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def get_privacy_settings(self, user_id: int) -> dict:
        settings = await self._get_or_create_settings(user_id)
        return {
            "data": settings.privacy_settings or dict(_DEFAULT_PRIVACY),
            "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
        }

    async def update_privacy_settings(self, user_id: int, data: dict) -> dict:
        try:
            settings = await self._get_or_create_settings(user_id)
            current = settings.privacy_settings or {}
            current.update(data)
            settings.privacy_settings = current
            await self.db.commit()
            await self.db.refresh(settings)
            return {
                "message": "隐私设置更新成功",
                "data": settings.privacy_settings,
                "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
            }
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def list_api_keys(self, user_id: int) -> dict:
        stmt = (
            select(UserApiKey)
            .where(UserApiKey.user_id == user_id, UserApiKey.is_active == True)
            .order_by(UserApiKey.created_at.desc())
        )
        result = await self.db.execute(stmt)
        keys = result.scalars().all()
        data = []
        for k in keys:
            data.append({
                "id": str(k.id),
                "name": k.name,
                "prefix": k.key_prefix,
                "masked_key": f"{k.key_prefix}****{k.key_hash[-4:]}",
                "scopes": k.permissions or [],
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "expires_at": None,
            })
        return {
            "data": data,
            "total": len(data),
        }

    async def create_api_key(self, user_id: int, name: str, permissions: dict | None = None) -> dict:
        try:
            raw_key = f"bxl_{secrets.token_hex(24)}"
            key_prefix = raw_key[:8]
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

            api_key = UserApiKey(
                user_id=user_id,
                name=name,
                key_hash=key_hash,
                key_prefix=key_prefix,
                permissions=permissions or {"scopes": ["consultation:read"]},
            )
            self.db.add(api_key)
            await self.db.commit()
            await self.db.refresh(api_key)

            return {
                "message": "API 密钥创建成功，请妥善保存密钥值，此值仅显示一次。",
                "data": {
                    "id": str(api_key.id),
                    "name": api_key.name,
                    "prefix": api_key.key_prefix,
                    "masked_key": f"{api_key.key_prefix}****{api_key.key_hash[-4:]}",
                    "full_key": raw_key,
                    "scopes": api_key.permissions.get("scopes", []) if api_key.permissions else [],
                    "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
                    "last_used_at": None,
                    "expires_at": None,
                },
            }
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")

    async def delete_api_key(self, user_id: int, key_id: int) -> dict:
        try:
            api_key = await self.db.get(UserApiKey, key_id)
            if api_key is None or api_key.user_id != user_id:
                raise HTTPException(status_code=404, detail=f"API 密钥 {key_id} 不存在")
            if not api_key.is_active:
                raise HTTPException(status_code=404, detail=f"API 密钥 {key_id} 不存在")

            api_key.is_active = False
            await self.db.commit()

            return {
                "message": f"API 密钥「{api_key.name}」已吊销",
                "revoked_key_id": str(key_id),
                "revoked_at": datetime.now(timezone.utc).isoformat(),
            }
        except HTTPException:
            raise
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="操作失败，请稍后重试")
