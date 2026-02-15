from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.document_template import DocumentTemplate, DocumentTemplateVersion
from ..models.user import User
from ..utils.deps import require_admin

router = APIRouter(tags=["文书模板管理"])


class TemplateVariable(BaseModel):
    """模板变量定义"""
    name: str = Field(..., min_length=1, max_length=50)
    type: str = Field(default="text", pattern="^(text|number|date|select|textarea)$")
    label: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=200)
    required: bool = Field(default=False)
    options: list[str] | None = Field(default=None)
    default_value: str | None = Field(default=None, max_length=500)


class DocumentTemplateOut(BaseModel):
    id: int
    key: str
    title: str
    description: str | None
    is_active: bool
    published_version: int | None = None
    created_at: datetime
    updated_at: datetime


class DocumentTemplateCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class DocumentTemplateUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class DocumentTemplateVersionOut(BaseModel):
    id: int
    template_id: int
    version: int
    is_published: bool
    content: str
    variables: list[TemplateVariable] | None = None
    usage_count: int = 0
    created_at: datetime


class DocumentTemplateVersionCreate(BaseModel):
    content: str = Field(..., min_length=1)
    publish: bool = False
    variables: list[TemplateVariable] | None = Field(default=None)


class DocumentTemplateVersionUpdate(BaseModel):
    """更新模板版本"""
    content: str | None = Field(default=None, min_length=1)
    variables: list[TemplateVariable] | None = Field(default=None)


class PreviewRequest(BaseModel):
    """预览请求"""
    variables: dict[str, str] = Field(default_factory=dict)


class PreviewResponse(BaseModel):
    """预览响应"""
    content: str
    rendered_content: str


@router.get("", response_model=list[DocumentTemplateOut])
async def list_document_templates(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user

    res = await db.execute(select(DocumentTemplate).order_by(DocumentTemplate.id.asc()))
    templates = res.scalars().all()

    out: list[DocumentTemplateOut] = []
    for t in templates:
        template_id = int(t.id)
        pub_res = await db.execute(
            select(func.max(DocumentTemplateVersion.version)).where(
                DocumentTemplateVersion.template_id == template_id,
                DocumentTemplateVersion.is_published.is_(True),
            )
        )
        published_version = pub_res.scalar_one_or_none()
        out.append(
            DocumentTemplateOut(
                id=template_id,
                key=str(t.key),
                title=str(t.title),
                description=t.description,
                is_active=bool(t.is_active),
                published_version=int(
                    published_version) if published_version is not None else None,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
        )

    return out


@router.post("", response_model=DocumentTemplateOut)
async def create_document_template(
    data: DocumentTemplateCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user

    key = str(data.key or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="key 不能为空")

    exists_res = await db.execute(select(DocumentTemplate).where(DocumentTemplate.key == key))
    if exists_res.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="key 已存在")

    row = DocumentTemplate(
        key=key,
        title=str(data.title or "").strip() or key,
        description=str(data.description).strip(
        ) if data.description is not None else None,
        is_active=bool(data.is_active),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    return DocumentTemplateOut(
        id=int(row.id),
        key=str(row.key),
        title=str(row.title),
        description=row.description,
        is_active=bool(row.is_active),
        published_version=None,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.put("/{template_id}", response_model=DocumentTemplateOut)
async def update_document_template(
    template_id: int,
    data: DocumentTemplateUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user

    res = await db.execute(select(DocumentTemplate).where(DocumentTemplate.id == int(template_id)))
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="模板不存在")

    if data.title is not None:
        row.title = str(data.title or "").strip() or str(getattr(row, "key"))
    if data.description is not None:
        row.description = str(
            data.description).strip() if data.description else None
    if data.is_active is not None:
        row.is_active = bool(data.is_active)

    db.add(row)
    await db.commit()
    await db.refresh(row)

    template_id = int(row.id)
    pub_res = await db.execute(
        select(func.max(DocumentTemplateVersion.version)).where(
            DocumentTemplateVersion.template_id == template_id,
            DocumentTemplateVersion.is_published.is_(True),
        )
    )
    published_version = pub_res.scalar_one_or_none()

    return DocumentTemplateOut(
        id=template_id,
        key=str(row.key),
        title=str(row.title),
        description=row.description,
        is_active=bool(row.is_active),
        published_version=int(
            published_version) if published_version is not None else None,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _parse_variables(variables_json: str | None) -> list[TemplateVariable] | None:
    """解析变量JSON"""
    if not variables_json:
        return None
    try:
        data = json.loads(variables_json)
        if isinstance(data, list):
            return [TemplateVariable(**v) for v in data]
    except Exception:
        pass
    return None


@router.get("/{template_id}/versions",
            response_model=list[DocumentTemplateVersionOut])
async def list_document_template_versions(
    template_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user

    res = await db.execute(select(DocumentTemplate).where(DocumentTemplate.id == int(template_id)))
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="模板不存在")

    q = (
        select(DocumentTemplateVersion) .where(
            DocumentTemplateVersion.template_id == int(template_id)) .order_by(
            DocumentTemplateVersion.version.desc(),
            DocumentTemplateVersion.id.desc()))
    versions_res = await db.execute(q)
    versions = versions_res.scalars().all()

    return [
        DocumentTemplateVersionOut(
            id=int(v.id),
            template_id=int(v.template_id),
            version=int(v.version),
            is_published=bool(v.is_published),
            content=str(v.content),
            variables=_parse_variables(v.variables),
            usage_count=int(v.usage_count or 0),
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.post("/{template_id}/versions",
             response_model=DocumentTemplateVersionOut)
async def create_document_template_version(
    template_id: int,
    data: DocumentTemplateVersionCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user

    tpl_res = await db.execute(select(DocumentTemplate).where(DocumentTemplate.id == int(template_id)))
    tpl = tpl_res.scalar_one_or_none()
    if tpl is None:
        raise HTTPException(status_code=404, detail="模板不存在")

    max_res = await db.execute(
        select(func.max(DocumentTemplateVersion.version)).where(
            DocumentTemplateVersion.template_id == int(template_id))
    )
    max_version = max_res.scalar_one_or_none()
    next_version = int(max_version or 0) + 1

    # 序列化变量
    variables_json = None
    if data.variables:
        variables_json = json.dumps([v.model_dump() for v in data.variables], ensure_ascii=False)

    row = DocumentTemplateVersion(
        template_id=int(template_id),
        version=int(next_version),
        content=str(data.content or "").strip(),
        is_published=bool(data.publish),
        variables=variables_json,
    )
    if not row.content:
        raise HTTPException(status_code=400, detail="content 不能为空")

    if bool(data.publish):
        existing_res = await db.execute(
            select(DocumentTemplateVersion).where(
                DocumentTemplateVersion.template_id == int(template_id))
        )
        for v in existing_res.scalars().all():
            if bool(v.is_published):
                v.is_published = False
                db.add(v)

    db.add(row)
    await db.commit()
    await db.refresh(row)

    return DocumentTemplateVersionOut(
        id=int(row.id),
        template_id=int(row.template_id),
        version=int(row.version),
        is_published=bool(row.is_published),
        content=str(row.content),
        variables=data.variables,
        usage_count=0,
        created_at=row.created_at,
    )


@router.put("/{template_id}/versions/{version_id}",
            response_model=DocumentTemplateVersionOut)
async def update_document_template_version(
    template_id: int,
    version_id: int,
    data: DocumentTemplateVersionUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """更新模板版本内容"""
    _ = current_user

    res = await db.execute(
        select(DocumentTemplateVersion).where(
            DocumentTemplateVersion.id == int(version_id),
            DocumentTemplateVersion.template_id == int(template_id),
        )
    )
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="版本不存在")

    if data.content is not None:
        row.content = str(data.content).strip()
    
    if data.variables is not None:
        row.variables = json.dumps([v.model_dump() for v in data.variables], ensure_ascii=False)

    db.add(row)
    await db.commit()
    await db.refresh(row)

    return DocumentTemplateVersionOut(
        id=int(row.id),
        template_id=int(row.template_id),
        version=int(row.version),
        is_published=bool(row.is_published),
        content=str(row.content),
        variables=_parse_variables(row.variables),
        usage_count=int(row.usage_count or 0),
        created_at=row.created_at,
    )


@router.post("/{template_id}/versions/{version_id}/publish",
             response_model=DocumentTemplateVersionOut)
async def publish_document_template_version(
    template_id: int,
    version_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _ = current_user

    tpl_res = await db.execute(select(DocumentTemplate).where(DocumentTemplate.id == int(template_id)))
    tpl = tpl_res.scalar_one_or_none()
    if tpl is None:
        raise HTTPException(status_code=404, detail="模板不存在")

    ver_res = await db.execute(
        select(DocumentTemplateVersion).where(
            DocumentTemplateVersion.id == int(version_id),
            DocumentTemplateVersion.template_id == int(template_id),
        )
    )
    row = ver_res.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="版本不存在")

    existing_res = await db.execute(
        select(DocumentTemplateVersion).where(
            DocumentTemplateVersion.template_id == int(template_id))
    )
    for v in existing_res.scalars().all():
        if int(v.id) == int(row.id):
            continue
        if bool(v.is_published):
            v.is_published = False
            db.add(v)

    row.is_published = True
    db.add(row)
    await db.commit()
    await db.refresh(row)

    return DocumentTemplateVersionOut(
        id=int(row.id),
        template_id=int(row.template_id),
        version=int(row.version),
        is_published=bool(row.is_published),
        content=str(row.content),
        variables=_parse_variables(row.variables),
        usage_count=int(row.usage_count or 0),
        created_at=row.created_at,
    )


@router.post("/{template_id}/versions/{version_id}/preview",
             response_model=PreviewResponse)
async def preview_document_template(
    template_id: int,
    version_id: int,
    data: PreviewRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """预览模板渲染效果"""
    _ = current_user

    res = await db.execute(
        select(DocumentTemplateVersion).where(
            DocumentTemplateVersion.id == int(version_id),
            DocumentTemplateVersion.template_id == int(template_id),
        )
    )
    version = res.scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=404, detail="版本不存在")

    content = str(version.content)
    
    # 使用正则表达式替换变量 {{variable_name}}
    def replace_variable(match: re.Match) -> str:
        var_name = match.group(1).strip()
        return data.variables.get(var_name, f"[{var_name}]")
    
    rendered_content = re.sub(r'\{\{(\w+)\}\}', replace_variable, content)
    
    return PreviewResponse(
        content=content,
        rendered_content=rendered_content,
    )
