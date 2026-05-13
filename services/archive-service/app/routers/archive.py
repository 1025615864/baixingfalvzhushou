"""案例CRUD API - 带鉴权"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.archive import LegalCase, CaseCategory
from app.services.archive_service import ArchiveService
from app.dependencies.auth import get_current_user, UserContext, check_permission
try:
    from services.common.services.audit_service import AuditService
except ImportError:
    class AuditService:
        def __init__(self, db=None):
            self.db = db
        async def log_action(self, *args, **kwargs):
            pass
from app.middleware.audit_middleware import get_audit_context

router = APIRouter(prefix="/api/v1/archive", tags=["案例管理"])


class CaseCreateRequest(BaseModel):
    case_number: Optional[str] = None
    case_type: str
    title: str
    facts: str
    legal_basis: Optional[str] = None
    judgment: Optional[str] = None
    result: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    court: Optional[str] = None
    court_level: Optional[str] = None
    judge_date: Optional[datetime] = None
    cause_of_action: Optional[str] = None
    judgment_result: Optional[str] = None
    key_points: Optional[str] = None
    applicable_laws: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    is_guiding_case: bool = False
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    weight: int = 1
    created_by: Optional[int] = None
    metadata: Optional[dict] = None


class CaseUpdateRequest(BaseModel):
    case_number: Optional[str] = None
    case_type: Optional[str] = None
    title: Optional[str] = None
    facts: Optional[str] = None
    legal_basis: Optional[str] = None
    judgment: Optional[str] = None
    result: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    court: Optional[str] = None
    court_level: Optional[str] = None
    judge_date: Optional[datetime] = None
    cause_of_action: Optional[str] = None
    judgment_result: Optional[str] = None
    key_points: Optional[str] = None
    applicable_laws: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    is_guiding_case: Optional[bool] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    weight: Optional[int] = None
    updated_by: Optional[int] = None
    metadata: Optional[dict] = None


class CaseResponse(BaseModel):
    id: int
    case_number: Optional[str]
    case_type: str
    title: str
    facts: str
    legal_basis: Optional[str]
    judgment: Optional[str]
    result: Optional[str]
    category: Optional[str]
    keywords: Optional[str]
    court: Optional[str]
    court_level: Optional[str]
    judge_date: Optional[datetime]
    cause_of_action: Optional[str]
    judgment_result: Optional[str]
    key_points: Optional[str]
    applicable_laws: Optional[str]
    source: Optional[str]
    source_url: Optional[str]
    is_guiding_case: bool
    is_vectorized: bool
    vector_indexed: bool
    status: str
    version: int
    effective_date: Optional[datetime]
    expiry_date: Optional[datetime]
    view_count: int
    weight: int
    is_active: bool
    created_by: Optional[int]
    updated_by: Optional[int]
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


def get_archive_service(db: Session = Depends(get_db)) -> ArchiveService:
    return ArchiveService(db)


def _get_audit_context(request: Request):
    return get_audit_context()


def _check_archive_permission(user: UserContext, action: str):
    """检查档案库操作权限"""
    if not check_permission(user.role, "archive", action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"您没有权限执行此操作: {action}"
        )


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    request: CaseCreateRequest,
    http_request: Request,
    service: ArchiveService = Depends(get_archive_service),
    current_user: UserContext = Depends(get_current_user)
):
    """创建案例 - 需要archive:create权限"""
    _check_archive_permission(current_user, "create")

    try:
        case = service.create_case(request)

        audit_ctx = _get_audit_context(http_request)
        audit_service = AuditService(service.db)
        audit_service.log_action(
            service="archive",
            action="create",
            resource_type="case",
            resource_id=case.id,
            user_id=current_user.user_id,
            user_role=current_user.role,
            ip_address=audit_ctx.ip_address if audit_ctx else None,
            user_agent=audit_ctx.user_agent if audit_ctx else None,
            request_id=audit_ctx.request_id if audit_ctx else None,
            changes={"status": "draft"},
        )

        return case
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    service: ArchiveService = Depends(get_archive_service)
):
    """获取案例详情 - 需要登录"""
    case = service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    return case


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    request: CaseUpdateRequest,
    http_request: Request,
    service: ArchiveService = Depends(get_archive_service),
    current_user: UserContext = Depends(get_current_user)
):
    """更新案例 - 需要archive:update权限"""
    _check_archive_permission(current_user, "update")

    try:
        old_case = service.get_case(case_id)
        if not old_case:
            raise HTTPException(status_code=404, detail="案例不存在")

        old_data = {k: getattr(old_case, k) for k in request.model_dump(exclude_unset=True).keys()}

        case = service.update_case(case_id, request)

        audit_ctx = _get_audit_context(http_request)
        audit_service = AuditService(service.db)
        audit_service.log_action(
            service="archive",
            action="update",
            resource_type="case",
            resource_id=case_id,
            user_id=current_user.user_id,
            user_role=current_user.role,
            ip_address=audit_ctx.ip_address if audit_ctx else None,
            user_agent=audit_ctx.user_agent if audit_ctx else None,
            request_id=audit_ctx.request_id if audit_ctx else None,
            changes={"before": old_data, "after": request.model_dump(exclude_unset=True)},
        )

        return case
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: int,
    http_request: Request,
    service: ArchiveService = Depends(get_archive_service),
    current_user: UserContext = Depends(get_current_user)
):
    """删除案例(软删除) - 需要archive:delete权限"""
    _check_archive_permission(current_user, "delete")

    try:
        old_case = service.get_case(case_id)
        if not old_case:
            raise HTTPException(status_code=404, detail="案例不存在")

        old_data = {"status": old_case.status, "is_deleted": old_case.is_deleted}

        service.delete_case(case_id)

        audit_ctx = _get_audit_context(http_request)
        audit_service = AuditService(service.db)
        audit_service.log_action(
            service="archive",
            action="delete",
            resource_type="case",
            resource_id=case_id,
            user_id=current_user.user_id,
            user_role=current_user.role,
            ip_address=audit_ctx.ip_address if audit_ctx else None,
            user_agent=audit_ctx.user_agent if audit_ctx else None,
            request_id=audit_ctx.request_id if audit_ctx else None,
            changes={"before": old_data, "after": {"is_deleted": True}},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{case_id}/publish", response_model=CaseResponse)
async def publish_case(
    case_id: int,
    reviewed_by: int = None,
    http_request: Request = None,
    service: ArchiveService = Depends(get_archive_service),
    current_user: UserContext = Depends(get_current_user)
):
    """发布案例 - 需要archive:publish权限"""
    _check_archive_permission(current_user, "publish")

    try:
        old_case = service.get_case(case_id)
        if not old_case:
            raise HTTPException(status_code=404, detail="案例不存在")

        old_data = {"status": old_case.status}

        case = service.publish_case(case_id, reviewed_by or current_user.user_id)

        if http_request:
            audit_ctx = _get_audit_context(http_request)
            audit_service = AuditService(service.db)
            audit_service.log_action(
                service="archive",
                action="publish",
                resource_type="case",
                resource_id=case_id,
                user_id=current_user.user_id,
                user_role=current_user.role,
                ip_address=audit_ctx.ip_address if audit_ctx else None,
                user_agent=audit_ctx.user_agent if audit_ctx else None,
                request_id=audit_ctx.request_id if audit_ctx else None,
                changes={"before": old_data, "after": {"status": "published"}},
            )

        return case
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{case_id}/unpublish", response_model=CaseResponse)
async def unpublish_case(
    case_id: int,
    http_request: Request = None,
    service: ArchiveService = Depends(get_archive_service),
    current_user: UserContext = Depends(get_current_user)
):
    """下线案例 - 需要archive:publish权限"""
    _check_archive_permission(current_user, "publish")

    try:
        old_case = service.get_case(case_id)
        if not old_case:
            raise HTTPException(status_code=404, detail="案例不存在")

        old_data = {"status": old_case.status}

        case = service.unpublish_case(case_id)

        if http_request:
            audit_ctx = _get_audit_context(http_request)
            audit_service = AuditService(service.db)
            audit_service.log_action(
                service="archive",
                action="unpublish",
                resource_type="case",
                resource_id=case_id,
                user_id=current_user.user_id,
                user_role=current_user.role,
                ip_address=audit_ctx.ip_address if audit_ctx else None,
                user_agent=audit_ctx.user_agent if audit_ctx else None,
                request_id=audit_ctx.request_id if audit_ctx else None,
                changes={"before": old_data, "after": {"status": "archived"}},
            )

        return case
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{case_id}/submit-review", response_model=CaseResponse)
async def submit_for_review(
    case_id: int,
    http_request: Request = None,
    service: ArchiveService = Depends(get_archive_service),
    current_user: UserContext = Depends(get_current_user)
):
    """提交案例审核 - 需要archive:create权限"""
    _check_archive_permission(current_user, "create")

    try:
        old_case = service.get_case(case_id)
        if not old_case:
            raise HTTPException(status_code=404, detail="案例不存在")

        old_data = {"status": old_case.status}

        case = service.submit_for_review(case_id)

        if http_request:
            audit_ctx = _get_audit_context(http_request)
            audit_service = AuditService(service.db)
            audit_service.log_action(
                service="archive",
                action="submit_review",
                resource_type="case",
                resource_id=case_id,
                user_id=current_user.user_id,
                user_role=current_user.role,
                ip_address=audit_ctx.ip_address if audit_ctx else None,
                user_agent=audit_ctx.user_agent if audit_ctx else None,
                request_id=audit_ctx.request_id if audit_ctx else None,
                changes={"before": old_data, "after": {"status": "pending_review"}},
            )

        return case
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
