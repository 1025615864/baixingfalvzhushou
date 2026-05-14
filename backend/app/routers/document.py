from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..utils.deps import get_current_user
from ..models.user import User
from ..services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])
contract_router = APIRouter(prefix="/contracts", tags=["Contracts"])


class GenerateDocumentRequest(BaseModel):
    template_id: int
    fields: dict[str, str]


class ReviewContractRequest(BaseModel):
    contract_text: Optional[str] = None
    file_url: Optional[str] = None
    review_type: Optional[str] = None
    filename: Optional[str] = None
    contract_type: Optional[str] = None


async def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(db)


@router.get("/templates")
async def get_document_templates(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    category: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_templates(page=page, page_size=page_size, category=category, keyword=keyword)


@router.get("/templates/{template_id}")
async def get_document_template_detail(
    template_id: int,
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_template_detail(template_id=template_id)


@router.post("/generate")
async def generate_document(
    request: GenerateDocumentRequest,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    return await service.generate_document(
        user_id=current_user.id,
        template_id=request.template_id,
        fields=request.fields,
    )


@router.get("/categories")
async def get_document_categories(
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_categories()


@contract_router.get("/reviews")
async def get_contract_reviews(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_contract_reviews(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
    )


@contract_router.post("/review")
async def review_contract(
    request: ReviewContractRequest,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    data = {
        "filename": request.filename or request.file_url or "",
        "contract_type": request.contract_type or request.review_type,
        "content_type": None,
        "text_chars": 0,
        "text_preview": request.contract_text or "",
        "focus": request.review_type,
    }
    return await service.submit_contract_review(user_id=current_user.id, data=data)


@contract_router.get("/reviews/{review_id}")
async def get_contract_review_detail(
    review_id: str,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_contract_review_detail(user_id=current_user.id, review_id=review_id)


@contract_router.get("/templates")
async def get_contract_templates(
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_contract_templates()
