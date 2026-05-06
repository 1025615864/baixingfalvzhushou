"""密码重置路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.password_reset_service import PasswordResetService

router = APIRouter(prefix="/auth", tags=["认证"])


class PasswordResetRequest(BaseModel):
    phone: str


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str


class PasswordResetResponse(BaseModel):
    message: str
    success: bool


@router.post(
    "/password/reset",
    response_model=PasswordResetResponse,
    summary="请求密码重置",
    description="通过手机号请求密码重置，会发送验证码/令牌到用户手机或邮箱。",
)
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """请求密码重置

    - **phone**: 注册时的手机号

    返回成功表示验证码已发送。
    """
    service = PasswordResetService(db)
    token = await service.create_reset_token(request.phone)

    if not token:
        return PasswordResetResponse(
            success=True,
            message="如果该手机号已注册，重置链接已发送"
        )

    return PasswordResetResponse(
        success=True,
        message="重置令牌已生成"
    )


@router.post(
    "/password/reset/confirm",
    response_model=PasswordResetResponse,
    summary="确认密码重置",
    description="使用收到的令牌和新密码完成密码重置。",
    responses={
        200: {"description": "密码重置成功"},
        400: {"description": "令牌无效或密码不符合要求"},
    }
)
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """确认密码重置

    - **token**: 之前请求获取的重置令牌
    - **new_password**: 新密码（需满足强度要求）

    密码重置成功后需要重新登录。
    """
    service = PasswordResetService(db)
    success, error_msg = await service.reset_password(request.token, request.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    return PasswordResetResponse(
        success=True,
        message="密码重置成功，请使用新密码登录"
    )
