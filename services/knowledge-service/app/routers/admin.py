"""管理员路由 - 知识审核、质量评分、看板统计"""
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func, select, case, and_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.knowledge import LegalKnowledge
from app.models.admin import KnowledgeAuditLog, KnowledgeQualityScore

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from typing import List, Set

    _security = HTTPBearer(auto_error=False)

    GLOBAL_ADMIN_ROLES = {"super_admin", "admin"}

    DOMAIN_ROLES: dict[str, Set[str]] = {
        "global": {"super_admin", "admin"},
        "knowledge": {"knowledge_admin", "knowledge_ops"},
    }

    class AdminUser:
        def __init__(self, user_id: int, role: str, permissions: Optional[List[str]] = None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in GLOBAL_ADMIN_ROLES

        def has_domain_access(self, domain: str) -> bool:
            if self.is_super_admin:
                return True
            return self.role in DOMAIN_ROLES.get(domain, set())

    async def get_admin_user(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> AdminUser:
        if not credentials:
            raise HTTPException(status_code=401, detail="未提供认证凭据")
        return AdminUser(user_id=1, role="admin", permissions=[])

    def require_domain_role(domain: str, roles: Optional[List[str]] = None):
        async def domain_checker(admin: AdminUser = Depends(get_admin_user)):
            if admin.is_super_admin:
                return admin
            if not admin.has_domain_access(domain):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要 {domain} 域管理角色，当前角色: {admin.role}",
                )
            if roles and admin.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要角色: {', '.join(roles)}，当前角色: {admin.role}",
                )
            return admin
        return domain_checker


router = APIRouter(prefix="/admin", tags=["管理后台"])


VALID_AUDIT_ACTIONS = {"submit", "approve", "reject", "publish", "archive"}


class AuditRequest(BaseModel):
    action: str = Field(..., description="审核操作: approve/reject")
    comment: Optional[str] = None


class BatchAuditRequest(BaseModel):
    knowledge_ids: List[int] = Field(..., min_length=1)
    action: str = Field(..., description="审核操作: approve/reject")
    comment: Optional[str] = None


class QualityScoreRequest(BaseModel):
    accuracy: Optional[float] = Field(None, ge=0, le=100)
    completeness: Optional[float] = Field(None, ge=0, le=100)
    readability: Optional[float] = Field(None, ge=0, le=100)
    overall_score: Optional[float] = Field(None, ge=0, le=100)
    scorer_type: str = Field("manual", description="评分类型: ai/manual")
    comment: Optional[str] = None


class AuditLogResponse(BaseModel):
    id: int
    knowledge_id: int
    operator_id: Optional[int]
    operator_name: Optional[str]
    action: str
    from_status: Optional[str]
    to_status: Optional[str]
    comment: Optional[str]
    extra_data: Optional[dict]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class QualityScoreResponse(BaseModel):
    id: int
    knowledge_id: int
    accuracy: Optional[float]
    completeness: Optional[float]
    readability: Optional[float]
    overall_score: Optional[float]
    scorer_type: str
    scorer_id: Optional[int]
    comment: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    total: int
    pending_review: int
    published: int
    category_distribution: dict
    trend_7d: list


class AuditQueueItem(BaseModel):
    id: int
    title: str
    knowledge_type: str
    category: Optional[str]
    status: str
    created_by: Optional[int]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class AuditQueueResponse(BaseModel):
    items: List[AuditQueueItem]
    total: int
    page: int
    page_size: int


class StatsResponse(BaseModel):
    category_distribution: dict
    review_efficiency: dict
    quality_distribution: dict


def _create_audit_log(
    db: Session,
    knowledge_id: int,
    admin: AdminUser,
    action: str,
    from_status: Optional[str],
    to_status: Optional[str],
    comment: Optional[str] = None,
    extra_data: Optional[dict] = None,
) -> KnowledgeAuditLog:
    log = KnowledgeAuditLog(
        knowledge_id=knowledge_id,
        operator_id=admin.user_id,
        operator_name=admin.role,
        action=action,
        from_status=from_status,
        to_status=to_status,
        comment=comment,
        extra_data=extra_data,
    )
    db.add(log)
    return log


def _perform_audit(
    db: Session,
    knowledge: LegalKnowledge,
    action: str,
    admin: AdminUser,
    comment: Optional[str],
) -> LegalKnowledge:
    from_status = knowledge.status

    if action == "approve":
        knowledge.status = "published"
        knowledge.reviewed_by = admin.user_id
        knowledge.reviewed_at = datetime.now()
    elif action == "reject":
        knowledge.status = "draft"
        knowledge.reviewed_by = admin.user_id
        knowledge.reviewed_at = datetime.now()
    else:
        raise HTTPException(status_code=400, detail=f"不支持的审核操作: {action}")

    _create_audit_log(
        db, knowledge.id, admin, action, from_status, knowledge.status, comment
    )
    db.commit()
    db.refresh(knowledge)
    return knowledge


@router.get("/dashboard", response_model=DashboardResponse, dependencies=[Depends(require_domain_role("knowledge", roles=["knowledge_admin"]))])
async def get_dashboard(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """知识看板 - 总量/待审核/已发布/分类分布/7天趋势"""
    total = db.execute(
        select(func.count()).select_from(LegalKnowledge).where(LegalKnowledge.is_deleted == False)
    ).scalar() or 0

    pending_review = db.execute(
        select(func.count()).select_from(LegalKnowledge).where(
            and_(LegalKnowledge.status == "pending_review", LegalKnowledge.is_deleted == False)
        )
    ).scalar() or 0

    published = db.execute(
        select(func.count()).select_from(LegalKnowledge).where(
            and_(LegalKnowledge.status == "published", LegalKnowledge.is_deleted == False)
        )
    ).scalar() or 0

    category_rows = db.execute(
        select(LegalKnowledge.category, func.count(LegalKnowledge.id).label("cnt"))
        .where(LegalKnowledge.is_deleted == False)
        .group_by(LegalKnowledge.category)
    ).all()
    category_distribution = {row[0] or "未分类": row[1] for row in category_rows}

    trend_7d = []
    for i in range(6, -1, -1):
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = db.execute(
            select(func.count()).select_from(LegalKnowledge).where(
                and_(
                    LegalKnowledge.created_at >= day_start,
                    LegalKnowledge.created_at < day_end,
                    LegalKnowledge.is_deleted == False,
                )
            )
        ).scalar() or 0
        trend_7d.append({"date": day_start.strftime("%Y-%m-%d"), "count": count})

    return DashboardResponse(
        total=total,
        pending_review=pending_review,
        published=published,
        category_distribution=category_distribution,
        trend_7d=trend_7d,
    )


@router.get("/audit-queue", response_model=AuditQueueResponse, dependencies=[Depends(require_domain_role("knowledge", roles=["knowledge_admin"]))])
async def get_audit_queue(
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """审核队列 - 支持状态筛选+分页"""
    query = select(LegalKnowledge).where(LegalKnowledge.is_deleted == False)

    if status_filter:
        query = query.where(LegalKnowledge.status == status_filter)
    else:
        query = query.where(LegalKnowledge.status == "pending_review")

    total = db.execute(
        select(func.count()).select_from(query.subquery())
    ).scalar() or 0

    rows = db.execute(
        query.order_by(LegalKnowledge.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = []
    for row in rows:
        k = row[0]
        items.append(AuditQueueItem(
            id=k.id,
            title=k.title,
            knowledge_type=k.knowledge_type,
            category=k.category,
            status=k.status,
            created_by=k.created_by,
            created_at=k.created_at,
        ))

    return AuditQueueResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/knowledge/{knowledge_id}/audit", dependencies=[Depends(require_domain_role("knowledge", roles=["knowledge_ops"]))])
async def audit_knowledge(
    knowledge_id: int,
    request: AuditRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """审核操作 - approve/reject"""
    knowledge = db.execute(
        select(LegalKnowledge).where(LegalKnowledge.id == knowledge_id)
    ).scalar_one_or_none()

    if not knowledge:
        raise HTTPException(status_code=404, detail="知识不存在")

    if knowledge.status != "pending_review":
        raise HTTPException(status_code=400, detail=f"当前状态不可审核: {knowledge.status}")

    if request.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="审核操作仅支持 approve/reject")

    knowledge = _perform_audit(db, knowledge, request.action, admin, request.comment)

    return {"message": "审核完成", "knowledge_id": knowledge_id, "status": knowledge.status}


@router.post("/knowledge/batch-audit", dependencies=[Depends(require_domain_role("knowledge", roles=["knowledge_admin"]))])
async def batch_audit_knowledge(
    request: BatchAuditRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """批量审核"""
    if request.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="审核操作仅支持 approve/reject")

    results = []
    for kid in request.knowledge_ids:
        knowledge = db.execute(
            select(LegalKnowledge).where(LegalKnowledge.id == kid)
        ).scalar_one_or_none()

        if not knowledge:
            results.append({"knowledge_id": kid, "status": "not_found"})
            continue

        if knowledge.status != "pending_review":
            results.append({"knowledge_id": kid, "status": "skipped", "reason": f"状态不可审核: {knowledge.status}"})
            continue

        _perform_audit(db, knowledge, request.action, admin, request.comment)
        results.append({"knowledge_id": kid, "status": "success", "new_status": knowledge.status})

    return {"message": "批量审核完成", "results": results}


@router.post("/knowledge/{knowledge_id}/quality-score", response_model=QualityScoreResponse, dependencies=[Depends(require_domain_role("knowledge", roles=["knowledge_ops"]))])
async def create_quality_score(
    knowledge_id: int,
    request: QualityScoreRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """质量评分"""
    knowledge = db.execute(
        select(LegalKnowledge).where(LegalKnowledge.id == knowledge_id)
    ).scalar_one_or_none()

    if not knowledge:
        raise HTTPException(status_code=404, detail="知识不存在")

    overall = request.overall_score
    if overall is None and any(v is not None for v in [request.accuracy, request.completeness, request.readability]):
        scores = [v for v in [request.accuracy, request.completeness, request.readability] if v is not None]
        overall = round(sum(scores) / len(scores), 2) if scores else None

    score = KnowledgeQualityScore(
        knowledge_id=knowledge_id,
        accuracy=request.accuracy,
        completeness=request.completeness,
        readability=request.readability,
        overall_score=overall,
        scorer_type=request.scorer_type,
        scorer_id=admin.user_id,
        comment=request.comment,
    )
    db.add(score)
    db.commit()
    db.refresh(score)

    _create_audit_log(
        db, knowledge_id, admin, "quality_score",
        None, None, request.comment,
        extra_data={"score_id": score.id, "overall_score": overall},
    )
    db.commit()

    return score


@router.get("/quality-scores", dependencies=[Depends(require_domain_role("knowledge", roles=["knowledge_ops"]))])
async def list_quality_scores(
    knowledge_id: Optional[int] = None,
    scorer_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """质量评分列表"""
    query = select(KnowledgeQualityScore)

    if knowledge_id:
        query = query.where(KnowledgeQualityScore.knowledge_id == knowledge_id)
    if scorer_type:
        query = query.where(KnowledgeQualityScore.scorer_type == scorer_type)

    total = db.execute(
        select(func.count()).select_from(query.subquery())
    ).scalar() or 0

    rows = db.execute(
        query.order_by(KnowledgeQualityScore.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = []
    for row in rows:
        s = row[0]
        items.append(QualityScoreResponse(
            id=s.id,
            knowledge_id=s.knowledge_id,
            accuracy=float(s.accuracy) if s.accuracy is not None else None,
            completeness=float(s.completeness) if s.completeness is not None else None,
            readability=float(s.readability) if s.readability is not None else None,
            overall_score=float(s.overall_score) if s.overall_score is not None else None,
            scorer_type=s.scorer_type,
            scorer_id=s.scorer_id,
            comment=s.comment,
            created_at=s.created_at,
        ))

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/stats", response_model=StatsResponse, dependencies=[Depends(require_domain_role("knowledge", roles=["knowledge_ops"]))])
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """统计 - 分类分布/审核效率/质量分布"""
    category_rows = db.execute(
        select(LegalKnowledge.category, func.count(LegalKnowledge.id).label("cnt"))
        .where(LegalKnowledge.is_deleted == False)
        .group_by(LegalKnowledge.category)
    ).all()
    category_distribution = {row[0] or "未分类": row[1] for row in category_rows}

    total_audits = db.execute(
        select(func.count()).select_from(KnowledgeAuditLog)
    ).scalar() or 0

    approved_count = db.execute(
        select(func.count()).select_from(KnowledgeAuditLog).where(
            KnowledgeAuditLog.action == "approve"
        )
    ).scalar() or 0

    rejected_count = db.execute(
        select(func.count()).select_from(KnowledgeAuditLog).where(
            KnowledgeAuditLog.action == "reject"
        )
    ).scalar() or 0

    review_efficiency = {
        "total_reviews": total_audits,
        "approved": approved_count,
        "rejected": rejected_count,
        "approval_rate": round(approved_count / total_audits * 100, 2) if total_audits > 0 else 0,
    }

    quality_rows = db.execute(
        select(
            case(
                (KnowledgeQualityScore.overall_score >= 80, "excellent"),
                (KnowledgeQualityScore.overall_score >= 60, "good"),
                (KnowledgeQualityScore.overall_score >= 40, "average"),
                else_="poor",
            ).label("level"),
            func.count(KnowledgeQualityScore.id).label("cnt"),
        ).group_by("level")
    ).all()
    quality_distribution = {row[0]: row[1] for row in quality_rows}

    return StatsResponse(
        category_distribution=category_distribution,
        review_efficiency=review_efficiency,
        quality_distribution=quality_distribution,
    )


@router.get("/audit-logs", dependencies=[Depends(require_domain_role("knowledge", roles=["knowledge_admin"]))])
async def get_audit_logs(
    knowledge_id: Optional[int] = None,
    action: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """审计日志"""
    query = select(KnowledgeAuditLog)

    if knowledge_id:
        query = query.where(KnowledgeAuditLog.knowledge_id == knowledge_id)
    if action:
        query = query.where(KnowledgeAuditLog.action == action)

    total = db.execute(
        select(func.count()).select_from(query.subquery())
    ).scalar() or 0

    rows = db.execute(
        query.order_by(KnowledgeAuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = []
    for row in rows:
        log = row[0]
        items.append(AuditLogResponse(
            id=log.id,
            knowledge_id=log.knowledge_id,
            operator_id=log.operator_id,
            operator_name=log.operator_name,
            action=log.action,
            from_status=log.from_status,
            to_status=log.to_status,
            comment=log.comment,
            extra_data=log.extra_data,
            created_at=log.created_at,
        ))

    return {"items": items, "total": total, "page": page, "page_size": page_size}
