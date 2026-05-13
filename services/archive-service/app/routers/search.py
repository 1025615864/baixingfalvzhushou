"""案例多维度检索API"""
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app.models.archive import LegalCase
try:
    from services.common.vector import PGVectorStore, VectorStore, VectorSearchResult
except ImportError:
    class VectorSearchResult:
        def __init__(self, id="", text="", metadata=None, distance=0.0):
            self.id = id
            self.text = text
            self.metadata = metadata or {}
            self.distance = distance

    class VectorStore:
        pass

    class PGVectorStore(VectorStore):
        pass

try:
    from services.common.middleware import check_search_rate_limit
except ImportError:
    def check_search_rate_limit(*args, **kwargs):
        return True, 999

router = APIRouter(prefix="/api/v1/archive", tags=["案例检索"])


class ArchiveSearchRequest(BaseModel):
    q: Optional[str] = None
    court_level: Optional[str] = None
    case_type: Optional[str] = None
    cause_of_action: Optional[str] = None
    category: Optional[str] = None
    is_guiding_case: Optional[bool] = None
    status: Optional[str] = "published"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = 1
    page_size: int = 20


class ArchiveSearchResult(BaseModel):
    id: int
    case_number: Optional[str]
    case_type: str
    title: str
    facts: str
    court: Optional[str]
    court_level: Optional[str]
    judge_date: Optional[str]
    cause_of_action: Optional[str]
    is_guiding_case: bool
    created_at: str


class ArchiveSearchResponse(BaseModel):
    items: list[ArchiveSearchResult]
    total: int
    page: int
    page_size: int


@router.get("/search", response_model=ArchiveSearchResponse)
async def search_archive(
    request: Request,
    q: Optional[str] = Query(None),
    court_level: Optional[str] = None,
    case_type: Optional[str] = None,
    cause_of_action: Optional[str] = None,
    category: Optional[str] = None,
    is_guiding_case: Optional[bool] = None,
    status: Optional[str] = "published",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """多维度检索案例（带限流保护）"""
    client_id = request.client.host if request.client else "unknown"
    is_allowed, remaining = check_search_rate_limit(client_id)

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试",
            headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"}
        )

    query_obj = db.query(LegalCase).filter(
        LegalCase.is_deleted == False,
        LegalCase.is_active == True
    )

    if status:
        query_obj = query_obj.filter(LegalCase.status == status)
    if court_level:
        query_obj = query_obj.filter(LegalCase.court_level == court_level)
    if case_type:
        query_obj = query_obj.filter(LegalCase.case_type == case_type)
    if cause_of_action:
        query_obj = query_obj.filter(LegalCase.cause_of_action == cause_of_action)
    if category:
        query_obj = query_obj.filter(LegalCase.category == category)
    if is_guiding_case is not None:
        query_obj = query_obj.filter(LegalCase.is_guiding_case == is_guiding_case)

    if q:
        search_pattern = f"%{q}%"
        query_obj = query_obj.filter(
            or_(
                LegalCase.title.ilike(search_pattern),
                LegalCase.facts.ilike(search_pattern),
                LegalCase.case_number.ilike(search_pattern),
                LegalCase.keywords.ilike(search_pattern)
            )
        )

    total = query_obj.count()

    query_obj = query_obj.order_by(
        LegalCase.is_guiding_case.desc(),
        LegalCase.weight.desc(),
        LegalCase.created_at.desc()
    )
    query_obj = query_obj.offset((page - 1) * page_size).limit(page_size)

    results = query_obj.all()

    items = []
    for r in results:
        items.append(ArchiveSearchResult(
            id=r.id,
            case_number=r.case_number,
            case_type=r.case_type,
            title=r.title,
            facts=r.facts[:300] + "..." if len(r.facts) > 300 else r.facts,
            court=r.court,
            court_level=r.court_level,
            judge_date=r.judge_date.isoformat() if r.judge_date else None,
            cause_of_action=r.cause_of_action,
            is_guiding_case=r.is_guiding_case,
            created_at=r.created_at.isoformat() if r.created_at else ""
        ))

    return ArchiveSearchResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )
