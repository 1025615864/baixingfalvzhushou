"""律师认证路由"""

from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.lawfirm import Lawyer, LawyerVerification
from ...models.user import User
from ...schemas.lawfirm import (
    VerificationCreate, VerificationResponse, VerificationListResponse,
)
from ...services.lawfirm_service import verification_service
from ...utils.deps import get_current_user, require_admin

router = APIRouter(prefix="/verification", tags=["律师认证"])


@router.post("/apply", summary="申请律师认证")
async def apply_verification(
    data: VerificationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """用户申请律师认证"""
    # 使用服务层创建认证申请
    try:
        verification = await verification_service.create(db, current_user.id, data)
        return {"detail": "认证申请已提交", "verification_id": verification.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status", summary="查询认证状态")
async def get_verification_status(current_user: Annotated[User, Depends(
        get_current_user)], db: AsyncSession = Depends(get_db)):
    """查询当前用户的认证状态"""
    from ...schemas.lawfirm import VerificationStatusResponse
    from sqlalchemy import select

    verification = await verification_service.get_by_user_id(db, current_user.id)

    lawyer = await db.execute(
        select(Lawyer).where(Lawyer.user_id == current_user.id)
    )
    lawyer_data = lawyer.scalar_one_or_none()

    return VerificationStatusResponse(
        has_verification=verification is not None,
        verification_status=verification.status if verification else None,
        verification_id=verification.id if verification else None,
        submitted_at=verification.created_at if verification else None,
        reviewed_at=verification.reviewed_at if verification else None,
        reject_reason=verification.reject_reason if verification else None,
        is_verified_lawyer=lawyer_data.is_verified if lawyer_data else False,
    )


@router.get("/admin/verifications",
            response_model=VerificationListResponse, summary="获取认证申请列表（管理员）")
async def admin_list_verifications(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: str | None = None,
):
    """管理员获取认证申请列表"""
    _ = current_user

    # 使用服务层获取认证申请列表
    verifications, total = await verification_service.get_list(db, page, page_size, status_filter)

    items = []
    for v in verifications:
        items.append(VerificationResponse(
            id=v.id,
            user_id=v.user_id,
            real_name=v.real_name,
            firm_name=v.firm_name,
            license_no=v.license_no,
            specialties=v.specialties,
            introduction=v.introduction,
            experience_years=v.experience_years,
            status=v.status,
            reject_reason=v.reject_reason,
            created_at=v.created_at,
            reviewed_at=v.reviewed_at,
        ))

    return VerificationListResponse(
        items=items, total=total, page=page, page_size=page_size)


@router.post("/admin/verifications/{verification_id}/review",
             summary="审核认证申请（管理员）")
async def admin_review_verification(
    verification_id: int,
    approved: bool,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    reject_reason: str = "",
):
    """管理员审核认证申请"""
    _ = current_user

    if approved:
        verification = await verification_service.approve(db, verification_id, current_user.id)
    else:
        verification = await verification_service.reject(db, verification_id, current_user.id, reject_reason or "")

    if not verification:
        raise HTTPException(status_code=404, detail="认证申请不存在")

    if approved:
        # 创建律师记录
        from ...models.lawfirm import Lawyer
        lawyer = Lawyer(
            user_id=verification.user_id,
            name=verification.real_name,
            license_no=verification.license_no,
            firm_name=verification.firm_name,
            specialties=verification.specialties,
            introduction=verification.introduction,
            experience_years=verification.experience_years,
            is_verified=True,
            is_active=True,
        )
        db.add(lawyer)
        await db.commit()

    return {"detail": f"认证申请已{'通过' if approved else '拒绝'}"}
