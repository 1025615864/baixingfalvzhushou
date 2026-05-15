"""裁判文书检索路由 (异步)"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.court_case import CourtCase, LawArticle

router = APIRouter(prefix="/api/v1/court-cases", tags=["裁判文书"])


@router.get("/search")
async def search_cases(
    q: Optional[str] = Query(None, description="关键词搜索"),
    case_type: Optional[str] = Query(None, description="案件类型: civil/criminal/administrative/labor"),
    court_name: Optional[str] = Query(None, description="法院名称"),
    category: Optional[str] = Query(None, description="案件分类"),
    min_amount: Optional[float] = Query(None, description="最小涉案金额"),
    max_amount: Optional[float] = Query(None, description="最大涉案金额"),
    appeal_status: Optional[str] = Query(None, description="上诉状态"),
    execution_status: Optional[str] = Query(None, description="执行状态"),
    year: Optional[int] = Query(None, description="案件年份"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """搜索裁判文书"""
    stmt = select(CourtCase).filter(CourtCase.is_deleted == False, CourtCase.is_published == True)

    if q:
        q_pattern = f"%{q}%"
        stmt = stmt.filter(
            or_(
                CourtCase.case_name.ilike(q_pattern),
                CourtCase.case_number.ilike(q_pattern),
                CourtCase.content.ilike(q_pattern),
                CourtCase.judgment_summary.ilike(q_pattern),
                CourtCase.legal_basis.ilike(q_pattern),
                CourtCase.keywords.ilike(q_pattern),
                CourtCase.plaintiff.ilike(q_pattern),
                CourtCase.defendant.ilike(q_pattern),
            )
        )

    if case_type:
        stmt = stmt.filter(CourtCase.case_type == case_type)

    if court_name:
        stmt = stmt.filter(CourtCase.court_name.like(f"%{court_name}%"))

    if category:
        stmt = stmt.filter(CourtCase.category == category)

    if min_amount is not None:
        stmt = stmt.filter(CourtCase.case_amount >= min_amount)
    if max_amount is not None:
        stmt = stmt.filter(CourtCase.case_amount <= max_amount)

    if appeal_status:
        stmt = stmt.filter(CourtCase.appeal_status == appeal_status)
    if execution_status:
        stmt = stmt.filter(CourtCase.execution_status == execution_status)
    if year:
        stmt = stmt.filter(func.extract("year", CourtCase.case_date) == year)

    # 计数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    result = await db.execute(count_stmt)
    total = result.scalar_one()

    # 分页
    stmt = stmt.order_by(CourtCase.case_date.desc().nullslast(), CourtCase.id.desc()) \
        .offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/types")
async def get_case_types():
    """获取案件类型列表"""
    return {
        "types": [
            {"value": "civil", "label": "民事案件", "count": 0},
            {"value": "criminal", "label": "刑事案件", "count": 0},
            {"value": "administrative", "label": "行政案件", "count": 0},
            {"value": "labor", "label": "劳动争议", "count": 0},
            {"value": "commercial", "label": "商事案件", "count": 0},
            {"value": "execution", "label": "执行案件", "count": 0},
        ]
    }


@router.get("/featured")
async def get_featured_cases(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """获取精选裁判文书"""
    stmt = select(CourtCase).filter(
        CourtCase.is_deleted == False,
        CourtCase.is_published == True,
        CourtCase.is_featured == True,
    ).order_by(CourtCase.view_count.desc()).limit(limit)
    result = await db.execute(stmt)
    cases = result.scalars().all()
    return {"items": cases}


@router.get("/{case_id}")
async def get_case_detail(
    case_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取裁判文书详情"""
    stmt = select(CourtCase).filter(
        CourtCase.id == case_id,
        CourtCase.is_deleted == False,
    )
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="裁判文书不存在")

    case.view_count = (case.view_count or 0) + 1
    await db.commit()
    await db.refresh(case)
    return case


@router.get("/number/{case_number}")
async def get_case_by_number(
    case_number: str,
    db: AsyncSession = Depends(get_db),
):
    """通过案号获取裁判文书"""
    stmt = select(CourtCase).filter(
        CourtCase.case_number == case_number,
        CourtCase.is_deleted == False,
    )
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="裁判文书不存在")
    return case


@router.get("/similar/{case_id}")
async def get_similar_cases(
    case_id: int,
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """获取相似裁判文书"""
    stmt = select(CourtCase).filter(CourtCase.id == case_id)
    result = await db.execute(stmt)
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="裁判文书不存在")

    stmt = select(CourtCase).filter(
        CourtCase.id != case_id,
        CourtCase.is_deleted == False,
        CourtCase.is_published == True,
        or_(
            CourtCase.case_type == original.case_type,
            CourtCase.category == original.category,
        )
    )

    if original.court_name:
        stmt = stmt.order_by(
            CourtCase.court_name == original.court_name,
            CourtCase.case_date.desc().nullslast(),
        )
    else:
        stmt = stmt.order_by(CourtCase.case_date.desc().nullslast())

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    cases = result.scalars().all()
    return {"items": cases, "original_id": case_id}


@router.get("/law/{law_number}")
async def get_cases_by_law(
    law_number: str,
    article_number: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取引用特定法律的裁判文书"""
    stmt = select(CourtCase).filter(
        CourtCase.is_deleted == False,
        CourtCase.is_published == True,
        or_(
            CourtCase.applicable_laws.ilike(f"%{law_number}%"),
            CourtCase.legal_basis.ilike(f"%{law_number}%"),
        )
    )
    if article_number:
        stmt = stmt.filter(
            CourtCase.applicable_articles.ilike(f"%{article_number}%")
        )

    # 计数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    result = await db.execute(count_stmt)
    total = result.scalar_one()

    # 分页
    stmt = stmt.order_by(CourtCase.case_date.desc().nullslast()) \
        .offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "law_number": law_number,
        "article_number": article_number,
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ==================== 法律法规检索 ====================

@router.get("/law/search")
async def search_laws(
    q: Optional[str] = Query(None),
    law_name: Optional[str] = Query(None),
    article_number: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """搜索法律法规条文"""
    stmt = select(LawArticle).filter(LawArticle.is_deleted == False, LawArticle.is_active == True)

    if q:
        q_pattern = f"%{q}%"
        stmt = stmt.filter(
            or_(
                LawArticle.law_name.ilike(q_pattern),
                LawArticle.article_title.ilike(q_pattern),
                LawArticle.content.ilike(q_pattern),
                LawArticle.keywords.ilike(q_pattern),
            )
        )

    if law_name:
        stmt = stmt.filter(LawArticle.law_name.ilike(f"%{law_name}%"))
    if article_number:
        stmt = stmt.filter(LawArticle.article_number == article_number)
    if category:
        stmt = stmt.filter(LawArticle.category == category)
    if jurisdiction:
        stmt = stmt.filter(LawArticle.jurisdiction == jurisdiction)

    # 计数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    result = await db.execute(count_stmt)
    total = result.scalar_one()

    # 分页
    stmt = stmt.order_by(LawArticle.law_name, LawArticle.article_number) \
        .offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/law/{law_number}")
async def get_law_detail(
    law_number: str,
    db: AsyncSession = Depends(get_db),
):
    """获取法律详情（包含所有条文）"""
    stmt = select(LawArticle).filter(
        LawArticle.law_number == law_number,
        LawArticle.is_deleted == False,
        LawArticle.is_active == True,
    ).order_by(LawArticle.article_number)
    result = await db.execute(stmt)
    articles = result.scalars().all()

    if not articles:
        raise HTTPException(status_code=404, detail="法律条文不存在")

    law_name = articles[0].law_name if articles else law_number
    jurisdiction = articles[0].jurisdiction if articles else None
    category = articles[0].category if articles else None

    return {
        "law_number": law_number,
        "law_name": law_name,
        "jurisdiction": jurisdiction,
        "category": category,
        "articles": articles,
        "total_articles": len(articles),
    }


@router.get("/law/{law_number}/article/{article_number}")
async def get_law_article(
    law_number: str,
    article_number: str,
    db: AsyncSession = Depends(get_db),
):
    """获取特定法律条文"""
    stmt = select(LawArticle).filter(
        LawArticle.law_number == law_number,
        LawArticle.article_number == article_number,
        LawArticle.is_deleted == False,
    )
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="法律条文不存在")
    return article
