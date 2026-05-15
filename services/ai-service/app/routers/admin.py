"""AI服务管理路由 - 管理员仪表盘与配置"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    from fastapi import Request
    class AdminUser:
        def __init__(self, user_id: int = 0, role: str = "admin", permissions=None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in {"super_admin", "admin"}
    async def get_admin_user(request: Request = None):
        if request:
            user_id = int(request.headers.get("X-Admin-User-Id", "0"))
            role = request.headers.get("X-Admin-Role", "admin")
            permissions = request.headers.get("X-Admin-Permissions", "").split(",")
            return AdminUser(user_id=user_id, role=role, permissions=permissions)
        return AdminUser()
    def require_domain_role(domain: str, roles=None):
        async def _checker(admin: AdminUser = Depends(get_admin_user)):
            if admin.is_super_admin:
                return admin
            if roles and admin.role not in roles:
                raise HTTPException(status_code=403, detail=f"需要角色: {', '.join(roles)}")
            return admin
        return _checker

admin_router = APIRouter(
    prefix="/api/admin",
    tags=["AI管理"],
    dependencies=[Depends(require_domain_role("ai", roles=["ai_admin"]))],
)


class DashboardResponse(BaseModel):
    total_conversations: int
    total_tokens: int
    total_cost: float
    avg_quality_score: float


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


class CostStatsResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    total_cost: float
    by_model: List[dict]
    daily_cost: List[dict]


class QualityReportResponse(BaseModel):
    period: str
    total_queries: int
    rag_hit_rate: float
    avg_latency_ms: float
    quality_score: float
    top_issues: List[dict]


class ConversationItem(BaseModel):
    id: str
    user_id: Optional[int]
    created_at: str
    message_count: int
    total_tokens: int
    quality_score: Optional[float]


class ConversationListResponse(BaseModel):
    items: List[ConversationItem]
    total: int
    page: int
    page_size: int


class RetrievalStatsResponse(BaseModel):
    total_queries: int
    hit_rate: float
    avg_latency_ms: float
    by_level: List[dict]


class AuditLogItem(BaseModel):
    id: int
    action: str
    resource_type: str
    resource_id: int
    user_id: Optional[int]
    created_at: str


class AuditLogListResponse(BaseModel):
    items: List[AuditLogItem]
    total: int
    page: int
    page_size: int


class ConfigUpdateRequest(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


class ConfigUpdateResponse(BaseModel):
    config_id: int
    key: str
    value: str
    updated_at: str


@admin_router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    return DashboardResponse(
        total_conversations=0,
        total_tokens=0,
        total_cost=0.0,
        avg_quality_score=0.0,
    )


@admin_router.get("/token-stats", response_model=TokenStatsResponse)
async def get_token_stats(
    period: str = Query("7d", pattern="^(1d|7d|30d)$"),
):
    now = datetime.now()
    return TokenStatsResponse(
        period=period,
        start_date=now.strftime("%Y-%m-%d"),
        end_date=now.strftime("%Y-%m-%d"),
        total_requests=0,
        total_prompt_tokens=0,
        total_completion_tokens=0,
        total_tokens=0,
        avg_latency_ms=0.0,
        by_model=[],
    )


@admin_router.get("/cost-stats", response_model=CostStatsResponse)
async def get_cost_stats(
    period: str = Query("7d", pattern="^(1d|7d|30d)$"),
):
    now = datetime.now()
    return CostStatsResponse(
        period=period,
        start_date=now.strftime("%Y-%m-%d"),
        end_date=now.strftime("%Y-%m-%d"),
        total_cost=0.0,
        by_model=[],
        daily_cost=[],
    )


@admin_router.get("/quality/report", response_model=QualityReportResponse)
async def get_quality_report(
    period: str = Query("7d", pattern="^(1d|7d|30d)$"),
):
    return QualityReportResponse(
        period=period,
        total_queries=0,
        rag_hit_rate=0.0,
        avg_latency_ms=0.0,
        quality_score=0.0,
        top_issues=[],
    )


@admin_router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    return ConversationListResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
    )


@admin_router.get("/retrieval/stats", response_model=RetrievalStatsResponse)
async def get_retrieval_stats(
    period: str = Query("7d", pattern="^(1d|7d|30d)$"),
):
    return RetrievalStatsResponse(
        total_queries=0,
        hit_rate=0.0,
        avg_latency_ms=0.0,
        by_level=[],
    )


@admin_router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    return AuditLogListResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
    )


@admin_router.put("/config/{config_id}", response_model=ConfigUpdateResponse)
async def update_config(
    config_id: int,
    request: ConfigUpdateRequest,
):
    now = datetime.now()
    return ConfigUpdateResponse(
        config_id=config_id,
        key=request.key,
        value=request.value,
        updated_at=now.strftime("%Y-%m-%dT%H:%M:%S"),
    )
