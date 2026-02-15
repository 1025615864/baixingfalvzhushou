"""
咨询模板管理路由
提供咨询表单模板的CRUD和管理功能
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.knowledge import ConsultationTemplate
from ..models.user import User
from ..utils.deps import require_admin

router = APIRouter(tags=["咨询模板管理"])


class ConsultationQuestion(BaseModel):
    """咨询问题定义"""
    id: str
    type: str = Field(pattern="^(text|textarea|select|radio|checkbox|date|number)$")
    label: str
    placeholder: str | None = None
    required: bool = False
    options: list[str] | None = None


class ConsultationTemplateOut(BaseModel):
    """咨询模板响应"""
    id: int
    key: str
    name: str
    description: str | None
    category: str
    questions: list[ConsultationQuestion]
    status: str
    is_default: bool
    usage_count: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class ConsultationTemplateCreate(BaseModel):
    """创建咨询模板请求"""
    key: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    category: str = Field(default="legal")
    questions: list[ConsultationQuestion]
    is_default: bool = False


class ConsultationTemplateUpdate(BaseModel):
    """更新咨询模板请求"""
    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    category: str | None = None
    questions: list[ConsultationQuestion] | None = None
    is_default: bool | None = None


class PreviewRequest(BaseModel):
    """预览请求"""
    answers: dict[str, str] = Field(default_factory=dict)


class PreviewResponse(BaseModel):
    """预览响应"""
    template_name: str
    questions: list[ConsultationQuestion]
    answers: dict[str, str]


def _parse_questions(questions_json: str | None) -> list[ConsultationQuestion]:
    """解析问题JSON"""
    if not questions_json:
        return []
    try:
        data = json.loads(questions_json)
        if isinstance(data, list):
            return [ConsultationQuestion(**q) for q in data]
    except Exception:
        pass
    return []


def _serialize_questions(questions: list[ConsultationQuestion]) -> str:
    """序列化问题列表"""
    return json.dumps([q.model_dump() for q in questions], ensure_ascii=False)


@router.get("", response_model=list[ConsultationTemplateOut], summary="获取咨询模板列表")
async def list_consultation_templates(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
):
    """获取咨询模板列表（需要管理员权限）"""
    _ = current_user
    
    query = select(ConsultationTemplate)
    
    if category:
        query = query.where(ConsultationTemplate.category == category)
    if status:
        query = query.where(ConsultationTemplate.status == status)
    if keyword:
        kw = f"%{keyword}%"
        query = query.where(
            ConsultationTemplate.name.ilike(kw) | 
            ConsultationTemplate.key.ilike(kw)
        )
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    
    # 分页
    query = query.order_by(ConsultationTemplate.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [
        ConsultationTemplateOut(
            id=int(t.id),
            key=str(t.key),
            name=str(t.name),
            description=t.description,
            category=str(t.category),
            questions=_parse_questions(t.questions),
            status=str(t.status),
            is_default=bool(t.is_default),
            usage_count=int(t.usage_count or 0),
            created_by=str(t.created_by),
            created_at=t.created_at,
            updated_at=t.updated_at,
            published_at=t.published_at,
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=ConsultationTemplateOut, summary="获取咨询模板详情")
async def get_consultation_template(
    template_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取咨询模板详情（需要管理员权限）"""
    _ = current_user
    
    result = await db.execute(
        select(ConsultationTemplate).where(ConsultationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return ConsultationTemplateOut(
        id=int(template.id),
        key=str(template.key),
        name=str(template.name),
        description=template.description,
        category=str(template.category),
        questions=_parse_questions(template.questions),
        status=str(template.status),
        is_default=bool(template.is_default),
        usage_count=int(template.usage_count or 0),
        created_by=str(template.created_by),
        created_at=template.created_at,
        updated_at=template.updated_at,
        published_at=template.published_at,
    )


@router.post("", response_model=ConsultationTemplateOut, summary="创建咨询模板")
async def create_consultation_template(
    data: ConsultationTemplateCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """创建咨询模板（需要管理员权限）"""
    
    # 检查key是否已存在
    existing = await db.execute(
        select(ConsultationTemplate).where(ConsultationTemplate.key == data.key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="模板key已存在")
    
    # 如果设为默认，取消其他默认模板
    if data.is_default:
        await db.execute(
            select(ConsultationTemplate)
            .where(ConsultationTemplate.is_default == True)
        )
        default_templates = await db.execute(
            select(ConsultationTemplate).where(ConsultationTemplate.is_default == True)
        )
        for dt in default_templates.scalars().all():
            dt.is_default = False
    
    template = ConsultationTemplate(
        key=data.key,
        name=data.name,
        description=data.description,
        category=data.category,
        questions=_serialize_questions(data.questions),
        status="draft",
        is_default=data.is_default,
        usage_count=0,
        created_by=str(current_user.username),
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return ConsultationTemplateOut(
        id=int(template.id),
        key=str(template.key),
        name=str(template.name),
        description=template.description,
        category=str(template.category),
        questions=data.questions,
        status=str(template.status),
        is_default=bool(template.is_default),
        usage_count=0,
        created_by=str(template.created_by),
        created_at=template.created_at,
        updated_at=template.updated_at,
        published_at=None,
    )


@router.put("/{template_id}", response_model=ConsultationTemplateOut, summary="更新咨询模板")
async def update_consultation_template(
    template_id: int,
    data: ConsultationTemplateUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """更新咨询模板（需要管理员权限）"""
    _ = current_user
    
    result = await db.execute(
        select(ConsultationTemplate).where(ConsultationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 更新字段
    if data.name is not None:
        template.name = data.name
    if data.description is not None:
        template.description = data.description
    if data.category is not None:
        template.category = data.category
    if data.questions is not None:
        template.questions = _serialize_questions(data.questions)
    if data.is_default is not None:
        # 如果设为默认，取消其他默认模板
        if data.is_default:
            default_templates = await db.execute(
                select(ConsultationTemplate).where(ConsultationTemplate.is_default == True)
            )
            for dt in default_templates.scalars().all():
                dt.is_default = False
        template.is_default = data.is_default
    
    await db.commit()
    await db.refresh(template)
    
    return ConsultationTemplateOut(
        id=int(template.id),
        key=str(template.key),
        name=str(template.name),
        description=template.description,
        category=str(template.category),
        questions=_parse_questions(template.questions),
        status=str(template.status),
        is_default=bool(template.is_default),
        usage_count=int(template.usage_count or 0),
        created_by=str(template.created_by),
        created_at=template.created_at,
        updated_at=template.updated_at,
        published_at=template.published_at,
    )


@router.delete("/{template_id}", summary="删除咨询模板")
async def delete_consultation_template(
    template_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """删除咨询模板（需要管理员权限）"""
    _ = current_user
    
    result = await db.execute(
        select(ConsultationTemplate).where(ConsultationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    await db.delete(template)
    await db.commit()
    
    return {"message": "模板已删除", "template_id": template_id}


@router.post("/{template_id}/publish", response_model=ConsultationTemplateOut, summary="发布咨询模板")
async def publish_consultation_template(
    template_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """发布咨询模板（需要管理员权限）"""
    _ = current_user
    
    result = await db.execute(
        select(ConsultationTemplate).where(ConsultationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    template.status = "published"
    template.published_at = datetime.now()
    
    await db.commit()
    await db.refresh(template)
    
    return ConsultationTemplateOut(
        id=int(template.id),
        key=str(template.key),
        name=str(template.name),
        description=template.description,
        category=str(template.category),
        questions=_parse_questions(template.questions),
        status=str(template.status),
        is_default=bool(template.is_default),
        usage_count=int(template.usage_count or 0),
        created_by=str(template.created_by),
        created_at=template.created_at,
        updated_at=template.updated_at,
        published_at=template.published_at,
    )


@router.post("/{template_id}/preview", response_model=PreviewResponse, summary="预览咨询模板")
async def preview_consultation_template(
    template_id: int,
    data: PreviewRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """预览咨询模板表单效果（需要管理员权限）"""
    _ = current_user
    
    result = await db.execute(
        select(ConsultationTemplate).where(ConsultationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    questions = _parse_questions(template.questions)
    
    return PreviewResponse(
        template_name=str(template.name),
        questions=questions,
        answers=data.answers,
    )
