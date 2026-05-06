"""AI质量运营API"""
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta

from app.services.quality_service import get_quality_service, QualityService
from app.dependencies.auth import require_admin, UserContext

router = APIRouter(prefix="/api/v1/ai-ops", tags=["AI质量运营"])


def get_quality_svc() -> QualityService:
    return get_quality_service()


class QualityFeedbackRequest(BaseModel):
    conversation_id: str
    user_id: Optional[int] = None
    query: str
    response: str
    quality_score: float = Field(..., ge=0.0, le=1.0, description="质量评分 0-1")
    feedback: Optional[int] = Field(None, description="用户反馈: 1=点赞, -1=点踩")
    issues: Optional[List[str]] = Field(None, description="问题标签列表")


class QualityStatsResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    total_queries: int
    avg_quality_score: float
    positive_feedback: int
    negative_feedback: int
    top_issues: List[tuple]


class TokenStatsResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    avg_latency_ms: float
    by_model: List[dict]


class ConversationStats(BaseModel):
    total_conversations: int
    total_messages: int
    avg_response_time_ms: float
    hallucination_rate: float


class QualityReport(BaseModel):
    period: str
    total_queries: int
    rag_hit_rate: float
    avg_latency_ms: float
    quality_score: float


@router.post("/quality/feedback")
async def submit_quality_feedback(
    request: QualityFeedbackRequest,
    user: UserContext = Depends(require_admin),
    svc: QualityService = Depends(get_quality_svc)
):
    """用户提交质量反馈"""
    record_id = await svc.record_quality(
        conversation_id=request.conversation_id,
        query=request.query,
        response=request.response,
        quality_score=request.quality_score,
        user_id=request.user_id,
        feedback=request.feedback,
        issues=request.issues
    )
    return {"success": True, "record_id": record_id}


@router.get("/quality/stats", response_model=QualityStatsResponse)
async def get_quality_stats(
    period: str = Query("7d", regex="^(1d|7d|30d)$"),
    svc: QualityService = Depends(get_quality_svc)
):
    """获取质量统计"""
    report = await svc.get_quality_report(period=period)
    return QualityStatsResponse(**report)


@router.get("/token/stats", response_model=TokenStatsResponse)
async def get_token_stats(
    period: str = Query("7d", regex="^(1d|7d|30d)$"),
    user: UserContext = Depends(require_admin),
    svc: QualityService = Depends(get_quality_svc)
):
    """获取Token消耗统计"""
    report = await svc.get_token_usage_report(period=period)
    return TokenStatsResponse(**report)


@router.get("/cost/stats")
async def get_cost_stats(
    period: str = Query("7d", regex="^(1d|7d|30d)$"),
    user: UserContext = Depends(require_admin),
    svc: QualityService = Depends(get_quality_svc)
):
    """获取成本统计"""
    return await svc.get_cost_statistics(period=period)


@router.get("/ai/conversations", response_model=ConversationStats)
async def get_conversation_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: UserContext = Depends(require_admin)
):
    """获取对话统计"""
    return ConversationStats(
        total_conversations=0,
        total_messages=0,
        avg_response_time_ms=0.0,
        hallucination_rate=0.0
    )


@router.get("/ai/quality/report", response_model=QualityReport)
async def get_quality_report(
    period: str = Query("7d", regex="^(1d|7d|30d)$")
):
    """获取质量报告"""
    return QualityReport(
        period=period,
        total_queries=0,
        rag_hit_rate=0.0,
        avg_latency_ms=0.0,
        quality_score=0.0
    )


@router.get("/knowledge/gaps")
async def get_knowledge_gaps(user: UserContext = Depends(require_admin)):
    """获取知识缺口"""
    return {
        "gaps": [],
        "total_queries": 0,
        "unanswered_rate": 0.0
    }


@router.get("/vector/status")
async def get_vector_status():
    """获取向量库状态"""
    return {
        "knowledge_vectors": 0,
        "archive_vectors": 0,
        "last_sync": None
    }


@router.get("/analytics/overview")
async def get_analytics_overview():
    """获取运营数据分析概览"""
    return {
        "total_knowledge": 0,
        "total_cases": 0,
        "total_conversations": 0,
        "avg_response_time_ms": 0.0,
        "active_users_30d": 0
    }


class HitRateResponse(BaseModel):
    start_date: str
    end_date: str
    group_by: str
    stats: List[dict]


@router.get("/retrieval/hit-rate", response_model=HitRateResponse)
async def get_retrieval_hit_rate(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = Query("day", regex="^(hour|day)$"),
    user: UserContext = Depends(require_admin)
):
    """获取检索命中率统计"""
    from app.database import SessionLocal
    from app.services.retrieval_log_service import RetrievalLogService

    db = SessionLocal()
    try:
        svc = RetrievalLogService(db)
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        return svc.get_hit_rate_stats(start_date=start, end_date=end, group_by=group_by)
    finally:
        db.close()


@router.get("/retrieval/distribution")
async def get_retrieval_distribution(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取检索层级分布"""
    from app.database import SessionLocal
    from app.services.retrieval_log_service import RetrievalLogService

    db = SessionLocal()
    try:
        svc = RetrievalLogService(db)
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        return svc.get_level_distribution(start_date=start, end_date=end)
    finally:
        db.close()


@router.get("/retrieval/unmatched")
async def get_unmatched_queries(
    min_count: int = Query(3, ge=1),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: UserContext = Depends(require_admin)
):
    """获取未命中查询（高频使用fallback的查询）"""
    from app.database import SessionLocal
    from app.services.retrieval_log_service import RetrievalLogService

    db = SessionLocal()
    try:
        svc = RetrievalLogService(db)
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        return svc.get_unmatched_queries(min_count=min_count, start_date=start, end_date=end)
    finally:
        db.close()
