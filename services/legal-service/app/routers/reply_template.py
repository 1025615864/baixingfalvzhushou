from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.database import get_db
from app.models.lawyer_profile import LawyerReplyTemplate

router = APIRouter()


@router.get("/lawyers/{lawyer_id}/reply-templates")
async def get_reply_templates(
    lawyer_id: int,
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(LawyerReplyTemplate).where(LawyerReplyTemplate.lawyer_id == lawyer_id)
    if category:
        stmt = stmt.where(LawyerReplyTemplate.category == category)
    if is_active is not None:
        stmt = stmt.where(LawyerReplyTemplate.is_active == is_active)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/lawyers/{lawyer_id}/reply-templates")
async def create_reply_template(
    lawyer_id: int,
    title: str = "",
    content: str = "",
    category: str = "general",
    db: AsyncSession = Depends(get_db),
):
    template = LawyerReplyTemplate(
        lawyer_id=lawyer_id,
        title=title,
        content=content,
        category=category,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.put("/lawyers/{lawyer_id}/reply-templates/{template_id}")
async def update_reply_template(
    lawyer_id: int,
    template_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LawyerReplyTemplate).where(
            LawyerReplyTemplate.id == template_id,
            LawyerReplyTemplate.lawyer_id == lawyer_id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="回复模板不存在")
    if title is not None:
        template.title = title
    if content is not None:
        template.content = content
    if category is not None:
        template.category = category
    if is_active is not None:
        template.is_active = is_active
    await db.commit()
    return template


@router.delete("/lawyers/{lawyer_id}/reply-templates/{template_id}")
async def delete_reply_template(lawyer_id: int, template_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LawyerReplyTemplate).where(
            LawyerReplyTemplate.id == template_id,
            LawyerReplyTemplate.lawyer_id == lawyer_id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="回复模板不存在")
    await db.delete(template)
    await db.commit()
    return {"message": "删除成功"}