"""邮箱验证路由"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.email_verification_service import EmailVerificationService
from ..middleware.auth import get_current_user
from ..models import User

router = APIRouter(prefix="/auth", tags=["认证"])


class SendVerificationRequest(BaseModel):
    email: str


class SendVerificationResponse(BaseModel):
    success: bool
    message: str


class VerifyEmailRequest(BaseModel):
    token: str


class VerifyEmailResponse(BaseModel):
    success: bool
    message: str


class EmailStatusResponse(BaseModel):
    email: str
    verified: bool


@router.post(
    "/email/send-verification",
    response_model=SendVerificationResponse,
    summary="发送邮箱验证",
    description="发送邮箱验证链接到用户邮箱。",
)
async def send_verification(
    request: SendVerificationRequest,
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """发送邮箱验证

    - **email**: 需要验证的邮箱地址

    如果邮箱已注册且未验证，将发送验证链接。
    """
    service = EmailVerificationService(db)
    success, message = await service.resend_verification(request.email)

    return SendVerificationResponse(success=success, message=message)


@router.post(
    "/email/verify",
    response_model=VerifyEmailResponse,
    summary="验证邮箱",
    description="使用收到的令牌验证邮箱。",
)
async def verify_email(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """验证邮箱

    - **token**: 邮件中的验证令牌

    验证成功后，邮箱状态变为已验证。
    """
    service = EmailVerificationService(db)
    success, user_info = await service.verify_token(request.token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    return VerifyEmailResponse(
        success=True,
        message="Email verified successfully"
    )


@router.get(
    "/email/status",
    response_model=EmailStatusResponse,
    summary="获取邮箱验证状态",
    description="获取当前用户邮箱的验证状态。",
)
async def get_email_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """获取邮箱验证状态"""
    return EmailStatusResponse(
        email=current_user.email or "",
        verified=current_user.email_verified,
    )


@router.post(
    "/email/resend",
    response_model=SendVerificationResponse,
    summary="重新发送验证（需登录）",
    description="为当前登录用户重新发送邮箱验证。",
)
async def resend_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """重新发送验证邮件（需登录）"""
    if not current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email address associated with this account"
        )

    service = EmailVerificationService(db)
    success, message = await service.resend_verification(current_user.email)

    return SendVerificationResponse(success=success, message=message)
