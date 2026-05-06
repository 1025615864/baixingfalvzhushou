"""法律文书路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.document_service import DocumentService, TemplateService
from ..middleware.auth import get_current_user, get_current_lawyer, AuthUser
from ..schemas.response import ApiResponse

router = APIRouter()


class CreateDocumentRequest(BaseModel):
    consultation_id: int
    document_type: str
    title: str
    content: Optional[str] = None
    generated_by_ai: bool = False


class UpdateDocumentRequest(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    consultation_id: int
    lawyer_id: Optional[int] = None
    user_id: int
    document_type: str
    title: str
    content: Optional[str] = None
    status: str
    generated_by_ai: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    id: int
    name: str
    category: str
    required_fields: list
    optional_fields: list
    description: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_document(
    body: CreateDocumentRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """创建法律文书"""
    from ..services.consultation_service import ConsultationService
    consultation_service = ConsultationService(db)
    consultation = await consultation_service.get(body.consultation_id)

    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    if consultation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权为此咨询创建文书")

    lawyer_id = None
    if current_user.role == "lawyer":
        from ..services.lawyer_service import LawyerService
        lawyer_service = LawyerService(db)
        lawyer = await lawyer_service.get_by_user_id(current_user.id)
        if lawyer:
            lawyer_id = lawyer.id

    service = DocumentService(db)
    document = await service.create(
        consultation_id=body.consultation_id,
        user_id=current_user.id,
        document_type=body.document_type,
        title=body.title,
        content=body.content,
        lawyer_id=lawyer_id,
        generated_by_ai=body.generated_by_ai,
    )
    return ApiResponse.success(DocumentResponse.model_validate(document))


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取文书详情"""
    service = DocumentService(db)
    document = await service.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.user_id != current_user.id and current_user.role != "admin":
        if document.lawyer_id:
            from ..services.lawyer_service import LawyerService
            lawyer_service = LawyerService(db)
            lawyer = await lawyer_service.get_by_user_id(current_user.id)
            if not lawyer or lawyer.id != document.lawyer_id:
                raise HTTPException(status_code=403, detail="无权查看此文书")

    return ApiResponse.success(DocumentResponse.model_validate(document))


@router.get("/consultation/{consultation_id}")
async def get_consultation_documents(
    consultation_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取咨询的所有文书"""
    service = DocumentService(db)
    documents = await service.get_by_consultation(consultation_id)
    return ApiResponse.success([DocumentResponse.model_validate(d) for d in documents])


@router.patch("/{document_id}")
async def update_document(
    document_id: int,
    body: UpdateDocumentRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """更新文书"""
    service = DocumentService(db)
    document = await service.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.user_id != current_user.id and current_user.role != "admin":
        if document.lawyer_id:
            from ..services.lawyer_service import LawyerService
            lawyer_service = LawyerService(db)
            lawyer = await lawyer_service.get_by_user_id(current_user.id)
            if not lawyer or lawyer.id != document.lawyer_id:
                raise HTTPException(status_code=403, detail="无权修改此文书")

    if body.content:
        document = await service.update_content(document_id, body.content)
    if body.status:
        document = await service.update_status(document_id, body.status)

    return ApiResponse.success(DocumentResponse.model_validate(document))


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """删除文书"""
    service = DocumentService(db)
    document = await service.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除此文书")

    deleted = await service.delete(document_id)
    return ApiResponse.success({"deleted": deleted})


@router.get("/templates/")
async def list_templates(
    category: Optional[str] = None,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取文书模板列表"""
    service = TemplateService(db)
    if category:
        templates = await service.get_by_category(category)
    else:
        templates = await service.list_all()
    return ApiResponse.success([TemplateResponse.model_validate(t) for t in templates])
