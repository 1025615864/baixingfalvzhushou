"""律所管理路由"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select, func, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.lawfirm import LawFirm
from ...models.user import User
from ...schemas.lawfirm import (
    LawFirmCreate, LawFirmUpdate, LawFirmResponse, LawFirmListResponse,
)
from ...services.lawfirm_service import lawfirm_service
from ...utils.deps import require_admin

router = APIRouter(prefix="/firms", tags=["律所管理"])


def _split_specialties(value: str | None) -> list[str]:
    """分割专业领域"""
    if not value:
        return []
    parts = [p.strip() for p in value.replace("，", ",").split(",")]
    return [p for p in parts if p]


def _format_firm_response(
        firm: LawFirm, lawyer_count: int = 0) -> LawFirmResponse:
    """格式化律所响应"""
    return LawFirmResponse(
        id=firm.id,
        name=firm.name,
        description=firm.description,
        address=firm.address,
        city=firm.city,
        province=firm.province,
        phone=firm.phone,
        email=firm.email,
        website=firm.website,
        logo=firm.logo,
        license_no=firm.license_no,
        specialties=_split_specialties(firm.specialties),
        rating=firm.rating,
        review_count=firm.review_count,
        is_verified=firm.is_verified,
        is_active=firm.is_active,
        created_at=firm.created_at,
        lawyer_count=lawyer_count
    )


@router.get("", response_model=LawFirmListResponse, summary="获取律所列表")
async def get_law_firms(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    city: str | None = None,
    keyword: str | None = None,
):
    """获取律所列表"""
    firms, total = await lawfirm_service.get_list(db, page, page_size, city, keyword)

    items = []
    for firm in firms:
        lawyer_count = await lawfirm_service.get_lawyer_count(db, firm.id)
        items.append(_format_firm_response(firm, lawyer_count))

    return LawFirmListResponse(
        items=items, total=total, page=page, page_size=page_size)


@router.get("/{firm_id}", response_model=LawFirmResponse, summary="获取律所详情")
async def get_law_firm(
        firm_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    """获取律所详情"""
    firm = await lawfirm_service.get_by_id(db, firm_id)
    if not firm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="律所不存在")

    lawyer_count = await lawfirm_service.get_lawyer_count(db, firm.id)
    return _format_firm_response(firm, lawyer_count)


@router.post("", response_model=LawFirmResponse, summary="创建律所")
async def create_law_firm(
    data: LawFirmCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """创建律所（需要管理员权限）"""
    _ = current_user
    firm = await lawfirm_service.create(db, data)
    return _format_firm_response(firm)


@router.put("/{firm_id}", response_model=LawFirmResponse, summary="更新律所")
async def update_law_firm(
    firm_id: int,
    data: LawFirmUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """更新律所（需要管理员权限）"""
    _ = current_user
    firm = await lawfirm_service.update(db, firm_id, data)
    if not firm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="律所不存在")
    return _format_firm_response(firm)


@router.delete("/{firm_id}", summary="删除律所")
async def delete_law_firm(
    firm_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """删除律所（需要管理员权限）"""
    _ = current_user
    success = await lawfirm_service.delete(db, firm_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="律所不存在")
    return {"detail": "律所已删除"}


# ==================== 批量审核和状态管理 ====================

class BatchVerifyRequest(BaseModel):
    """批量审核请求"""
    firm_ids: list[int]
    is_verified: bool
    reason: str | None = None


class BatchVerifyResponse(BaseModel):
    """批量审核响应"""
    success_count: int
    failed_count: int
    failed_ids: list[int]


class FirmStatusUpdateRequest(BaseModel):
    """律所状态更新请求"""
    is_active: bool


@router.post("/batch/verify", response_model=BatchVerifyResponse, summary="批量审核律所")
async def batch_verify_law_firms(
    data: BatchVerifyRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """批量审核律所认证状态（需要管理员权限）"""
    _ = current_user
    
    success_count = 0
    failed_ids = []
    
    for firm_id in data.firm_ids:
        try:
            firm = await lawfirm_service.get_by_id(db, firm_id)
            if firm:
                firm.is_verified = data.is_verified
                await db.commit()
                success_count += 1
            else:
                failed_ids.append(firm_id)
        except Exception:
            failed_ids.append(firm_id)
    
    return BatchVerifyResponse(
        success_count=success_count,
        failed_count=len(failed_ids),
        failed_ids=failed_ids
    )


@router.put("/{firm_id}/status", response_model=LawFirmResponse, summary="更新律所状态")
async def update_law_firm_status(
    firm_id: int,
    data: FirmStatusUpdateRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """更新律所启用/停用状态（需要管理员权限）"""
    _ = current_user
    
    firm = await lawfirm_service.get_by_id(db, firm_id)
    if not firm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="律所不存在")
    
    firm.is_active = data.is_active
    await db.commit()
    await db.refresh(firm)
    
    lawyer_count = await lawfirm_service.get_lawyer_count(db, firm.id)
    return _format_firm_response(firm, lawyer_count)


@router.put("/{firm_id}/verify", response_model=LawFirmResponse, summary="审核律所")
async def verify_law_firm(
    firm_id: int,
    is_verified: bool,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """审核律所认证（需要管理员权限）"""
    _ = current_user
    
    firm = await lawfirm_service.get_by_id(db, firm_id)
    if not firm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="律所不存在")
    
    firm.is_verified = is_verified
    await db.commit()
    await db.refresh(firm)
    
    lawyer_count = await lawfirm_service.get_lawyer_count(db, firm.id)
    return _format_firm_response(firm, lawyer_count)


@router.get("/statistics/overview", summary="律所统计概览")
async def get_law_firm_statistics(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取律所统计概览（需要管理员权限）"""
    _ = current_user
    
    # 总律所数
    total_res = await db.execute(select(func.count(LawFirm.id)))
    total_count = int(total_res.scalar() or 0)
    
    # 已认证律所数
    verified_res = await db.execute(
        select(func.count(LawFirm.id)).where(LawFirm.is_verified == True)
    )
    verified_count = int(verified_res.scalar() or 0)
    
    # 启用中的律所数
    active_res = await db.execute(
        select(func.count(LawFirm.id)).where(LawFirm.is_active == True)
    )
    active_count = int(active_res.scalar() or 0)
    
    # 待审核律所数（未认证且活跃的）
    pending_res = await db.execute(
        select(func.count(LawFirm.id)).where(
            LawFirm.is_verified == False,
            LawFirm.is_active == True
        )
    )
    pending_count = int(pending_res.scalar() or 0)
    
    # 按城市统计
    city_res = await db.execute(
        select(LawFirm.city, func.count(LawFirm.id))
        .where(LawFirm.city.isnot(None))
        .group_by(LawFirm.city)
        .order_by(desc(func.count(LawFirm.id)))
        .limit(10)
    )
    city_stats = [{"city": city, "count": count} for city, count in city_res.all()]
    
    return {
        "total_count": total_count,
        "verified_count": verified_count,
        "active_count": active_count,
        "pending_count": pending_count,
        "city_stats": city_stats
    }
