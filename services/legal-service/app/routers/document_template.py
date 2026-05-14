"""文书模板路由"""
import json
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import AsyncSessionLocal
from ..models.document_template import DocumentTemplate
from ..middleware.auth import get_current_lawyer, get_current_user, AuthUser
from ..schemas.response import ApiResponse, PaginatedData

router = APIRouter()


class CreateTemplateRequest(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    content: str
    variables: Optional[str] = None
    price: float = 0.0
    is_public: bool = False


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[str] = None
    price: Optional[float] = None
    is_public: Optional[bool] = None


class GenerateDocumentRequest(BaseModel):
    values: str  # JSON: {"变量名": "值", ...}


@router.get("/")
async def list_templates(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取模板列表"""
    query = select(DocumentTemplate)

    if is_public is not None:
        query = query.where(DocumentTemplate.is_public == is_public)
    if category:
        query = query.where(DocumentTemplate.category == category)

    count_query = select(func.count(DocumentTemplate.id))
    if is_public is not None:
        count_query = count_query.where(DocumentTemplate.is_public == is_public)
    if category:
        count_query = count_query.where(DocumentTemplate.category == category)

    total = await db.scalar(count_query)
    result = await db.execute(
        query.order_by(DocumentTemplate.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    templates = result.scalars().all()

    items = [
        {
            "id": t.id,
            "lawyer_id": t.lawyer_id,
            "name": t.name,
            "category": t.category,
            "description": t.description,
            "price": t.price,
            "is_public": t.is_public,
            "use_count": t.use_count,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in templates
    ]

    return ApiResponse.success({"items": items, "total": total or 0, "page": page, "page_size": page_size})


@router.post("/")
async def create_template(
    body: CreateTemplateRequest,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """创建文书模板"""
    from ..services.lawyer_service import LawyerService
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    template = DocumentTemplate(
        lawyer_id=lawyer.id,
        name=body.name,
        category=body.category,
        description=body.description,
        content=body.content,
        variables=body.variables,
        price=body.price,
        is_public=body.is_public,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return ApiResponse.success({"id": template.id, "name": template.name, "created_at": template.created_at.isoformat()})


@router.get("/{template_id}")
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取模板详情"""
    template = await db.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    return ApiResponse.success({
        "id": template.id,
        "lawyer_id": template.lawyer_id,
        "name": template.name,
        "category": template.category,
        "description": template.description,
        "content": template.content,
        "variables": template.variables,
        "price": template.price,
        "is_public": template.is_public,
        "use_count": template.use_count,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    })


@router.patch("/{template_id}")
async def update_template(
    template_id: int,
    body: UpdateTemplateRequest,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """更新模板"""
    template = await db.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)

    template.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(template)

    return ApiResponse.success({"id": template.id, "name": template.name, "updated_at": template.updated_at.isoformat()})


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """删除模板"""
    template = await db.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    await db.delete(template)
    await db.commit()

    return ApiResponse.success({"id": template_id, "deleted": True})


@router.post("/{template_id}/generate")
async def generate_document(
    template_id: int,
    body: GenerateDocumentRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """根据模板和变量生成文书"""
    template = await db.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    try:
        values = json.loads(body.values)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="values 不是有效的 JSON")

    content = template.content
    for key, val in values.items():
        placeholder = "{{" + key + "}}"
        content = content.replace(placeholder, str(val))

    template.use_count = (template.use_count or 0) + 1
    template.updated_at = datetime.utcnow()
    await db.commit()

    return ApiResponse.success({
        "template_id": template_id,
        "template_name": template.name,
        "content": content,
    })