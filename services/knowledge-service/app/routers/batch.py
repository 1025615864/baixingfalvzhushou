"""批量导入导出 API"""
from typing import Optional, List, Dict
from datetime import datetime

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.knowledge import LegalKnowledge
from app.services.knowledge_service import KnowledgeService
from app.routers.knowledge import KnowledgeCreateRequest
from services.common.middleware import check_batch_rate_limit

router = APIRouter(prefix="/api/v1/knowledge", tags=["批量操作"])

MAX_BATCH_SIZE = 500


class BatchImportRequest(BaseModel):
    items: List[KnowledgeCreateRequest]
    skip_duplicates: bool = True


class BatchImportError(BaseModel):
    index: int
    error: str


class BatchImportResponse(BaseModel):
    total: int
    successful: int
    failed: int
    errors: List[BatchImportError]


class ExportQueryParams(Query):
    category: Optional[str] = None
    knowledge_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 100


class ExportResponse(BaseModel):
    items: List[Dict]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.post("/batch-import", response_model=BatchImportResponse, status_code=status.HTTP_201_CREATED)
async def batch_import(
    request: BatchImportRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """批量导入知识"""
    client_id = http_request.client.host if http_request.client else "unknown"
    is_allowed, remaining = check_batch_rate_limit(client_id)
    if not is_allowed:
        raise HTTPException(status_code=429, detail="批量操作限流，请稍后再试")

    if not request.items:
        raise HTTPException(status_code=400, detail="导入数据不能为空")

    if len(request.items) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"单次导入最多 {MAX_BATCH_SIZE} 条数据"
        )

    service = KnowledgeService(db)
    errors: List[BatchImportError] = []
    successful = 0

    for index, item in enumerate(request.items):
        try:
            existing = db.query(LegalKnowledge).filter(
                LegalKnowledge.title == item.title,
                LegalKnowledge.knowledge_type == item.knowledge_type,
                LegalKnowledge.is_deleted == False
            ).first()

            if existing:
                if request.skip_duplicates:
                    successful += 1
                    continue
                else:
                    errors.append(BatchImportError(
                        index=index,
                        error=f"重复数据: 标题 '{item.title}' 已存在"
                    ))
                    continue

            service.create_knowledge(item)
            successful += 1

        except Exception as e:
            db.rollback()
            errors.append(BatchImportError(
                index=index,
                error=str(e)
            ))

    if errors and errors:
        db.rollback()
        return BatchImportResponse(
            total=len(request.items),
            successful=0,
            failed=len(errors),
            errors=errors
        )

    db.commit()
    return BatchImportResponse(
        total=len(request.items),
        successful=successful,
        failed=len(errors),
        errors=errors
    )


@router.get("/export", response_model=ExportResponse)
async def export_knowledge(
    category: Optional[str] = None,
    knowledge_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db)
):
    """导出知识"""
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > MAX_BATCH_SIZE:
        page_size = MAX_BATCH_SIZE

    query = db.query(LegalKnowledge).filter(LegalKnowledge.is_deleted == False)

    if category:
        query = query.filter(LegalKnowledge.category == category)
    if knowledge_type:
        query = query.filter(LegalKnowledge.knowledge_type == knowledge_type)
    if status:
        query = query.filter(LegalKnowledge.status == status)
    if start_date:
        query = query.filter(LegalKnowledge.created_at >= start_date)
    if end_date:
        query = query.filter(LegalKnowledge.created_at <= end_date)

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    offset = (page - 1) * page_size
    items = query.order_by(LegalKnowledge.created_at.desc()).offset(offset).limit(page_size).all()

    result: List[Dict] = []
    for item in items:
        result.append({
            "id": item.id,
            "knowledge_type": item.knowledge_type,
            "title": item.title,
            "article_number": item.article_number,
            "content": item.content,
            "summary": item.summary,
            "category": item.category,
            "keywords": item.keywords,
            "source": item.source,
            "status": item.status,
            "version": item.version,
            "effective_date": item.effective_date.isoformat() if item.effective_date else None,
            "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
            "law_number": item.law_number,
            "jurisdiction": item.jurisdiction,
            "weight": item.weight,
            "is_active": item.is_active,
            "is_vectorized": item.is_vectorized,
            "created_by": item.created_by,
            "updated_by": item.updated_by,
            "reviewed_by": item.reviewed_by,
            "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "metadata": item.metadata,
        })

    return ExportResponse(
        items=result,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )