"""案例推荐API"""
from typing import Optional, List, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.archive import LegalCase
from app.services.case_recommendation import CaseRecommendationService

router = APIRouter(prefix="/api/v1/archive", tags=["案例推荐"])


class CaseResponse(BaseModel):
    id: int
    case_number: Optional[str]
    case_type: str
    title: str
    facts: str
    legal_basis: Optional[str]
    judgment: Optional[str]
    result: Optional[str]
    court: Optional[str]
    court_level: Optional[str]
    judge_date: Optional[str]
    cause_of_action: Optional[str]
    judgment_result: Optional[str]
    keywords: Optional[str]
    is_guiding_case: bool
    created_at: str

    class Config:
        from_attributes = True


class RelatedCaseResponse(BaseModel):
    case: CaseResponse
    related_cases: List[CaseResponse]
    total_count: int
    similarity_scores: Dict[int, float]


class SimilarCaseResponse(BaseModel):
    cases: List[CaseResponse]
    total_count: int


class SameCourtResponse(BaseModel):
    cases: List[CaseResponse]
    total_count: int


class GuidingCaseResponse(BaseModel):
    cases: List[CaseResponse]
    total: int
    page: int
    page_size: int


class RecommendationQuery(BaseModel):
    max_results: int = 5
    include_same_cause: bool = True
    include_same_court: bool = True
    include_guiding: bool = False


def _case_to_response(case: LegalCase) -> CaseResponse:
    return CaseResponse(
        id=case.id,
        case_number=case.case_number,
        case_type=case.case_type,
        title=case.title,
        facts=case.facts[:500] + "..." if len(case.facts) > 500 else case.facts,
        legal_basis=case.legal_basis,
        judgment=case.judgment,
        result=case.result,
        court=case.court,
        court_level=case.court_level,
        judge_date=case.judge_date.isoformat() if case.judge_date else None,
        cause_of_action=case.cause_of_action,
        judgment_result=case.judgment_result,
        keywords=case.keywords,
        is_guiding_case=case.is_guiding_case,
        created_at=case.created_at.isoformat() if case.created_at else ""
    )


@router.get("/{case_id}/related", response_model=RelatedCaseResponse)
async def get_related_cases(
    case_id: int,
    max_results: int = Query(5, ge=1, le=20),
    include_same_cause: bool = Query(True),
    include_same_court: bool = Query(True),
    db: Session = Depends(get_db)
):
    """获取相关案例"""
    service = CaseRecommendationService(db)
    source_case = db.query(LegalCase).filter(
        LegalCase.id == case_id,
        LegalCase.is_deleted == False,
        LegalCase.is_active == True
    ).first()

    if not source_case:
        return RelatedCaseResponse(
            case=_case_to_response(source_case) if source_case else None,
            related_cases=[],
            total_count=0,
            similarity_scores={}
        )

    related_cases, similarity_scores = service.get_related_cases(
        case_id=case_id,
        max_results=max_results,
        include_same_cause=include_same_cause,
        include_same_court=include_same_court
    )

    return RelatedCaseResponse(
        case=_case_to_response(source_case),
        related_cases=[_case_to_response(c) for c in related_cases],
        total_count=len(related_cases),
        similarity_scores={k: float(v) for k, v in similarity_scores.items()}
    )


@router.get("/{case_id}/similar", response_model=SimilarCaseResponse)
async def get_similar_by_case_number(
    case_id: int,
    max_results: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """基于案号相似性获取相似案例"""
    service = CaseRecommendationService(db)
    similar_cases = service.get_similar_by_case_number(case_id, max_results)

    return SimilarCaseResponse(
        cases=[_case_to_response(c) for c in similar_cases],
        total_count=len(similar_cases)
    )


@router.get("/{case_id}/same-court", response_model=SameCourtResponse)
async def get_cases_by_court(
    case_id: int,
    max_results: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """获取同法院案例"""
    service = CaseRecommendationService(db)
    same_court_cases = service.get_cases_by_court(case_id, max_results)

    return SameCourtResponse(
        cases=[_case_to_response(c) for c in same_court_cases],
        total_count=len(same_court_cases)
    )


@router.get("/{case_id}/same-cause", response_model=SameCourtResponse)
async def get_cases_by_cause(
    case_id: int,
    max_results: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """获取同案由案例"""
    service = CaseRecommendationService(db)
    same_cause_cases = service.get_cases_by_cause(case_id, max_results)

    return SameCourtResponse(
        cases=[_case_to_response(c) for c in same_cause_cases],
        total_count=len(same_cause_cases)
    )


@router.get("/guiding-cases", response_model=GuidingCaseResponse)
async def get_guide_cases(
    court_level: Optional[str] = Query(None),
    cause_of_action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取指导性案例列表"""
    service = CaseRecommendationService(db)
    guide_cases, total = service.get_guide_cases(
        court_level=court_level,
        cause_of_action=cause_of_action,
        page=page,
        page_size=page_size
    )

    return GuidingCaseResponse(
        cases=[_case_to_response(c) for c in guide_cases],
        total=total,
        page=page,
        page_size=page_size
    )
