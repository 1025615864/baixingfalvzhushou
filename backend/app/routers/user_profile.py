"""用户个人信息 API 路由"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field

from ..database import get_db, AsyncSessionLocal
from ..models.user import User
from ..config import get_settings
from ..utils.deps import get_current_user
from ..utils.security import hash_password, verify_password

router = APIRouter(prefix="/user", tags=["用户"])

settings = get_settings()

# CSRF Token 缓存（开发环境用，生产环境应使用 Redis）
_csrf_tokens: dict[str, dict] = {}


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    nickname: str | None
    avatar: str | None
    role: str
    is_active: bool
    created_at: datetime | None


class UserProfileUpdate(BaseModel):
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    avatar: str | None = None


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


class CsrfTokenResponse(BaseModel):
    csrf_token: str
    expires_in_hours: int


class SuccessResponse(BaseModel):
    message: str


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取当前登录用户的个人信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        nickname=current_user.nickname,
        avatar=current_user.avatar,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.patch("/me", response_model=UserResponse, summary="更新当前用户信息")
async def update_current_user(
    data: UserProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """更新当前登录用户的个人信息"""
    if data.nickname is not None:
        current_user.nickname = data.nickname
    if data.email is not None:
        current_user.email = data.email
    if data.avatar is not None:
        current_user.avatar = data.avatar

    async with AsyncSessionLocal() as session:
        try:
            session.add(current_user)
            await session.commit()
            await session.refresh(current_user)
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新用户信息失败: {str(e)}",
            )

    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        nickname=current_user.nickname,
        avatar=current_user.avatar,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.put("/me/password", response_model=SuccessResponse, summary="修改密码")
async def change_password(
    data: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """修改当前用户密码"""
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码不正确",
        )

    current_user.hashed_password = hash_password(data.new_password)

    async with AsyncSessionLocal() as session:
        try:
            session.add(current_user)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"密码修改失败: {str(e)}",
            )

    return SuccessResponse(message="密码修改成功")


@router.get("/me/csrf-token", response_model=CsrfTokenResponse, summary="获取 CSRF Token")
async def get_csrf_token(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取 CSRF Token（用于前端表单验证）"""
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(hours=1)

    _csrf_tokens[token] = {
        "user_id": current_user.id,
        "expires_at": expires,
    }

    # 清理过期 Token
    now = datetime.now()
    expired_keys = [k for k, v in _csrf_tokens.items() if v["expires_at"] < now]
    for k in expired_keys:
        del _csrf_tokens[k]

    return CsrfTokenResponse(
        csrf_token=token,
        expires_in_hours=1,
    )


@router.get("/me/settings", summary="获取用户设置")
async def get_user_settings(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取用户个性化设置（占位实现）"""
    return {
        "theme": "light",
        "language": "zh-CN",
        "notifications": {
            "email": True,
            "push": True,
            "sms": False,
        },
    }


@router.put("/me/settings", summary="更新用户设置")
async def update_user_settings(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """更新用户个性化设置（占位实现）"""
    return {"message": "设置已更新"}


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户信息（公开）")
async def get_user_public_info(
    user_id: int,
):
    """获取用户公开信息（无需认证）"""
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        nickname=user.nickname,
        avatar=user.avatar,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.get("/me/stats", summary="获取用户统计")
async def get_user_stats(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取用户统计数据（占位实现）"""
    return {
        "total_consultations": 0,
        "total_orders": 0,
        "total_points": 0,
        "total_knowledge_entries": 0,
        "member_since": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@router.get("/me/quotas", summary="获取用户配额")
async def get_user_quotas(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取用户配额信息（占位实现）"""
    return {
        "ai_queries_remaining": 100,
        "ai_queries_limit": 100,
        "ai_queries_reset_date": None,
        "storage_used_mb": 0,
        "storage_limit_mb": 500,
    }


@router.get("/me/usage", summary="获取用户使用记录")
async def get_user_usage(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取用户使用记录（占位实现）"""
    return {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 20,
    }


@router.get("/me/preferences", summary="获取用户偏好")
async def get_user_preferences(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取用户偏好设置（占位实现）"""
    return {
        "theme": "light",
        "language": "zh-CN",
        "auto_save_drafts": True,
        "notification_sound": True,
    }


@router.put("/me/preferences", summary="更新用户偏好")
async def update_user_preferences(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """更新用户偏好设置（占位实现）"""
    return {"message": "偏好设置已更新"}


@router.get("/me/2fa/status", summary="获取 2FA 状态")
async def get_2fa_status(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取两步验证状态（占位实现）"""
    return {
        "enabled": False,
        "method": None,
        "backup_codes_remaining": 0,
    }


@router.post("/me/2fa/setup", summary="设置 2FA")
async def setup_2fa(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """设置两步验证（占位实现）"""
    return {"message": "2FA 设置成功", "secret": "PLACEHOLDER", "backup_codes": []}


@router.post("/me/2fa/disable", summary="禁用 2FA")
async def disable_2fa(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """禁用两步验证（占位实现）"""
    return {"message": "2FA 已禁用"}


@router.get("/me/sessions", summary="获取会话列表")
async def get_user_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """获取用户活跃会话列表（占位实现）"""
    return {
        "sessions": [
            {
                "id": "current-session",
                "device": "Current Browser",
                "ip": "127.0.0.1",
                "location": "Unknown",
                "last_active": datetime.now().isoformat(),
                "is_current": True,
            }
        ],
        "total": 1,
    }


@router.delete("/me/sessions/{session_id}", summary="删除会话")
async def delete_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """删除指定会话（占位实现）"""
    return {"message": "会话已删除"}


@router.delete("/me", summary="删除账号")
async def delete_account(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """删除用户账号（占位实现，需要确认）"""
    return {"message": "账号删除请求已接收，将在 30 天后执行"}
