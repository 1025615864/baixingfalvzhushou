"""文书领域路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...schemas import DocumentResponse, DocumentCreate
from ...services import DocumentService, TemplateService
from ...middleware.auth import require_permissions
from ...shared.permissions import Permission

router = APIRouter(prefix="/documents", tags=["文书"])


@router.post("/", response_model=DocumentResponse)
async def create_document(
    request: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.DOCUMENT_CREATE)),
):
    service = DocumentService(db)
    document = await service.create(
        consultation_id=request.consultation_id,
        user_id=current_user.id,
        document_type=request.document_type,
        title=request.title,
        lawyer_id=request.lawyer_id,
        content=request.content,
        generated_by_ai=request.generated_by_ai,
    )
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.DOCUMENT_READ)),
):
    service = DocumentService(db)
    document = await service.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    return DocumentResponse.model_validate(document)


@router.get("/consultation/{consultation_id}")
async def get_consultation_documents(
    consultation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.DOCUMENT_READ)),
):
    service = DocumentService(db)
    documents = await service.get_by_consultation(consultation_id)
    return [DocumentResponse.model_validate(d) for d in documents]


@router.patch("/{document_id}/content")
async def update_document_content(
    document_id: int,
    content: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.DOCUMENT_UPDATE)),
):
    service = DocumentService(db)
    document = await service.update_content(document_id, content)
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    return {"message": "内容已更新"}


@router.patch("/{document_id}/status")
async def update_document_status(
    document_id: int,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.DOCUMENT_UPDATE)),
):
    service = DocumentService(db)
    document = await service.update_status(document_id, status)
    if not document:
        raise HTTPException(status_code=404, detail="文书不存在")
    return {"message": "状态已更新"}