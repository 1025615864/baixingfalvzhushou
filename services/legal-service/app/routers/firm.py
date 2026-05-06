"""律所路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import LawFirm
from ..services.firm_service import FirmService
from ..services.invitation_service import InvitationService
from ..middleware.auth import get_current_user, AuthUser
from ..schemas.response import ApiResponse, PaginatedData

router = APIRouter()


class FirmCreateRequest(BaseModel):
    name: str
    license_no: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None


class FirmVerificationRequest(BaseModel):
    license_image: Optional[str] = None
    id_card_image: Optional[str] = None


class FirmUpdateRequest(BaseModel):
    name: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None


class InvitationCreateRequest(BaseModel):
    lawyer_id: int
    firm_role: str = "associate"
    message: Optional[str] = None


class FirmResponse(BaseModel):
    id: int
    user_id: int
    name: str
    license_no: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    status: str
    lawyer_count: int = 0

    class Config:
        from_attributes = True


class LawyerInFirmResponse(BaseModel):
    id: int
    user_id: int
    name: str
    title: Optional[str] = None
    firm_role: Optional[str] = None
    status: str
    rating: float
    consultation_count: int

    class Config:
        from_attributes = True


class InvitationResponse(BaseModel):
    id: int
    lawfirm_id: int
    lawyer_id: int
    status: str
    firm_role: str
    message: Optional[str] = None
    expires_at: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/", status_code=201)
async def create_firm(
    request: FirmCreateRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """申请入驻律所"""
    service = FirmService(db)
    firm = await service.create_firm(
        user_id=current_user.id,
        name=request.name,
        license_no=request.license_no,
        province=request.province,
        city=request.city,
        address=request.address,
        phone=request.phone,
        email=request.email,
        description=request.description,
    )
    return ApiResponse.success(FirmResponse.model_validate(firm))


@router.get("/")
async def list_firms(
    page: int = 1,
    page_size: int = 20,
    province: Optional[str] = None,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律所列表 - 公开接口"""
    service = FirmService(db)
    firms, total = await service.list_firms(page, page_size, province, status="verified")
    items = [FirmResponse.model_validate(f) for f in firms]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.get("/{firm_id}")
async def get_firm(
    firm_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律所详情"""
    service = FirmService(db)
    firm = await service.get_firm(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="律所不存在")
    return ApiResponse.success(FirmResponse.model_validate(firm))


@router.patch("/{firm_id}")
async def update_firm(
    firm_id: int,
    request: FirmUpdateRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """更新律所信息"""
    service = FirmService(db)
    firm = await service.get_firm(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="律所不存在")

    if firm.user_id != current_user.id and current_user.role not in ["admin", "platform_firm_admin"]:
        raise HTTPException(status_code=403, detail="无权操作")

    updated = await service.update_firm(
        firm_id,
        name=request.name,
        province=request.province,
        city=request.city,
        address=request.address,
        phone=request.phone,
        email=request.email,
        description=request.description,
    )
    return ApiResponse.success(FirmResponse.model_validate(updated))


@router.post("/{firm_id}/verification")
async def submit_verification(
    firm_id: int,
    request: FirmVerificationRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """提交资质审核"""
    service = FirmService(db)
    firm = await service.get_firm(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="律所不存在")

    if firm.user_id != current_user.id and current_user.role not in ["admin", "platform_firm_admin"]:
        raise HTTPException(status_code=403, detail="无权操作")

    verification = await service.submit_verification(
        firm_id=firm_id,
        license_image=request.license_image,
        id_card_image=request.id_card_image,
    )
    return ApiResponse.success({"status": verification.status})


@router.get("/{firm_id}/verification")
async def get_verification_status(
    firm_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取审核状态"""
    service = FirmService(db)
    verification = await service.get_verification_status(firm_id)
    if not verification:
        raise HTTPException(status_code=404, detail="暂无审核记录")
    return ApiResponse.success({
        "status": verification.status,
        "rejection_reason": verification.rejection_reason,
        "reviewed_at": verification.reviewed_at.isoformat() if verification.reviewed_at else None,
    })


@router.get("/{firm_id}/lawyers")
async def get_firm_lawyers(
    firm_id: int,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律所律师列表"""
    service = FirmService(db)
    lawyers, total = await service.get_firm_lawyers(firm_id, page, page_size)
    items = [LawyerInFirmResponse.model_validate(l) for l in lawyers]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.post("/{firm_id}/invitations")
async def create_invitation(
    firm_id: int,
    request: InvitationCreateRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """邀请律师加入律所"""
    service = FirmService(db)
    invitation_service = InvitationService(db)

    if not await service.is_firm_admin(firm_id, current_user.id):
        if current_user.role not in ["admin", "platform_firm_admin"]:
            raise HTTPException(status_code=403, detail="只有律所管理员可以邀请律师")

    try:
        invitation = await invitation_service.create_invitation(
            lawfirm_id=firm_id,
            lawyer_id=request.lawyer_id,
            invited_by_user_id=current_user.id,
            firm_role=request.firm_role,
            message=request.message,
        )
        return ApiResponse.success(InvitationResponse.model_validate(invitation))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{firm_id}/invitations")
async def get_firm_invitations(
    firm_id: int,
    status: Optional[str] = None,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律所的邀请列表"""
    service = FirmService(db)

    if not await service.is_firm_admin(firm_id, current_user.id):
        if current_user.role not in ["admin", "platform_firm_admin"]:
            raise HTTPException(status_code=403, detail="只有律所管理员可以查看邀请")

    invitation_service = InvitationService(db)
    invitations = await invitation_service.get_invitations_by_firm(firm_id, status)
    items = [
        {
            "id": inv.id,
            "lawfirm_id": inv.lawfirm_id,
            "lawyer_id": inv.lawyer_id,
            "status": inv.status,
            "firm_role": inv.firm_role,
            "message": inv.message,
            "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        }
        for inv in invitations
    ]
    return ApiResponse.success({"items": items, "total": len(items)})


@router.delete("/{firm_id}/lawyers/{lawyer_id}")
async def remove_lawyer_from_firm(
    firm_id: int,
    lawyer_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """从律所移除律师"""
    service = FirmService(db)

    if not await service.is_firm_admin(firm_id, current_user.id):
        if current_user.role not in ["admin", "platform_firm_admin"]:
            raise HTTPException(status_code=403, detail="只有律所管理员可以移除律师")

    invitation_service = InvitationService(db)
    success = await invitation_service.remove_lawyer_from_firm(lawyer_id, firm_id)

    if not success:
        raise HTTPException(status_code=404, detail="律师不在该律所或不存在")

    return ApiResponse.success({"message": "律师已从律所移除"})
