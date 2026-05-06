"""案例统计分析API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from datetime import datetime

from app.services.case_statistics import CaseStatisticsService
from app.database import SessionLocal

router = APIRouter(prefix="/api/v1/archive", tags=["案例统计"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_stats_svc(db=Depends(get_db)) -> CaseStatisticsService:
    return CaseStatisticsService(db)


@router.get("/stats/by-court")
async def get_stats_by_court(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    svc: CaseStatisticsService = Depends(get_stats_svc)
):
    """按法院级别统计"""
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    return svc.get_by_court_level(start_date=start, end_date=end)


@router.get("/stats/by-type")
async def get_stats_by_type(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    svc: CaseStatisticsService = Depends(get_stats_svc)
):
    """按案件类型统计"""
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    return svc.get_by_case_type(start_date=start, end_date=end)


@router.get("/stats/by-cause")
async def get_stats_by_cause(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(20, ge=1, le=100),
    svc: CaseStatisticsService = Depends(get_stats_svc)
):
    """按案由统计（Top N）"""
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    return svc.get_by_cause(start_date=start, end_date=end, limit=limit)


@router.get("/stats/trends")
async def get_stats_trends(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    group_by: str = Query("month", regex="^(day|week|month)$"),
    svc: CaseStatisticsService = Depends(get_stats_svc)
):
    """获取趋势统计"""
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    return svc.get_trends(group_by=group_by, start_date=start, end_date=end)


@router.get("/stats/summary")
async def get_stats_summary(
    svc: CaseStatisticsService = Depends(get_stats_svc)
):
    """获取统计摘要"""
    return svc.get_summary()
