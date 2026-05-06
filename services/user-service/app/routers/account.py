"""账号注销路由 - 冷静期机制"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.account_deletion_service import AccountDeletionService
from ..middleware.auth import get_current_user
from ..models import User

router = APIRouter(prefix="/account", tags=["账号"])


class DeletionRequest(BaseModel):
    reason: Optional[str] = None


class DeletionStatusResponse(BaseModel):
    status: str
    in_grace_period: bool
    requested_at: Optional[str] = None
    grace_end_at: Optional[str] = None
    remaining_days: int = 0


class DeletionResponse(BaseModel):
    success: bool
    message: str


@router.post(
    "/deletion/request",
    response_model=DeletionResponse,
    summary="请求账号注销",
    description=f"请求注销账号，进入{7}天冷静期。冷静期内可取消注销。",
)
async def request_deletion(
    request: Request,
    deletion_request: Optional[DeletionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """请求账号注销（进入冷静期）

    - 冷静期为7天
    - 冷静期内可随时取消
    - 冷静期结束后自动执行注销
    """
    ip_address = request.client.host if request.client else None
    reason = deletion_request.reason if deletion_request else None

    service = AccountDeletionService(db)
    success, message = await service.request_deletion(
        user_id=current_user.id,
        reason=reason,
        ip_address=ip_address,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return DeletionResponse(success=True, message=message)


@router.post(
    "/deletion/cancel",
    response_model=DeletionResponse,
    summary="取消账号注销",
    description="取消待执行的账号注销，恢复账号正常使用。",
)
async def cancel_deletion(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """取消账号注销

    取消后账号恢复正常使用。
    """
    ip_address = request.client.host if request.client else None

    service = AccountDeletionService(db)
    success, message = await service.cancel_deletion(
        user_id=current_user.id,
        ip_address=ip_address,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return DeletionResponse(success=True, message=message)


@router.post(
    "/deletion/confirm",
    response_model=DeletionResponse,
    summary="确认立即注销",
    description="跳过冷静期，立即注销账号。",
)
async def confirm_deletion(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """确认立即注销

    立即永久注销账号，不可恢复。
    """
    ip_address = request.client.host if request.client else None

    service = AccountDeletionService(db)
    success, message = await service.confirm_deletion(
        user_id=current_user.id,
        ip_address=ip_address,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return DeletionResponse(success=True, message=message)


@router.get(
    "/deletion/status",
    response_model=DeletionStatusResponse,
    summary="获取注销状态",
    description="查看当前账号的注销处理状态。",
)
async def get_deletion_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """获取注销状态"""
    service = AccountDeletionService(db)
    status = await service.get_deletion_status(current_user.id)

    if not status:
        raise HTTPException(status_code=404, detail="用户不存在")

    return DeletionStatusResponse(**status)
