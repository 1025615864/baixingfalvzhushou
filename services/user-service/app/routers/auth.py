"""认证路由

提供用户登录、注册、Token刷新等功能。
支持登录频率限制和Token撤销机制。
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import User
from ..services.auth_service import AuthService

router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求"""
    phone: str
    password: str


class RegisterRequest(BaseModel):
    """注册请求"""
    phone: str
    password: str


class RefreshRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    access_jti: str | None = None
    refresh_jti: str | None = None
    uid: str | None = None


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    id: int
    uid: str
    phone: str
    role: str
    status: str


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="用户登录",
    description="使用手机号和密码登录。连续5次失败后会被锁定15分钟。",
    responses={
        200: {"description": "登录成功"},
        401: {"description": "手机号或密码错误"},
        429: {"description": "登录尝试次数过多，账户已被锁定或请求过于频繁"},
    }
)
async def login(
    request: Request,
    login_request: LoginRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """用户登录

    - **phone**: 手机号
    - **password**: 密码

    登录成功后返回 access_token 和 refresh_token。
    """
    try:
        from ..middleware import check_request_rate_limit
        await check_request_rate_limit(request)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="登录请求过于频繁，请稍后再试"
        )

    ip_address = request.client.host if request.client else None
    auth_service = AuthService(db)
    result = await auth_service.login(login_request.phone, login_request.password, ip_address)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if result.get("error") == "too_many_attempts":
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=result.get("message"),
            headers={"Retry-After": str(result.get("retry_after", 900))}
        )

    return result


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="用户注册",
    description="注册新用户账号。密码长度至少8位，需包含大小写字母和数字。",
    responses={
        200: {"description": "注册成功"},
        400: {"description": "手机号已注册或密码不符合要求"},
        429: {"description": "注册过于频繁，请稍后再试"},
    }
)
async def register(
    register_request: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """用户注册

    - **phone**: 手机号（将作为登录账号）
    - **password**: 密码（至少8位，需包含大小写字母和数字）

    注册成功后自动登录并返回Token。
    """
    try:
        from ..middleware import check_request_rate_limit, check_register_rate_limit
        await check_request_rate_limit(request)
        await check_register_rate_limit(request, register_request.phone)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="注册过于频繁，请稍后再试"
        )

    auth_service = AuthService(db)
    result = await auth_service.register(register_request.phone, register_request.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已注册"
        )

    if result.get("error") == "weak_password":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Password does not meet security requirements")
        )

    return result


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新Token",
    description="使用refresh_token获取新的access_token。旧的refresh_token会被撤销。",
    responses={
        200: {"description": "刷新成功"},
        401: {"description": "refresh_token无效或已过期"},
    }
)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """刷新访问令牌

    - **refresh_token**: 刷新令牌（在登录时获取）

    返回新的access_token和refresh_token。
    """
    auth_service = AuthService(db)
    result = await auth_service.refresh_access_token(request.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    return result


@router.get(
    "/me",
    response_model=UserInfoResponse,
    summary="获取当前用户",
    description="获取当前登录用户的信息。需要携带有效的access_token。",
    responses={
        200: {"description": "成功获取用户信息"},
        401: {"description": "未认证或token已过期"},
    }
)
async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取当前用户信息

    需要在请求头中携带: `Authorization: Bearer <access_token>`
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    token = authorization[7:]
    auth_service = AuthService(db)
    user_info = await auth_service.verify_token(token)

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    result = await db.execute(select(User).where(User.id == user_info["user_id"]))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserInfoResponse(
        id=user.id,
        uid=user.uid,
        phone=user.phone or "",
        role=user.role,
        status=user.status
    )


class JWKSResponse(BaseModel):
    """JWKS响应"""
    keys: list[dict]


@router.get(
    "/.well-known/jwks.json",
    response_model=JWKSResponse,
    summary="获取JWKS",
    description="获取公钥用于验证Token。用于其他服务验证User Service签发的Token。",
    tags=["认证"],
)
async def get_jwks():
    """获取JWKS公钥端点

    返回公钥信息，其他服务可用于验证JWT Token。
    """
    from ..core.jwt_keys import jwt_key_manager

    public_key_pem = jwt_key_manager.get_public_key_pem()
    if not public_key_pem:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Public key not available"
        )

    return JWKSResponse(
        keys=[
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "n": public_key_pem,
                "e": "AQAB",
            }
        ]
    )
