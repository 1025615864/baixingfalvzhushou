"""新闻管理路由 - 管理员审核/编辑分配/统计/批量操作"""
from typing import List, Optional

import logging

from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.news_admin_service import news_admin_service
from app.database import get_db, AsyncSession

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi import status as http_status
    import os

    security = HTTPBearer(auto_error=False)

    class AdminUser:
        def __init__(self, user_id: int = 0, role: str = "admin", permissions: Optional[list] = None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in {"super_admin", "admin"}

    async def get_admin_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> AdminUser:
        if not credentials:
            raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="未提供认证凭据")
        if os.getenv("DISABLE_AUTH", "").lower() in {"1", "true", "yes"}:
            return AdminUser(user_id=1, role="super_admin")
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="认证服务不可用")

    def require_domain_role(domain: str, roles: Optional[List[str]] = None):
        async def domain_checker(admin: AdminUser = Depends(get_admin_user)):
            if admin.is_super_admin:
                return admin
            if roles and admin.role not in roles:
                raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=f"需要角色: {', '.join(roles)}，当前角色: {admin.role}")
            return admin
        return domain_checker

logger = logging.getLogger(__name__)

router = APIRouter()


class SubmitReviewRequest(BaseModel):
    operator_id: int = Field(..., ge=1)
    operator_name: Optional[str] = None


class AssignEditorRequest(BaseModel):
    editor_id: int = Field(..., ge=1)
    editor_name: Optional[str] = None
    assigned_by: int = Field(..., ge=1)
    assigned_by_name: Optional[str] = None


class ReviewNewsRequest(BaseModel):
    reviewer_id: int = Field(..., ge=1)
    reviewer_name: Optional[str] = None
    action: str = Field(..., pattern="^(approve|reject)$")
    comment: Optional[str] = None


class PublishRequest(BaseModel):
    operator_id: int = Field(..., ge=1)
    operator_name: Optional[str] = None


class BatchStatusRequest(BaseModel):
    news_ids: List[int] = Field(..., min_length=1, max_length=100)
    target_status: str = Field(..., pattern="^(review|approved|published|archived|draft|rejected)$")
    operator_id: int = Field(..., ge=1)
    operator_name: Optional[str] = None


class AuditQueueResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int


class AuditLogResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int


@router.get("/audit-queue", response_model=AuditQueueResponse, dependencies=[Depends(require_domain_role("news", roles=["news_admin"]))])
async def get_audit_queue(
    status: Optional[str] = Query(None, pattern="^(review|approved|rejected)$"),
    category_id: Optional[int] = Query(None, ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取审核队列"""
    items, total = await news_admin_service.get_audit_queue(
        db, status=status, category_id=category_id, page=page, page_size=page_size,
    )
    return AuditQueueResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/{news_id}/submit-review", dependencies=[Depends(require_domain_role("news", roles=["news_ops"]))])
async def submit_for_review(
    news_id: int,
    body: SubmitReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """提交新闻审核（draft → review）"""
    try:
        news = await news_admin_service.submit_for_review(
            db, news_id, body.operator_id, body.operator_name,
        )
        await db.commit()
        return {"message": "已提交审核", "news_id": news_id, "status": news.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{news_id}/assign-editor", dependencies=[Depends(require_domain_role("news", roles=["news_admin"]))])
async def assign_editor(
    news_id: int,
    body: AssignEditorRequest,
    db: AsyncSession = Depends(get_db),
):
    """分配编辑审核"""
    try:
        assignment = await news_admin_service.assign_editor(
            db, news_id, body.editor_id, body.editor_name,
            body.assigned_by, body.assigned_by_name,
        )
        await db.commit()
        return {
            "message": "编辑分配成功",
            "assignment_id": assignment.id,
            "editor_id": body.editor_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{news_id}/review", dependencies=[Depends(require_domain_role("news", roles=["news_ops"]))])
async def review_news(
    news_id: int,
    body: ReviewNewsRequest,
    db: AsyncSession = Depends(get_db),
):
    """审核新闻（review → approved/rejected）"""
    try:
        news = await news_admin_service.review_news(
            db, news_id, body.reviewer_id, body.reviewer_name,
            body.action, body.comment,
        )
        await db.commit()
        return {"message": "审核完成", "news_id": news_id, "status": news.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{news_id}/publish", dependencies=[Depends(require_domain_role("news", roles=["news_ops"]))])
async def publish_approved_news(
    news_id: int,
    body: PublishRequest,
    db: AsyncSession = Depends(get_db),
):
    """发布已审核通过的新闻（approved → published）"""
    try:
        news = await news_admin_service.publish_approved_news(
            db, news_id, body.operator_id, body.operator_name,
        )
        await db.commit()

        try:
            from app.events.kafka_producer import publish_news_published
            await publish_news_published(
                news_id=str(news_id),
                title=news.title,
                author_id=str(body.operator_id),
                category=str(news.category_id or ""),
            )
        except Exception as e:
            logger.error(f"Failed to publish news event: {e}")

        return {"message": "发布成功", "news_id": news_id, "status": news.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch/status", dependencies=[Depends(require_domain_role("news", roles=["news_ops"]))])
async def batch_update_status(
    body: BatchStatusRequest,
    db: AsyncSession = Depends(get_db),
):
    """批量更新新闻状态"""
    result = await news_admin_service.batch_update_status(
        db, body.news_ids, body.target_status,
        body.operator_id, body.operator_name,
    )
    await db.commit()
    return result


@router.get("/dashboard", dependencies=[Depends(require_domain_role("news", roles=["news_admin"]))])
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """获取管理看板统计数据"""
    stats = await news_admin_service.get_dashboard_stats(db)
    return stats


@router.get("/audit-logs", response_model=AuditLogResponse, dependencies=[Depends(require_domain_role("news", roles=["news_admin"]))])
async def get_audit_logs(
    news_id: Optional[int] = Query(None, ge=1),
    operator_id: Optional[int] = Query(None, ge=1),
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取审核日志"""
    items, total = await news_admin_service.get_audit_logs(
        db, news_id=news_id, operator_id=operator_id,
        action=action, page=page, page_size=page_size,
    )
    return AuditLogResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/editor-workload", dependencies=[Depends(require_domain_role("news", roles=["news_admin"]))])
async def get_editor_workload(
    db: AsyncSession = Depends(get_db),
):
    """获取编辑工作量统计"""
    workload = await news_admin_service.get_editor_workload(db)
    return {"editors": workload}
