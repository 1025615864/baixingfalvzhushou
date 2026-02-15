"""快捷回复模板路由"""

from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...schemas.lawfirm import (
    LawyerReplyTemplateCreate, LawyerReplyTemplateUpdate,
    LawyerReplyTemplateResponse, LawyerReplyTemplateListResponse,
)
from ...services.lawyer_reply_template_service import LawyerReplyTemplateService
from ...utils.deps import get_current_user

router = APIRouter(prefix="/lawyer/reply-templates", tags=["快捷回复模板"])


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
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="未绑定律师资料")
    return lawyer


@router.get("", response_model=LawyerReplyTemplateListResponse,
            summary="获取快捷回复模板列表")
async def lawyer_get_reply_templates(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = None,
    is_active: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """律师获取自己的快捷回复模板列表"""
    lawyer = await _require_verified_lawyer(db, current_user)

    templates, total = await LawyerReplyTemplateService.get_list(
        db,
        int(lawyer.id),
        category=category,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

    items = []
    for t in templates:
        items.append(LawyerReplyTemplateResponse(
            id=t.id,
            lawyer_id=t.lawyer_id,
            title=t.title,
            content=t.content,
            category=t.category,
            is_active=t.is_active,
            use_count=t.use_count,
            created_at=t.created_at,
            updated_at=t.updated_at,
        ))

    return LawyerReplyTemplateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/categories", summary="获取模板分类列表")
async def lawyer_get_reply_template_categories(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师获取自己的快捷回复模板分类列表"""
    lawyer = await _require_verified_lawyer(db, current_user)

    categories = await LawyerReplyTemplateService.get_categories(db, int(lawyer.id))

    return {"categories": categories}


@router.post("", response_model=LawyerReplyTemplateResponse,
             summary="创建快捷回复模板")
async def lawyer_create_reply_template(
    data: LawyerReplyTemplateCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师创建快捷回复模板"""
    lawyer = await _require_verified_lawyer(db, current_user)

    template = await LawyerReplyTemplateService.create(
        db,
        int(lawyer.id),
        title=data.title,
        content=data.content,
        category=data.category,
        is_active=True,
    )

    return LawyerReplyTemplateResponse(
        id=template.id,
        lawyer_id=template.lawyer_id,
        title=template.title,
        content=template.content,
        category=template.category,
        is_active=template.is_active,
        use_count=template.use_count,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("/{template_id}",
            response_model=LawyerReplyTemplateResponse, summary="获取快捷回复模板详情")
async def lawyer_get_reply_template(
    template_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师获取快捷回复模板详情"""
    lawyer = await _require_verified_lawyer(db, current_user)

    template = await LawyerReplyTemplateService.get_by_id(db, template_id, int(lawyer.id))

    if not template:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="模板不存在")

    return LawyerReplyTemplateResponse(
        id=template.id,
        lawyer_id=template.lawyer_id,
        title=template.title,
        content=template.content,
        category=template.category,
        is_active=template.is_active,
        use_count=template.use_count,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.put("/{template_id}",
            response_model=LawyerReplyTemplateResponse, summary="更新快捷回复模板")
async def lawyer_update_reply_template(
    template_id: int,
    data: LawyerReplyTemplateUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师更新快捷回复模板"""
    lawyer = await _require_verified_lawyer(db, current_user)

    template = await LawyerReplyTemplateService.update(
        db, template_id, int(lawyer.id),
        title=data.title,
        content=data.content,
        category=data.category,
        is_active=data.is_active,
    )

    if not template:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="模板不存在")

    return LawyerReplyTemplateResponse(
        id=template.id,
        lawyer_id=template.lawyer_id,
        title=template.title,
        content=template.content,
        category=template.category,
        is_active=template.is_active,
        use_count=template.use_count,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.delete("/{template_id}", summary="删除快捷回复模板")
async def lawyer_delete_reply_template(
    template_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师删除快捷回复模板"""
    lawyer = await _require_verified_lawyer(db, current_user)

    success = await LawyerReplyTemplateService.delete(db, template_id, int(lawyer.id))

    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="模板不存在")

    return {"detail": "模板已删除"}


@router.post("/{template_id}/use", summary="使用快捷回复模板")
async def lawyer_use_reply_template(
    template_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师使用快捷回复模板"""
    lawyer = await _require_verified_lawyer(db, current_user)

    template = await LawyerReplyTemplateService.get_by_id(db, template_id, int(lawyer.id))
    if not template:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="模板不存在")

    await LawyerReplyTemplateService.increment_use_count(db, template_id, int(lawyer.id))

    return {"content": template.content}
