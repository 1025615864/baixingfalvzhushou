"""用户认证 API 路由

提供登录、注册、刷新 Token、登出等功能。
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.user import User
from ..config import get_settings
from ..utils.security import (
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["认证"])

settings = get_settings()


# ==================== 请求模型 ====================

class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    nickname: str | None = Field(default=None, max_length=50, description="昵称")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="刷新 Token")


# ==================== 响应模型 ====================

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class AuthResponse(BaseModel):
    message: str
    user: dict[str, object]
    token: TokenResponse | None = None


class SuccessResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


# ==================== 路由 ====================

@router.post("/login", response_model=AuthResponse, summary="用户登录")
async def login(
    data: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """用户登录接口

    支持用户名或邮箱登录。
    """
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

    return AuthResponse(
        message="登录成功",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "avatar_url": user.avatar,
            "role": user.role,
        },
        token=TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
        ),
    )


@router.post("/register", response_model=AuthResponse, summary="用户注册")
async def register(
    data: RegisterRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """用户注册接口"""
    existing = await db.execute(
        select(User).where(
            (User.username == data.username) | (User.email == data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名或邮箱已存在",
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

    return AuthResponse(
        message="注册成功",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "avatar_url": user.avatar,
            "role": user.role,
        },
        token=TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
        ),
    )


@router.post("/logout", response_model=SuccessResponse, summary="用户登出")
async def logout(response: Response):
    """用户登出接口"""
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return SuccessResponse(message="登出成功")


@router.post("/refresh", response_model=TokenResponse, summary="刷新 Token")
async def refresh_token(
    data: RefreshRequest,
    response: Response,
):
    """刷新访问 Token"""
    from ..utils.security import decode_access_token

    payload = decode_access_token(data.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新 Token",
        )

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新 Token",
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(sub)},
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

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )
