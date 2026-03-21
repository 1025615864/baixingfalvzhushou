"""认证路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import User
from ..services.auth_service import AuthService

router = APIRouter()


class LoginRequest(BaseModel):
    phone: str
    password: str


class RegisterRequest(BaseModel):
    phone: str
    password: str
    sms_code: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(lambda: AsyncSessionLocal())):
    """用户登录"""
    auth_service = AuthService(db)
    result = await auth_service.login(request.phone, request.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    return result


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(lambda: AsyncSessionLocal())):
    """用户注册"""
    auth_service = AuthService(db)
    result = await auth_service.register(request.phone, request.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed"
        )

    return result


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """刷新Token"""
    # TODO: 实现Token刷新
    pass
