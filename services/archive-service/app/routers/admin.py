"""管理员路由 - 案例审核与管理"""
import logging
from typing import Optional, List
from datetime import datetime, timedelta

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.archive import LegalCase, CaseCategory
from app.models.admin import CaseAuditLog

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    from fastapi import Header
    from typing import List, Set

    GLOBAL_ADMIN_ROLES = {"super_admin", "admin"}

    DOMAIN_ROLES: dict[str, Set[str]] = {
        "global": {"super_admin", "admin"},
        "archive": {"archive_admin", "archive_ops"},
    }

    class AdminUser:
        def __init__(self, user_id: int = 0, role: str = "admin", permissions: Optional[List[str]] = None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in GLOBAL_ADMIN_ROLES

        def has_permission(self, permission: str) -> bool:
            return self.is_super_admin or permission in self.permissions

        def has_domain_access(self, domain: str) -> bool:
            if self.is_super_admin:
                return True
            return self.role in DOMAIN_ROLES.get(domain, set())

    async def get_admin_user(
        authorization: Optional[str] = Header(None, alias="Authorization"),
    ) -> AdminUser:
        if not authorization:
            raise HTTPException(status_code=401, detail="未提供认证凭据")
        return AdminUser(user_id=1, role="admin")

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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["管理后台"])


class AuditRequest(BaseModel):
    action: str
    comment: Optional[str] = None


class BatchAuditRequest(BaseModel):
    case_ids: List[int]
    action: str
    comment: Optional[str] = None


class AuditLogResponse(BaseModel):
    id: int
    case_id: int
    operator_id: int
    operator_name: Optional[str]
    action: str
    from_status: Optional[str]
    to_status: Optional[str]
    comment: Optional[str]
    extra_data: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


def _validate_audit_action(action: str):
    valid_actions = {"approve", "reject"}
    if action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"无效的审核操作: {action}，允许: {', '.join(valid_actions)}",
        )


def _create_audit_log(
    db: Session,
    case_id: int,
    admin: AdminUser,
    action: str,
    from_status: Optional[str],
    to_status: Optional[str],
    comment: Optional[str] = None,
    extra_data: Optional[dict] = None,
) -> CaseAuditLog:
    log = CaseAuditLog(
        case_id=case_id,
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


@router.get("/dashboard", dependencies=[Depends(require_domain_role("archive", roles=["archive_admin"]))])
async def get_dashboard(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """案例看板 - 总量/待审核/已发布/分类分布/热门排行"""
    total = db.query(func.count(LegalCase.id)).filter(LegalCase.is_deleted == False).scalar() or 0
    pending_review = db.query(func.count(LegalCase.id)).filter(
        LegalCase.status == "pending_review",
        LegalCase.is_deleted == False,
    ).scalar() or 0
    published = db.query(func.count(LegalCase.id)).filter(
        LegalCase.status == "published",
        LegalCase.is_deleted == False,
    ).scalar() or 0

    category_dist = (
        db.query(LegalCase.category, func.count(LegalCase.id).label("count"))
        .filter(LegalCase.is_deleted == False, LegalCase.category.isnot(None))
        .group_by(LegalCase.category)
        .order_by(func.count(LegalCase.id).desc())
        .limit(10)
        .all()
    )

    top_cases = (
        db.query(LegalCase.id, LegalCase.title, LegalCase.view_count)
        .filter(LegalCase.is_deleted == False, LegalCase.status == "published")
        .order_by(LegalCase.view_count.desc())
        .limit(10)
        .all()
    )

    return {
        "total": total,
        "pending_review": pending_review,
        "published": published,
        "draft": db.query(func.count(LegalCase.id)).filter(
            LegalCase.status == "draft", LegalCase.is_deleted == False
        ).scalar() or 0,
        "archived": db.query(func.count(LegalCase.id)).filter(
            LegalCase.status == "archived", LegalCase.is_deleted == False
        ).scalar() or 0,
        "category_distribution": [
            {"category": c, "count": n} for c, n in category_dist if c
        ],
        "top_viewed": [
            {"id": cid, "title": t, "view_count": vc} for cid, t, vc in top_cases
        ],
    }


@router.get("/audit-queue", dependencies=[Depends(require_domain_role("archive", roles=["archive_admin"]))])
async def get_audit_queue(
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """审核队列 - 支持状态筛选+分页"""
    query = db.query(LegalCase).filter(LegalCase.is_deleted == False)

    if status_filter:
        valid_statuses = {"draft", "pending_review", "published", "archived"}
        if status_filter not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"无效状态: {status_filter}")
        query = query.filter(LegalCase.status == status_filter)
    else:
        query = query.filter(LegalCase.status == "pending_review")

    total = query.count()
    cases = (
        query.order_by(LegalCase.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": c.id,
                "title": c.title,
                "case_type": c.case_type,
                "category": c.category,
                "status": c.status,
                "court": c.court,
                "created_by": c.created_by,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in cases
        ],
    }


@router.post("/cases/{case_id}/audit", dependencies=[Depends(require_domain_role("archive", roles=["archive_ops"]))])
async def audit_case(
    case_id: int,
    request: AuditRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """审核操作 - approve/reject"""
    _validate_audit_action(request.action)

    case = db.query(LegalCase).filter(
        LegalCase.id == case_id, LegalCase.is_deleted == False
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")

    if case.status != "pending_review":
        raise HTTPException(status_code=400, detail=f"案例当前状态为 {case.status}，无法审核")

    from_status = case.status
    if request.action == "approve":
        case.status = "published"
        case.reviewed_by = admin.user_id
        case.reviewed_at = datetime.now()
        to_status = "published"
    else:
        case.status = "draft"
        to_status = "draft"

    _create_audit_log(
        db=db,
        case_id=case_id,
        admin=admin,
        action=request.action,
        from_status=from_status,
        to_status=to_status,
        comment=request.comment,
    )

    db.commit()
    db.refresh(case)

    return {
        "id": case.id,
        "title": case.title,
        "status": case.status,
        "reviewed_by": case.reviewed_by,
        "reviewed_at": case.reviewed_at.isoformat() if case.reviewed_at else None,
    }


@router.post("/cases/batch-audit", dependencies=[Depends(require_domain_role("archive", roles=["archive_admin"]))])
async def batch_audit_cases(
    request: BatchAuditRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """批量审核"""
    _validate_audit_action(request.action)

    if not request.case_ids:
        raise HTTPException(status_code=400, detail="案例ID列表不能为空")

    cases = db.query(LegalCase).filter(
        LegalCase.id.in_(request.case_ids),
        LegalCase.is_deleted == False,
        LegalCase.status == "pending_review",
    ).all()

    if not cases:
        raise HTTPException(status_code=404, detail="未找到符合条件的待审核案例")

    results = {"approved": 0, "rejected": 0, "skipped": 0}

    for case in cases:
        from_status = case.status
        if request.action == "approve":
            case.status = "published"
            case.reviewed_by = admin.user_id
            case.reviewed_at = datetime.now()
            results["approved"] += 1
            to_status = "published"
        else:
            case.status = "draft"
            results["rejected"] += 1
            to_status = "draft"

        _create_audit_log(
            db=db,
            case_id=case.id,
            admin=admin,
            action=request.action,
            from_status=from_status,
            to_status=to_status,
            comment=request.comment,
        )

    skipped = len(request.case_ids) - len(cases)
    results["skipped"] = skipped

    db.commit()

    return {
        "total_requested": len(request.case_ids),
        "processed": len(cases),
        "results": results,
    }


@router.get("/stats", dependencies=[Depends(require_domain_role("archive", roles=["archive_admin"]))])
async def get_stats(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """统计 - 分类分布/审核效率/引用排行"""
    category_stats = (
        db.query(LegalCase.category, func.count(LegalCase.id).label("count"))
        .filter(LegalCase.is_deleted == False, LegalCase.category.isnot(None))
        .group_by(LegalCase.category)
        .order_by(func.count(LegalCase.id).desc())
        .all()
    )

    seven_days_ago = datetime.now() - timedelta(days=7)
    audit_logs_recent = (
        db.query(CaseAuditLog.action, func.count(CaseAuditLog.id).label("count"))
        .filter(CaseAuditLog.created_at >= seven_days_ago)
        .group_by(CaseAuditLog.action)
        .all()
    )

    avg_audit_time = None
    approved_logs = (
        db.query(CaseAuditLog)
        .filter(CaseAuditLog.action == "approve")
        .order_by(CaseAuditLog.created_at.desc())
        .limit(100)
        .all()
    )
    if approved_logs:
        total_hours = 0
        count = 0
        for log in approved_logs:
            case = db.query(LegalCase).filter(LegalCase.id == log.case_id).first()
            if case and case.created_at and log.created_at:
                delta = log.created_at - case.created_at
                total_hours += delta.total_seconds() / 3600
                count += 1
        if count > 0:
            avg_audit_time = round(total_hours / count, 2)

    top_referenced = (
        db.query(LegalCase.id, LegalCase.title, LegalCase.view_count)
        .filter(LegalCase.is_deleted == False, LegalCase.status == "published")
        .order_by(LegalCase.view_count.desc())
        .limit(10)
        .all()
    )

    return {
        "category_distribution": [
            {"category": c, "count": n} for c, n in category_stats if c
        ],
        "audit_efficiency": {
            "last_7_days": {action: count for action, count in audit_logs_recent},
            "avg_audit_hours": avg_audit_time,
        },
        "top_referenced": [
            {"id": cid, "title": t, "view_count": vc} for cid, t, vc in top_referenced
        ],
    }


@router.get("/quality/duplicates", dependencies=[Depends(require_domain_role("archive", roles=["archive_admin"]))])
async def detect_duplicates(
    threshold: int = Query(80, ge=50, le=100, description="相似度阈值"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """重复案例检测 - 基于标题相似度"""
    cases = (
        db.query(LegalCase.id, LegalCase.title, LegalCase.case_type, LegalCase.category)
        .filter(LegalCase.is_deleted == False)
        .order_by(LegalCase.created_at.desc())
        .limit(500)
        .all()
    )

    duplicates = []
    seen = set()

    for i, case_a in enumerate(cases):
        for j in range(i + 1, len(cases)):
            case_b = cases[j]
            pair_key = (min(case_a.id, case_b.id), max(case_a.id, case_b.id))
            if pair_key in seen:
                continue

            title_a = case_a.title or ""
            title_b = case_b.title or ""

            if not title_a or not title_b:
                continue

            set_a = set(title_a)
            set_b = set(title_b)
            intersection = len(set_a & set_b)
            union = len(set_a | set_b)
            similarity = int((intersection / union) * 100) if union > 0 else 0

            if similarity >= threshold:
                seen.add(pair_key)
                duplicates.append({
                    "case_a": {"id": case_a.id, "title": case_a.title, "category": case_a.category},
                    "case_b": {"id": case_b.id, "title": case_b.title, "category": case_b.category},
                    "similarity": similarity,
                })

                if len(duplicates) >= limit:
                    break
        if len(duplicates) >= limit:
            break

    return {
        "total_found": len(duplicates),
        "threshold": threshold,
        "duplicates": duplicates,
    }


@router.get("/audit-logs", dependencies=[Depends(require_domain_role("archive", roles=["archive_admin"]))])
async def get_audit_logs(
    case_id: Optional[int] = Query(None, description="按案例ID筛选"),
    action: Optional[str] = Query(None, description="按操作类型筛选"),
    operator_id: Optional[int] = Query(None, description="按操作人筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_admin_user),
):
    """审计日志查询"""
    query = db.query(CaseAuditLog)

    if case_id is not None:
        query = query.filter(CaseAuditLog.case_id == case_id)
    if action:
        valid_actions = {"submit", "approve", "reject", "publish", "archive"}
        if action not in valid_actions:
            raise HTTPException(status_code=400, detail=f"无效操作类型: {action}")
        query = query.filter(CaseAuditLog.action == action)
    if operator_id is not None:
        query = query.filter(CaseAuditLog.operator_id == operator_id)
    if start_date:
        query = query.filter(CaseAuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(CaseAuditLog.created_at <= end_date)

    total = query.count()
    logs = (
        query.order_by(CaseAuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": log.id,
                "case_id": log.case_id,
                "operator_id": log.operator_id,
                "operator_name": log.operator_name,
                "action": log.action,
                "from_status": log.from_status,
                "to_status": log.to_status,
                "comment": log.comment,
                "extra_data": log.extra_data,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }
