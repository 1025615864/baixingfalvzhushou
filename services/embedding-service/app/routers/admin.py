import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker, Session

from app.config.settings import get_settings
from app.models.admin import Base, EmbeddingCallStats, ServiceQuota
from app.services.embedding_service import get_embedding_service

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi import status
    from typing import List, Set

    _security = HTTPBearer(auto_error=False)

    GLOBAL_ADMIN_ROLES = {"super_admin", "admin"}

    DOMAIN_ROLES: dict[str, Set[str]] = {
        "global": {"super_admin", "admin"},
        "embedding": {"embedding_admin"},
    }

    class AdminUser:
        def __init__(self, user_id: int = 0, role: str = "admin", permissions: Optional[List[str]] = None):
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供认证凭据",
            )
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

router = APIRouter()

settings = get_settings()

_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./embedding_admin.db")

engine = create_engine(_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DashboardResponse(BaseModel):
    today_calls: int
    avg_latency_ms: float
    error_rate: float
    quota_usage_rate: float
    model_name: str
    model_loaded: bool


class StatsItem(BaseModel):
    stat_date: str
    model_name: str
    call_count: int
    avg_latency_ms: float
    error_count: int
    total_tokens: int


class StatsResponse(BaseModel):
    total: int
    items: List[StatsItem]


class QuotaItem(BaseModel):
    id: int
    service_name: str
    daily_limit: int
    used_count: int
    reset_date: str


class QuotaListResponse(BaseModel):
    total: int
    items: List[QuotaItem]


class QuotaUpdateRequest(BaseModel):
    daily_limit: Optional[int] = None
    used_count: Optional[int] = None


class QuotaUpdateResponse(BaseModel):
    id: int
    service_name: str
    daily_limit: int
    used_count: int
    reset_date: str


class HealthModelStatus(BaseModel):
    model_name: str
    loaded: bool
    device: str
    dimension: int


class HealthResponse(BaseModel):
    status: str
    models: List[HealthModelStatus]
    uptime_seconds: Optional[float] = None


class AuditLogItem(BaseModel):
    id: int
    service: str
    action: str
    resource_type: str
    resource_id: int
    user_id: Optional[int]
    created_at: Optional[str]


class AuditLogResponse(BaseModel):
    total: int
    items: List[AuditLogItem]


_start_time = datetime.now()


@router.get("/dashboard", response_model=DashboardResponse, dependencies=[Depends(require_domain_role("embedding", roles=["embedding_admin"]))])
async def get_dashboard(
    admin: AdminUser = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    today = datetime.now().strftime("%Y-%m-%d")

    today_stats = (
        db.query(EmbeddingCallStats)
        .filter(EmbeddingCallStats.stat_date == today)
        .all()
    )

    today_calls = sum(s.call_count for s in today_stats)
    total_latency = sum(s.avg_latency_ms * s.call_count for s in today_stats if s.call_count > 0)
    avg_latency = (total_latency / today_calls) if today_calls > 0 else 0.0

    total_errors = sum(s.error_count for s in today_stats)
    error_rate = (total_errors / today_calls * 100) if today_calls > 0 else 0.0

    quota = db.query(ServiceQuota).filter(ServiceQuota.service_name == "embedding-service").first()
    quota_usage_rate = 0.0
    if quota and quota.daily_limit > 0:
        quota_usage_rate = round(quota.used_count / quota.daily_limit * 100, 2)

    service = get_embedding_service()

    return DashboardResponse(
        today_calls=today_calls,
        avg_latency_ms=round(avg_latency, 2),
        error_rate=round(error_rate, 2),
        quota_usage_rate=quota_usage_rate,
        model_name=service.model_name,
        model_loaded=service.is_model_loaded(),
    )


@router.get("/stats", response_model=StatsResponse, dependencies=[Depends(require_domain_role("embedding", roles=["embedding_admin"]))])
async def get_stats(
    model_name: Optional[str] = Query(None, description="按模型名称筛选"),
    stat_date: Optional[str] = Query(None, description="按日期筛选 (YYYY-MM-DD)"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    query = db.query(EmbeddingCallStats)

    if model_name:
        query = query.filter(EmbeddingCallStats.model_name == model_name)
    if stat_date:
        query = query.filter(EmbeddingCallStats.stat_date == stat_date)
    if start_date:
        query = query.filter(EmbeddingCallStats.stat_date >= start_date)
    if end_date:
        query = query.filter(EmbeddingCallStats.stat_date <= end_date)

    total = query.count()
    items = (
        query.order_by(desc(EmbeddingCallStats.stat_date))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return StatsResponse(
        total=total,
        items=[
            StatsItem(
                stat_date=s.stat_date,
                model_name=s.model_name,
                call_count=s.call_count,
                avg_latency_ms=float(s.avg_latency_ms),
                error_count=s.error_count,
                total_tokens=s.total_tokens,
            )
            for s in items
        ],
    )


@router.get("/quotas", response_model=QuotaListResponse, dependencies=[Depends(require_domain_role("embedding", roles=["embedding_admin"]))])
async def get_quotas(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    query = db.query(ServiceQuota)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return QuotaListResponse(
        total=total,
        items=[
            QuotaItem(
                id=q.id,
                service_name=q.service_name,
                daily_limit=q.daily_limit,
                used_count=q.used_count,
                reset_date=q.reset_date,
            )
            for q in items
        ],
    )


@router.put("/quotas/{quota_id}", response_model=QuotaUpdateResponse, dependencies=[Depends(require_domain_role("embedding", roles=["embedding_admin"]))])
async def update_quota(
    quota_id: int,
    request: QuotaUpdateRequest,
    admin: AdminUser = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    quota = db.query(ServiceQuota).filter(ServiceQuota.id == quota_id).first()
    if not quota:
        raise HTTPException(status_code=404, detail="配额不存在")

    if request.daily_limit is not None:
        quota.daily_limit = request.daily_limit
    if request.used_count is not None:
        quota.used_count = request.used_count

    quota.updated_at = datetime.now()
    db.commit()
    db.refresh(quota)

    return QuotaUpdateResponse(
        id=quota.id,
        service_name=quota.service_name,
        daily_limit=quota.daily_limit,
        used_count=quota.used_count,
        reset_date=quota.reset_date,
    )


@router.get("/health", response_model=HealthResponse, dependencies=[Depends(require_domain_role("embedding", roles=["embedding_admin"]))])
async def get_admin_health(
    admin: AdminUser = Depends(get_admin_user),
):
    service = get_embedding_service()
    uptime = (datetime.now() - _start_time).total_seconds()

    return HealthResponse(
        status="healthy" if service.is_model_loaded() else "degraded",
        models=[
            HealthModelStatus(
                model_name=service.model_name,
                loaded=service.is_model_loaded(),
                device=service.device,
                dimension=service.embedding_dim,
            )
        ],
        uptime_seconds=uptime,
    )


@router.get("/audit-logs", response_model=AuditLogResponse, dependencies=[Depends(require_domain_role("embedding", roles=["embedding_admin"]))])
async def get_audit_logs(
    service_name: Optional[str] = Query(None, description="按服务名称筛选"),
    action: Optional[str] = Query(None, description="按操作类型筛选"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    try:
        from services.common.models.audit_log import AuditLog
    except ImportError:
        return AuditLogResponse(total=0, items=[])

    query = db.query(AuditLog)

    if service_name:
        query = query.filter(AuditLog.service == service_name)
    if action:
        query = query.filter(AuditLog.action == action)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    total = query.count()
    logs = (
        query.order_by(desc(AuditLog.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AuditLogResponse(
        total=total,
        items=[
            AuditLogItem(
                id=log.id,
                service=log.service,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                user_id=log.user_id,
                created_at=log.created_at.isoformat() if log.created_at else None,
            )
            for log in logs
        ],
    )
