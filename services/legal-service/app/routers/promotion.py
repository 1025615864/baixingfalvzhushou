from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.database import get_db
from app.models.lawyer_profile import LawyerPromotionLink

router = APIRouter()


@router.get("/lawyers/{lawyer_id}/promotion-links")
async def get_promotion_links(lawyer_id: int, is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = select(LawyerPromotionLink).where(LawyerPromotionLink.lawyer_id == lawyer_id)
    if is_active is not None:
        stmt = stmt.where(LawyerPromotionLink.is_active == is_active)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/lawyers/{lawyer_id}/promotion-links")
async def create_promotion_link(lawyer_id: int, link_name: str = "", description: str = "", db: AsyncSession = Depends(get_db)):
    link_code = f"PL{lawyer_id}{hash(link_name) % 100000:05d}"
    link = LawyerPromotionLink(
        lawyer_id=lawyer_id,
        link_code=link_code,
        link_name=link_name,
        description=description,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


@router.put("/lawyers/{lawyer_id}/promotion-links/{link_id}")
async def update_promotion_link(lawyer_id: int, link_id: int, is_active: Optional[bool] = None, link_name: Optional[str] = None, description: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LawyerPromotionLink).where(
            LawyerPromotionLink.id == link_id,
            LawyerPromotionLink.lawyer_id == lawyer_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="推广链接不存在")
    if is_active is not None:
        link.is_active = is_active
    if link_name is not None:
        link.link_name = link_name
    if description is not None:
        link.description = description
    await db.commit()
    return link


@router.post("/lawyers/{lawyer_id}/promotion-links/{link_id}/track")
async def track_promotion_click(lawyer_id: int, link_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LawyerPromotionLink).where(
            LawyerPromotionLink.id == link_id,
            LawyerPromotionLink.lawyer_id == lawyer_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="推广链接不存在")
    link.click_count = (link.click_count or 0) + 1
    await db.commit()
    return {"click_count": link.click_count}