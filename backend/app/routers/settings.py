"""个人设置 API 路由（Phase 1 Mock 实现）

用户级别的 Profile、通知、隐私、API Key 设置。
Phase 2 将接入数据库和认证中间件。
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter(prefix="/settings", tags=["Settings"])


# ==================== 请求模型 ====================

class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=50, description="显示名称")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    email_visible: Optional[bool] = Field(None, description="邮箱是否公开")


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
    name: str = Field(..., min_length=1, max_length=50, description="密钥名称")


# ==================== Mock 数据存储 ====================

_mock_profile = {
    "display_name": "张律师",
    "bio": "执业十年，专注民商事诉讼与企业法律顾问服务。",
    "phone": "138****5678",
    "email": "zhanglawyer@example.com",
    "email_visible": False,
    "username": "zhang_lawyer",
    "avatar_url": "https://cdn.baixingfalv.com/avatars/default-lawyer.png",
    "member_since": "2023-06-15T09:00:00",
    "verified": True,
    "verification_type": "lawyer_cert",
}

_mock_notification = {
    "email": True,
    "sms": False,
    "push": True,
    "consultation_reminder": True,
    "payment_notice": True,
    "promotion": False,
    "system_notice": True,
}

_mock_privacy = {
    "profile_visible": True,
    "search_visible": True,
    "show_online_status": False,
    "allow_messages_from_strangers": True,
}

_mock_api_keys: List[dict] = [
    {
        "id": "key_a1b2c3d4",
        "name": "WebHook 集成",
        "prefix": "bxfv_live_",
        "masked_key": "bxfv_live_****a1b2",
        "scopes": ["consultation:read", "document:read"],
        "created_at": "2025-03-10T14:30:00",
        "last_used_at": "2025-05-12T08:22:00",
        "expires_at": None,
    },
    {
        "id": "key_e5f6g7h8",
        "name": "内部管理系统",
        "prefix": "bxfv_live_",
        "masked_key": "bxfv_live_****c3d4",
        "scopes": ["consultation:read", "document:read", "user:read"],
        "created_at": "2025-01-20T10:00:00",
        "last_used_at": "2025-05-08T16:45:00",
        "expires_at": "2026-01-20T10:00:00",
    },
]


# ==================== Profile ====================

@router.get("/profile", summary="获取个人资料设置")
async def get_profile():
    """获取当前用户的个人资料设置（显示名称、简介、手机号等）。"""
    return {
        "data": _mock_profile,
        "updated_at": "2025-05-10T15:00:00",
    }


@router.put("/profile", summary="更新个人资料设置")
async def update_profile(data: ProfileUpdateRequest):
    """更新当前用户的个人资料设置。"""
    updated_fields = data.model_dump(exclude_none=True)
    if not updated_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要提供一个待更新字段",
        )
    _mock_profile.update(updated_fields)
    return {
        "message": "个人资料更新成功",
        "data": _mock_profile,
        "updated_at": datetime.now().isoformat(),
    }


# ==================== Notification ====================

@router.get("/notification", summary="获取通知偏好设置")
async def get_notification():
    """获取当前用户的通知偏好设置（邮件、短信、推送、各分类开关）。"""
    return {
        "data": _mock_notification,
        "updated_at": "2025-05-08T09:00:00",
    }


@router.put("/notification", summary="更新通知偏好设置")
async def update_notification(data: NotificationUpdateRequest):
    """更新当前用户的通知偏好设置。"""
    updated_fields = data.model_dump(exclude_none=True)
    if not updated_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要提供一个待更新字段",
        )
    _mock_notification.update(updated_fields)
    return {
        "message": "通知偏好更新成功",
        "data": _mock_notification,
        "updated_at": datetime.now().isoformat(),
    }


# ==================== Privacy ====================

@router.get("/privacy", summary="获取隐私设置")
async def get_privacy():
    """获取当前用户的隐私设置（资料可见性、在线状态等）。"""
    return {
        "data": _mock_privacy,
        "updated_at": "2025-04-22T11:00:00",
    }


@router.put("/privacy", summary="更新隐私设置")
async def update_privacy(data: PrivacyUpdateRequest):
    """更新当前用户的隐私设置。"""
    updated_fields = data.model_dump(exclude_none=True)
    if not updated_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要提供一个待更新字段",
        )
    _mock_privacy.update(updated_fields)
    return {
        "message": "隐私设置更新成功",
        "data": _mock_privacy,
        "updated_at": datetime.now().isoformat(),
    }


# ==================== API Keys ====================

@router.get("/api-keys", summary="获取 API 密钥列表")
async def list_api_keys():
    """获取当前用户的所有 API 密钥（密钥值已脱敏）。"""
    return {
        "data": _mock_api_keys,
        "total": len(_mock_api_keys),
    }


@router.post("/api-keys", status_code=status.HTTP_201_CREATED, summary="创建 API 密钥")
async def create_api_key(data: ApiKeyCreateRequest):
    """为当前用户创建一个新的 API 密钥，返回完整密钥值（仅此一次可见）。"""
    import secrets
    key_suffix = secrets.token_hex(8)
    full_key = f"bxfv_live_{key_suffix}"
    masked = f"bxfv_live_****{key_suffix[:4]}"

    new_key = {
        "id": f"key_{secrets.token_hex(4)}",
        "name": data.name,
        "prefix": "bxfv_live_",
        "masked_key": masked,
        "full_key": full_key,
        "scopes": ["consultation:read"],
        "created_at": datetime.now().isoformat(),
        "last_used_at": None,
        "expires_at": None,
    }
    _mock_api_keys.append(new_key)

    return {
        "message": "API 密钥创建成功，请妥善保存密钥值，此值仅显示一次。",
        "data": new_key,
    }


@router.delete("/api-keys/{key_id}", summary="删除（吊销）API 密钥")
async def delete_api_key(key_id: str):
    """吊销指定 API 密钥，吊销后该密钥将立即失效。"""
    for i, key in enumerate(_mock_api_keys):
        if key["id"] == key_id:
            removed = _mock_api_keys.pop(i)
            return {
                "message": f"API 密钥「{removed['name']}」已吊销",
                "revoked_key_id": key_id,
                "revoked_at": datetime.now().isoformat(),
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"API 密钥 {key_id} 不存在",
    )