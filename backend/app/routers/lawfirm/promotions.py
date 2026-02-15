"""推广链接路由"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...schemas.lawfirm import (
    LawyerPromotionLinkCreate,
    LawyerPromotionLinkUpdate,
    LawyerPromotionLinkResponse,
    LawyerPromotionLinkListResponse,
    LawyerPromotionLinkStatsResponse,
)
from ...services.lawyer_promotion_link_service import LawyerPromotionLinkService
from ...utils.deps import get_current_user

router = APIRouter(prefix="/lawyer/promotion-links", tags=["推广链接"])


async def _require_verified_lawyer(db: AsyncSession, current_user: User):
    """获取当前用户的律师信息"""
    from ...models.lawfirm import Lawyer
    from sqlalchemy import select

    res = await db.execute(
        select(Lawyer).where(
            Lawyer.user_id == int(current_user.id),
            Lawyer.is_active,
        )
    )
    lawyer = res.scalar_one_or_none()
    if not lawyer:
        raise HTTPException(status_code=403, detail="未绑定律师资料")
    return lawyer


@router.get("", response_model=LawyerPromotionLinkListResponse,
            summary="律师-获取推广链接列表")
async def lawyer_get_promotion_links(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    is_active: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """律师获取自己的推广链接列表"""
    lawyer = await _require_verified_lawyer(db, current_user)

    links, total = await LawyerPromotionLinkService.get_list(
        db,
        int(lawyer.id),
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

    items = []
    for link in links:
        items.append(LawyerPromotionLinkResponse(
            id=link.id,
            lawyer_id=link.lawyer_id,
            link_code=link.link_code,
            link_name=link.link_name,
            description=link.description,
            is_active=link.is_active,
            click_count=link.click_count,
            consultation_count=link.consultation_count,
            conversion_count=link.conversion_count,
            created_at=link.created_at,
            updated_at=link.updated_at,
        ))

    return LawyerPromotionLinkListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=LawyerPromotionLinkResponse,
             summary="律师-创建推广链接")
async def lawyer_create_promotion_link(
    data: LawyerPromotionLinkCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师创建推广链接"""
    lawyer = await _require_verified_lawyer(db, current_user)

    link = await LawyerPromotionLinkService.create(db, int(lawyer.id), data)

    return LawyerPromotionLinkResponse(
        id=link.id,
        lawyer_id=link.lawyer_id,
        link_code=link.link_code,
        link_name=link.link_name,
        description=link.description,
        is_active=link.is_active,
        click_count=link.click_count,
        consultation_count=link.consultation_count,
        conversion_count=link.conversion_count,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.get("/{link_id}", response_model=LawyerPromotionLinkResponse,
            summary="律师-获取推广链接详情")
async def lawyer_get_promotion_link(
    link_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师获取推广链接详情"""
    lawyer = await _require_verified_lawyer(db, current_user)

    link = await LawyerPromotionLinkService.get_by_id(db, link_id, int(lawyer.id))

    if not link:
        raise HTTPException(status_code=404, detail="推广链接不存在")

    return LawyerPromotionLinkResponse(
        id=link.id,
        lawyer_id=link.lawyer_id,
        link_code=link.link_code,
        link_name=link.link_name,
        description=link.description,
        is_active=link.is_active,
        click_count=link.click_count,
        consultation_count=link.consultation_count,
        conversion_count=link.conversion_count,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.put("/{link_id}",
            response_model=LawyerPromotionLinkResponse, summary="律师-更新推广链接")
async def lawyer_update_promotion_link(
    link_id: int,
    data: LawyerPromotionLinkUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师更新推广链接"""
    lawyer = await _require_verified_lawyer(db, current_user)

    link = await LawyerPromotionLinkService.update(db, link_id, int(lawyer.id), data)

    if not link:
        raise HTTPException(status_code=404, detail="推广链接不存在")

    return LawyerPromotionLinkResponse(
        id=link.id,
        lawyer_id=link.lawyer_id,
        link_code=link.link_code,
        link_name=link.link_name,
        description=link.description,
        is_active=link.is_active,
        click_count=link.click_count,
        consultation_count=link.consultation_count,
        conversion_count=link.conversion_count,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.delete("/{link_id}", summary="律师-删除推广链接")
async def lawyer_delete_promotion_link(
    link_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师删除推广链接"""
    lawyer = await _require_verified_lawyer(db, current_user)

    success = await LawyerPromotionLinkService.delete(db, link_id, int(lawyer.id))

    if not success:
        raise HTTPException(status_code=404, detail="推广链接不存在")

    return {"detail": "推广链接已删除"}


@router.get("/stats/{link_id}",
            response_model=LawyerPromotionLinkStatsResponse,
            summary="律师-推广链接统计")
async def lawyer_get_promotion_stats(
    link_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师获取推广链接统计"""
    lawyer = await _require_verified_lawyer(db, current_user)

    stats = await LawyerPromotionLinkService.get_stats(db, link_id, int(lawyer.id))
    if not stats:
        raise HTTPException(status_code=404, detail="推广链接不存在")

    link_name_value = stats.get("link_name")
    link_name = str(link_name_value) if link_name_value is not None else None

    return LawyerPromotionLinkStatsResponse(
        link_id=int(stats.get("link_id") or 0),
        link_code=str(stats.get("link_code") or ""),
        link_name=link_name,
        click_count=int(stats.get("click_count") or 0),
        consultation_count=int(stats.get("consultation_count") or 0),
        conversion_count=int(stats.get("conversion_count") or 0),
        conversion_rate=float(stats.get("conversion_rate") or 0.0),
    )
