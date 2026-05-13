"""知识库全文搜索API"""
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app.models.knowledge import LegalKnowledge
try:
    from services.common.middleware.rate_limit import check_search_rate_limit
except ImportError:
    def check_search_rate_limit(*args, **kwargs):
        return True, 999

router = APIRouter(prefix="/api/v1/knowledge", tags=["知识搜索"])


class KnowledgeSearchRequest(BaseModel):
    q: str = Query(..., min_length=1, description="搜索关键词")
    category: Optional[str] = None
    knowledge_type: Optional[str] = None
    status: Optional[str] = "published"
    page: int = 1
    page_size: int = 20


class KnowledgeSearchResult(BaseModel):
    id: int
    title: str
    content: str
    summary: Optional[str]
    category: Optional[str]
    keywords: Optional[str]
    source: Optional[str]
    created_at: str


class KnowledgeSearchResponse(BaseModel):
    items: list[KnowledgeSearchResult]
    total: int
    page: int
    page_size: int
    query: str


@router.get("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    request: Request,
    q: str = Query(..., min_length=1),
    category: Optional[str] = None,
    knowledge_type: Optional[str] = None,
    status: Optional[str] = "published",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """全文搜索知识（带限流保护）"""
    client_id = request.client.host if request.client else "unknown"
    is_allowed, remaining = check_search_rate_limit(client_id)

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试",
            headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"}
        )

    query_obj = db.query(LegalKnowledge).filter(
        LegalKnowledge.is_deleted == False,
        LegalKnowledge.is_active == True
    )

    if status:
        query_obj = query_obj.filter(LegalKnowledge.status == status)
    if category:
        query_obj = query_obj.filter(LegalKnowledge.category == category)
    if knowledge_type:
        query_obj = query_obj.filter(LegalKnowledge.knowledge_type == knowledge_type)

    search_pattern = f"%{q}%"
    query_obj = query_obj.filter(
        or_(
            LegalKnowledge.title.ilike(search_pattern),
            LegalKnowledge.content.ilike(search_pattern),
            LegalKnowledge.summary.ilike(search_pattern),
            LegalKnowledge.keywords.ilike(search_pattern),
            LegalKnowledge.article_number.ilike(search_pattern)
        )
    )

    total = query_obj.count()

    query_obj = query_obj.order_by(LegalKnowledge.weight.desc(), LegalKnowledge.created_at.desc())
    query_obj = query_obj.offset((page - 1) * page_size).limit(page_size)

    results = query_obj.all()

    items = []
    for r in results:
        items.append(KnowledgeSearchResult(
            id=r.id,
            title=r.title,
            content=r.content[:500] + "..." if len(r.content) > 500 else r.content,
            summary=r.summary,
            category=r.category,
            keywords=r.keywords,
            source=r.source,
            created_at=r.created_at.isoformat() if r.created_at else ""
        ))

    return KnowledgeSearchResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        query=q
    )
