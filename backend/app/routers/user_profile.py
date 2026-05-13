"""用户个人信息 API 路由"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..config import get_settings
from ..utils.deps import get_current_user
from ..utils.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/user", tags=["用户"])

settings = get_settings()


class _TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class _AuthResponse(BaseModel):
    message: str
    user: dict[str, object]
    token: _TokenResponse | None = None


class _LoginRequest(BaseModel):
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class _RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    nickname: str | None = Field(default=None, max_length=50, description="昵称")
    agree_terms: bool = Field(default=False, description="同意用户协议")
    agree_privacy: bool = Field(default=False, description="同意隐私政策")
    agree_ai_disclaimer: bool = Field(default=False, description="同意AI咨询免责声明")


@router.post("/register", response_model=_AuthResponse, summary="用户注册")
async def register(
    data: _RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    if not data.agree_terms or not data.agree_privacy or not data.agree_ai_disclaimer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请阅读并同意用户协议、隐私政策和AI咨询免责声明",
        )

    existing_username = await db.execute(
        select(User).where(User.username == data.username)
    )
    if existing_username.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用",
        )

    existing_email = await db.execute(
        select(User).where(User.email == data.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册",
        )

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        nickname=data.nickname or data.username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )

    return _AuthResponse(
        message="注册成功",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "avatar_url": user.avatar,
            "role": user.role,
        },
        token=_TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
        ),
    )


@router.post("/login", response_model=_AuthResponse, summary="用户登录")
async def login(
    data: _LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            (User.username == data.username) | (User.email == data.username)
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系客服",
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )

    return _AuthResponse(
        message="登录成功",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "avatar_url": user.avatar,
            "role": user.role,
        },
        token=_TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
        ),
    )

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
    phone: str | None = None


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


class _PasswordResetRequestModel(BaseModel):
    email: EmailStr


class _PasswordResetConfirmModel(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=128)


class _SmsSendModel(BaseModel):
    phone: str = Field(..., min_length=5, max_length=20)
    scene: str = Field(default="bind_phone")


class _SmsVerifyModel(BaseModel):
    phone: str = Field(..., min_length=5, max_length=20)
    code: str = Field(..., min_length=4, max_length=10)
    scene: str = Field(default="bind_phone")


class _AdminRoleUpdate(BaseModel):
    role: str


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
    db=Depends(get_db),
):
    """更新当前登录用户的个人信息"""
    if data.nickname is not None:
        current_user.nickname = data.nickname
    if data.email is not None:
        current_user.email = data.email
    if data.avatar is not None:
        current_user.avatar = data.avatar

    try:
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
    except Exception as e:
        await db.rollback()
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


@router.put("/me", response_model=UserResponse, summary="更新当前用户信息(PUT)")
async def update_current_user_put(
    data: UserProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    if data.phone is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号请通过短信验证码完成绑定",
        )
    if data.nickname is not None:
        current_user.nickname = data.nickname
    if data.email is not None:
        current_user.email = data.email
    if data.avatar is not None:
        current_user.avatar = data.avatar
    try:
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
    except Exception as e:
        await db.rollback()
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


@router.put("/me/password", summary="修改密码")
async def change_password(
    data: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误",
        )

    if data.old_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与当前密码相同",
        )

    current_user.hashed_password = hash_password(data.new_password)

    try:
        db.add(current_user)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败: {str(e)}",
        )

    return {"message": "密码修改成功", "success": True}


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
    db=Depends(get_db),
):
    """获取用户公开信息（无需认证）"""
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
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
    return {"message": "账号删除请求已接收，将在 30 天后执行"}


@router.post("/password-reset/request", summary="请求密码重置")
async def request_password_reset(
    data: _PasswordResetRequestModel,
    db=Depends(get_db),
):
    from sqlalchemy import select as sa_select
    result = await db.execute(sa_select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if user:
        try:
            from app.services.email_service import email_service
            await email_service.generate_reset_token(user.id, user.email)
        except Exception:
            pass
    return {"message": "如果邮箱存在，重置邮件已发送", "success": True}


@router.post("/password-reset/confirm", summary="确认密码重置")
async def confirm_password_reset(
    data: _PasswordResetConfirmModel,
    db=Depends(get_db),
):
    try:
        from app.services.email_service import email_service
        result = await email_service.verify_reset_token(data.token)
        if result is None:
            raise HTTPException(status_code=400, detail="无效或已过期的重置令牌")
        user_id = result["user_id"]
        from sqlalchemy import select as sa_select
        result_q = await db.execute(sa_select(User).where(User.id == user_id))
        user = result_q.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=400, detail="用户不存在")
        user.hashed_password = hash_password(data.new_password)
        db.add(user)
        await db.commit()
        return {"message": "密码重置成功", "success": True}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="无效或已过期的重置令牌")


@router.post("/email-verification/request", summary="请求邮箱验证")
async def request_email_verification(
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    try:
        from app.services.email_service import email_service
        await email_service.configure_from_db(db)
        token = await email_service.generate_email_verification_token(current_user.id, current_user.email)
        verify_url = f"{settings.site_url}/verify-email?token={token}" if hasattr(settings, 'site_url') else f"http://localhost:3000/verify-email?token={token}"
        await email_service.send_email_verification_email(current_user.email, verify_url, user_id=current_user.id)
    except Exception:
        pass
    return {"success": True, "message": "验证邮件已发送"}


@router.get("/email-verification/verify", summary="验证邮箱")
async def verify_email(
    token: str,
    db=Depends(get_db),
):
    try:
        from app.services.email_service import email_service
        result = await email_service.verify_email_verification_token(token)
        if result is None:
            raise HTTPException(status_code=400, detail="无效或已过期的验证令牌")
        user_id = result["user_id"]
        from sqlalchemy import select as sa_select
        result_q = await db.execute(sa_select(User).where(User.id == user_id))
        user = result_q.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=400, detail="用户不存在")
        user.email_verified = True
        user.email_verified_at = datetime.now()
        db.add(user)
        await db.commit()
        return {"success": True, "message": "邮箱验证成功"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="无效或已过期的验证令牌")


@router.post("/sms/send", summary="发送短信验证码")
async def send_sms_code(
    data: _SmsSendModel,
    current_user: Annotated[User, Depends(get_current_user)],
):
    import random
    code = f"{random.randint(100000, 999999)}"
    try:
        from app.services.cache_service import cache_service
        cache_key = f"sms_code:{data.scene}:{data.phone}"
        await cache_service.set_json(
            cache_key,
            {"code": code, "phone": data.phone, "scene": data.scene, "created_at": datetime.now().isoformat()},
            expire=300,
        )
    except Exception:
        pass
    resp = {"success": True, "message": "验证码已发送"}
    if getattr(settings, 'debug', False):
        resp["code"] = code
    return resp


@router.post("/sms/verify", summary="验证短信验证码")
async def verify_sms_code(
    data: _SmsVerifyModel,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    try:
        from app.services.cache_service import cache_service
        cache_key = f"sms_code:{data.scene}:{data.phone}"
        cached = await cache_service.get_json(cache_key)
        if not cached or cached.get("code") != data.code:
            raise HTTPException(status_code=400, detail="验证码无效或已过期")
        await cache_service.delete(cache_key)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")

    current_user.phone = data.phone
    current_user.phone_verified = True
    current_user.phone_verified_at = datetime.now()
    db.add(current_user)
    await db.commit()
    return {"success": True, "message": "手机验证成功"}


@router.get("/admin/list", summary="管理员获取用户列表")
async def admin_list_users(
    page: int = 1,
    page_size: int = 20,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db=Depends(get_db),
):
    from app.utils.permissions import has_any_role, Role
    if not has_any_role(current_user, [Role.ADMIN, Role.SUPER_ADMIN]):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    from sqlalchemy import select as sa_select, func
    from app.services.user_service import UserService
    users, total = await UserService.get_user_list(db, page=page, page_size=page_size)
    items = []
    for u in users:
        items.append({
            "id": u.id, "username": u.username, "email": u.email,
            "nickname": u.nickname, "role": u.role, "is_active": u.is_active,
            "created_at": str(u.created_at) if u.created_at else None,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.put("/admin/{user_id}/toggle-active", summary="管理员切换用户状态")
async def admin_toggle_user_active(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db=Depends(get_db),
):
    from app.utils.permissions import has_any_role, Role
    if not has_any_role(current_user, [Role.ADMIN, Role.SUPER_ADMIN]):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能修改自己的状态")
    from sqlalchemy import select as sa_select
    result = await db.execute(sa_select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = not user.is_active
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "is_active": user.is_active, "username": user.username, "role": user.role}


@router.put("/admin/{user_id}/role", summary="管理员修改用户角色")
async def admin_update_user_role(
    user_id: int,
    role: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db=Depends(get_db),
):
    from app.utils.permissions import has_any_role, Role
    if not has_any_role(current_user, [Role.ADMIN, Role.SUPER_ADMIN]):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    valid_roles = {"user", "lawyer", "moderator", "admin", "super_admin"}
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail="无效的角色")
    from sqlalchemy import select as sa_select
    result = await db.execute(sa_select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.role = role
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "role": user.role, "username": user.username}


@router.get("/me/quota-usage", summary="获取配额消耗记录")
async def get_quota_usage(
    days: int = 7,
    page: int = 1,
    page_size: int = 20,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    if days > 365:
        raise HTTPException(status_code=422, detail="days参数不能超过365")
    return {"usage": [], "total": 0, "page": page, "page_size": page_size}


@router.post("/admin/debug/password-reset-token", summary="调试获取密码重置令牌")
async def admin_debug_password_reset_token(
    data: _PasswordResetRequestModel,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db=Depends(get_db),
):
    if not getattr(settings, 'debug', False):
        raise HTTPException(status_code=404, detail="Not Found")
    from app.utils.permissions import has_any_role, Role
    if not has_any_role(current_user, [Role.ADMIN, Role.SUPER_ADMIN]):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    from sqlalchemy import select as sa_select
    result = await db.execute(sa_select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    try:
        from app.services.email_service import email_service
        token = await email_service.generate_reset_token(user.id, user.email)
        return {"token": token, "reset_url": f"http://localhost:3000/reset-password?token={token}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
