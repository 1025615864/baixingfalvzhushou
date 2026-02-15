"""法律文书生成API路由（轻量级包装器）

此文件保留路由定义，业务逻辑已迁移至 services/document/ 模块。
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from ..database import get_db
from ..models.user import User
from ..schemas.document import (
    DocumentExportPdfRequest,
    DocumentGenerateRequest,
    DocumentListResponse,
    DocumentResponse,
    DocumentDetail,
    DocumentSaveRequest,
)
from ..utils.deps import get_current_user_optional, get_current_user
from ..utils.rate_limiter import rate_limit, RateLimitConfig

# 导入新服务模块
from ..services.document import (
    document_generation_service,
    document_template_service,
    document_storage_service,
    create_pdf_response,
)

router = APIRouter(prefix="/documents", tags=["文书生成"])


@router.post("/generate", response_model=DocumentResponse)
@rate_limit(*RateLimitConfig.DOCUMENT_GENERATE, by_ip=True, by_user=False)
async def generate_document(
    data: DocumentGenerateRequest,
    request: Request,
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """生成法律文书"""
    if current_user is None:
        await document_generation_service._enforce_guest_document_quota(request)
    else:
        from ..services.quota_service import quota_service

        await quota_service.enforce_document_generate_quota(db, current_user)

    result = await document_generation_service.generate_document_content(
        db,
        document_type=data.document_type,
        plaintiff_name=data.plaintiff_name,
        defendant_name=data.defendant_name,
        case_type=data.case_type,
        facts=data.facts,
        claims=data.claims,
        evidence=data.evidence,
    )

    if current_user is not None:
        try:
            from ..services.quota_service import quota_service

            await quota_service.record_document_generate_usage(db, current_user)
        except Exception:
            logger.exception("Failed to record document generate usage")

    return DocumentResponse(**result)


@router.post("/export/pdf")
@rate_limit(*RateLimitConfig.DOCUMENT_GENERATE, by_ip=True, by_user=False)
async def export_document_pdf(data: DocumentExportPdfRequest):
    """导出文书为PDF"""
    return create_pdf_response(
        title=str(data.title or "").strip(),
        content=str(data.content or ""),
        filename="法律文书",
    )


@router.get("/types")
async def get_document_types(db: Annotated[AsyncSession, Depends(get_db)]):
    """获取支持的文书类型"""
    return await document_template_service.get_document_types(db)


@router.post("/save")
async def save_document(
    data: DocumentSaveRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """保存文书"""
    template_key = str(
        data.template_key or data.document_type or "").strip() or None
    template_version: int | None = None
    if data.template_version is not None:
        try:
            template_version = int(data.template_version)
        except Exception:
            logger.exception("Failed to parse template_version")
            template_version = None

    if template_version is None and template_key:
        try:
            template_version = await document_template_service.get_published_template_version(
                db, template_key=template_key
            )
        except Exception:
            logger.exception("Failed to get published template version")
            template_version = None

    doc_id = await document_storage_service.save_document(
        db,
        user_id=current_user.id,
        document_type=data.document_type,
        title=data.title,
        content=data.content,
        template_key=template_key,
        template_version=template_version,
        payload=data.payload,
    )
    return {"id": doc_id, "message": "保存成功"}


@router.get("/my", response_model=DocumentListResponse)
async def list_my_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
):
    """列出我的文书"""
    result = await document_storage_service.list_user_documents(
        db, user_id=current_user.id, page=page, page_size=page_size
    )
    return result


@router.get("/my/{doc_id}", response_model=DocumentDetail)
async def get_my_document(
    doc_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取我的文书详情"""
    doc = await document_storage_service.get_document(
        db, doc_id=doc_id, user_id=current_user.id
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="文书不存在")

    return DocumentDetail(
        id=int(doc.id),
        user_id=int(doc.user_id),
        document_type=str(doc.document_type),
        title=str(doc.title),
        content=str(doc.content),
        payload_json=doc.payload_json,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("/my/{doc_id}/export")
async def export_my_document(
    doc_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """导出我的文书为PDF"""
    result = await document_storage_service.get_document_for_export(
        db, doc_id=doc_id, user_id=current_user.id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="文书不存在")

    title, content = result
    return create_pdf_response(title=title, content=content, filename=title)


@router.delete("/my/{doc_id}")
async def delete_my_document(
    doc_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """删除我的文书"""
    success = await document_storage_service.delete_document(
        db, doc_id=doc_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="文书不存在")
    return {"message": "删除成功"}
