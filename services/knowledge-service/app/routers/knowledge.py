"""知识CRUD API - 带鉴权"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.knowledge import LegalKnowledge
from app.services.knowledge_service import KnowledgeService
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

router = APIRouter(prefix="/api/v1/knowledge", tags=["知识管理"])


class KnowledgeCreateRequest(BaseModel):
    knowledge_type: str
    title: str
    article_number: Optional[str] = None
    content: str
    summary: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    source: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    law_number: Optional[str] = None
    jurisdiction: Optional[str] = None
    weight: int = 1
    created_by: Optional[int] = None
    metadata: Optional[dict] = None


class KnowledgeUpdateRequest(BaseModel):
    knowledge_type: Optional[str] = None
    title: Optional[str] = None
    article_number: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    source: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    law_number: Optional[str] = None
    jurisdiction: Optional[str] = None
    weight: Optional[int] = None
    updated_by: Optional[int] = None
    metadata: Optional[dict] = None


class KnowledgeResponse(BaseModel):
    id: int
    knowledge_type: str
    title: str
    article_number: Optional[str]
    content: str
    summary: Optional[str]
    category: Optional[str]
    keywords: Optional[str]
    source: Optional[str]
    is_vectorized: bool
    vector_indexed: bool
    status: str
    version: int
    effective_date: Optional[datetime]
    expiry_date: Optional[datetime]
    law_number: Optional[str]
    jurisdiction: Optional[str]
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


def _get_audit_context(request: Request):
    return get_audit_context()


def _check_knowledge_permission(user: UserContext, action: str):
    """检查知识库操作权限"""
    if not check_permission(user.role, "knowledge", action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"您没有权限执行此操作: {action}"
        )


@router.post("", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge(
    request: KnowledgeCreateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    """创建知识 - 需要knowledge:create权限"""
    _check_knowledge_permission(current_user, "create")

    service = KnowledgeService(db)
    knowledge = service.create_knowledge(request)

    audit_ctx = _get_audit_context(http_request)
    audit_service = AuditService(db)
    audit_service.log_action(
        service="knowledge",
        action="create",
        resource_type="knowledge",
        resource_id=knowledge.id,
        user_id=current_user.user_id,
        user_role=current_user.role,
        ip_address=audit_ctx.ip_address if audit_ctx else None,
        user_agent=audit_ctx.user_agent if audit_ctx else None,
        request_id=audit_ctx.request_id if audit_ctx else None,
        changes={"status": "draft"},
    )

    return knowledge


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    """获取知识详情 - 需要登录"""
    service = KnowledgeService(db)
    knowledge = service.get_knowledge(knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识不存在")
    return knowledge


@router.put("/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge(
    knowledge_id: int,
    request: KnowledgeUpdateRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    """更新知识 - 需要knowledge:update权限"""
    _check_knowledge_permission(current_user, "update")

    service = KnowledgeService(db)
    old_knowledge = service.get_knowledge(knowledge_id)
    if not old_knowledge:
        raise HTTPException(status_code=404, detail="知识不存在")

    old_data = {k: getattr(old_knowledge, k) for k in request.model_dump(exclude_unset=True).keys()}

    knowledge = service.update_knowledge(knowledge_id, request)
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识不存在")

    audit_ctx = _get_audit_context(http_request)
    audit_service = AuditService(db)
    audit_service.log_action(
        service="knowledge",
        action="update",
        resource_type="knowledge",
        resource_id=knowledge_id,
        user_id=current_user.user_id,
        user_role=current_user.role,
        ip_address=audit_ctx.ip_address if audit_ctx else None,
        user_agent=audit_ctx.user_agent if audit_ctx else None,
        request_id=audit_ctx.request_id if audit_ctx else None,
        changes={"before": old_data, "after": request.model_dump(exclude_unset=True)},
    )

    return knowledge


@router.delete("/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge(
    knowledge_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    """删除知识(软删除) - 需要knowledge:delete权限"""
    _check_knowledge_permission(current_user, "delete")

    service = KnowledgeService(db)
    knowledge = service.get_knowledge(knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="知识不存在")

    old_data = {"status": knowledge.status, "is_deleted": knowledge.is_deleted}

    result = await service.delete_knowledge(knowledge_id)
    if not result:
        raise HTTPException(status_code=404, detail="知识不存在")

    audit_ctx = _get_audit_context(http_request)
    audit_service = AuditService(db)
    audit_service.log_action(
        service="knowledge",
        action="delete",
        resource_type="knowledge",
        resource_id=knowledge_id,
        user_id=current_user.user_id,
        user_role=current_user.role,
        ip_address=audit_ctx.ip_address if audit_ctx else None,
        user_agent=audit_ctx.user_agent if audit_ctx else None,
        request_id=audit_ctx.request_id if audit_ctx else None,
        changes={"before": old_data, "after": {"is_deleted": True}},
    )


@router.post("/{knowledge_id}/publish", response_model=KnowledgeResponse)
async def publish_knowledge(
    knowledge_id: int,
    reviewed_by: int = None,
    http_request: Request = None,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    """发布知识 - 需要knowledge:publish权限"""
    _check_knowledge_permission(current_user, "publish")

    service = KnowledgeService(db)
    try:
        old_knowledge = service.get_knowledge(knowledge_id)
        if not old_knowledge:
            raise HTTPException(status_code=404, detail="知识不存在")

        old_data = {"status": old_knowledge.status}

        knowledge = await service.publish_knowledge(knowledge_id, reviewed_by or current_user.user_id)
        if not knowledge:
            raise HTTPException(status_code=404, detail="知识不存在")

        if http_request:
            audit_ctx = _get_audit_context(http_request)
            audit_service = AuditService(db)
            audit_service.log_action(
                service="knowledge",
                action="publish",
                resource_type="knowledge",
                resource_id=knowledge_id,
                user_id=current_user.user_id,
                user_role=current_user.role,
                ip_address=audit_ctx.ip_address if audit_ctx else None,
                user_agent=audit_ctx.user_agent if audit_ctx else None,
                request_id=audit_ctx.request_id if audit_ctx else None,
                changes={"before": old_data, "after": {"status": "published"}},
            )

        return knowledge
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{knowledge_id}/unpublish", response_model=KnowledgeResponse)
async def unpublish_knowledge(
    knowledge_id: int,
    http_request: Request = None,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    """下线知识 - 需要knowledge:publish权限"""
    _check_knowledge_permission(current_user, "publish")

    service = KnowledgeService(db)
    try:
        old_knowledge = service.get_knowledge(knowledge_id)
        if not old_knowledge:
            raise HTTPException(status_code=404, detail="知识不存在")

        old_data = {"status": old_knowledge.status}

        knowledge = await service.unpublish_knowledge(knowledge_id)
        if not knowledge:
            raise HTTPException(status_code=404, detail="知识不存在")

        if http_request:
            audit_ctx = _get_audit_context(http_request)
            audit_service = AuditService(db)
            audit_service.log_action(
                service="knowledge",
                action="unpublish",
                resource_type="knowledge",
                resource_id=knowledge_id,
                user_id=current_user.user_id,
                user_role=current_user.role,
                ip_address=audit_ctx.ip_address if audit_ctx else None,
                user_agent=audit_ctx.user_agent if audit_ctx else None,
                request_id=audit_ctx.request_id if audit_ctx else None,
                changes={"before": old_data, "after": {"status": "archived"}},
            )

        return knowledge
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{knowledge_id}/submit-review", response_model=KnowledgeResponse)
async def submit_for_review(
    knowledge_id: int,
    http_request: Request = None,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user)
):
    """提交知识审核 - 需要knowledge:create权限"""
    _check_knowledge_permission(current_user, "create")

    service = KnowledgeService(db)
    try:
        old_knowledge = service.get_knowledge(knowledge_id)
        if not old_knowledge:
            raise HTTPException(status_code=404, detail="知识不存在")

        old_data = {"status": old_knowledge.status}

        knowledge = service.submit_for_review(knowledge_id)
        if not knowledge:
            raise HTTPException(status_code=404, detail="知识不存在")

        if http_request:
            audit_ctx = _get_audit_context(http_request)
            audit_service = AuditService(db)
            audit_service.log_action(
                service="knowledge",
                action="submit_review",
                resource_type="knowledge",
                resource_id=knowledge_id,
                user_id=current_user.user_id,
                user_role=current_user.role,
                ip_address=audit_ctx.ip_address if audit_ctx else None,
                user_agent=audit_ctx.user_agent if audit_ctx else None,
                request_id=audit_ctx.request_id if audit_ctx else None,
                changes={"before": old_data, "after": {"status": "pending_review"}},
            )

        return knowledge
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
