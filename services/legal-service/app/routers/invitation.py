"""律师邀请响应路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.invitation_service import InvitationService
from ..services.lawyer_service import LawyerService
from ..middleware.auth import get_current_user, get_current_lawyer, AuthUser
from ..schemas.response import ApiResponse

router = APIRouter()


class InvitationDetailResponse(BaseModel):
    id: int
    lawfirm_id: int
    lawyer_id: int
    status: str
    firm_role: str
    message: Optional[str] = None
    expires_at: str
    responded_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


@router.post("/{invitation_id}/accept")
async def accept_invitation(
    invitation_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """接受邀请"""
    invitation_service = InvitationService(db)
    lawyer_service = LawyerService(db)

    # 获取律师信息
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    # 获取邀请信息并验证
    invitation = await invitation_service.get_invitation(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="邀请不存在")

    if invitation.lawyer_id != lawyer.id:
        raise HTTPException(status_code=403, detail="该邀请不是给您的")

    try:
        result = await invitation_service.accept_invitation(invitation_id)
        return ApiResponse.success({
            "id": result.id,
            "status": result.status,
            "lawfirm_id": result.lawfirm_id,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{invitation_id}/reject")
async def reject_invitation(
    invitation_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """拒绝邀请"""
    invitation_service = InvitationService(db)
    lawyer_service = LawyerService(db)

    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    invitation = await invitation_service.get_invitation(invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="邀请不存在")

    if invitation.lawyer_id != lawyer.id:
        raise HTTPException(status_code=403, detail="该邀请不是给您的")

    try:
        result = await invitation_service.reject_invitation(invitation_id)
        return ApiResponse.success({"id": result.id, "status": result.status})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
async def get_my_invitations(
    status: Optional[str] = None,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取我的邀请列表"""
    lawyer_service = LawyerService(db)
    invitation_service = InvitationService(db)

    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    invitations = await invitation_service.get_pending_invitations_by_lawyer(lawyer.id)

    if status:
        invitations = [inv for inv in invitations if inv.status == status]

    items = [
        {
            "id": inv.id,
            "lawfirm_id": inv.lawfirm_id,
            "lawyer_id": inv.lawyer_id,
            "status": inv.status,
            "firm_role": inv.firm_role,
            "message": inv.message,
            "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
            "responded_at": inv.responded_at.isoformat() if inv.responded_at else None,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        }
        for inv in invitations
    ]
    return ApiResponse.success({"items": items, "total": len(items)})