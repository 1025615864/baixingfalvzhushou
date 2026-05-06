"""Admin 路由 - 管理后台"""
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..database import get_db
from ..services import PostService, CommentService
from ..middleware import AuthMiddleware, AuthUser
from ..clients import user_service_client
from ..events import event_bus
from ..models import Report, Post, Comment
from ..schemas import PostResponse, PostListResponse

router = APIRouter()

auth_middleware = AuthMiddleware(user_client=user_service_client)


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    target_type: str
    target_id: int
    reason: str
    detail: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    items: List[ReportResponse]
    total: int
    page: int
    page_size: int


class ReviewRequest(BaseModel):
    action: str
    result: Optional[str] = None


async def require_admin(request: Request) -> AuthUser:
    current_user = await auth_middleware.get_current_user(request)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


@router.get("/posts/pending", response_model=PostListResponse)
async def list_pending_posts(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    await require_admin(request)

    from sqlalchemy import select, func, desc, and_
    query = select(Post).where(
        and_(
            Post.status == "pending_review",
            Post.is_deleted == False
        )
    )

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = query.order_by(desc(Post.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    posts = result.scalars().all()

    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in posts],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/posts/{post_id}/review")
async def review_post(
    post_id: int,
    request: Request,
    review: ReviewRequest,
    db: AsyncSession = Depends(get_db)
):
    current_user = await require_admin(request)

    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    if review.action == "approve":
        post.status = "published"
    elif review.action == "reject":
        post.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="无效的操作")

    post.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {"success": True, "message": f"帖子已{'通过' if review.action == 'approve' else '拒绝'}"}


@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    await require_admin(request)

    query = select(Report)

    if status_filter:
        query = query.where(Report.status == status_filter)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = query.order_by(desc(Report.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    reports = result.scalars().all()

    return ReportListResponse(
        items=[ReportResponse.model_validate(r) for r in reports],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/reports/{report_id}/handle")
async def handle_report(
    report_id: int,
    request: Request,
    review: ReviewRequest,
    db: AsyncSession = Depends(get_db)
):
    current_user = await require_admin(request)

    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="举报不存在")

    report.status = "handled"
    report.handled_by = current_user.id
    report.handled_at = datetime.now(timezone.utc)
    report.handle_result = review.result

    if review.action == "delete_content":
        if report.target_type == "post":
            post_result = await db.execute(
                select(Post).where(Post.id == report.target_id)
            )
            post = post_result.scalar_one_or_none()
            if post:
                post.status = "deleted"
                post.is_deleted = True
                post.deleted_at = datetime.now(timezone.utc)

        elif report.target_type == "comment":
            comment_result = await db.execute(
                select(Comment).where(Comment.id == report.target_id)
            )
            comment = comment_result.scalar_one_or_none()
            if comment:
                comment.status = "deleted"
                comment.is_deleted = True
                comment.deleted_at = datetime.now(timezone.utc)

    await db.commit()

    return {"success": True, "message": "举报已处理"}


@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: int,
    request: Request,
    reason: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    current_user = await require_admin(request)

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能封禁自己")

    from ..clients import user_service_client
    user_info = await user_service_client.get_user_info(user_id)
    if not user_info:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {"success": True, "message": f"用户 {user_id} 已被封禁", "reason": reason}


@router.get("/statistics")
async def get_statistics(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    await require_admin(request)

    from sqlalchemy import select, func

    total_posts = await db.execute(
        select(func.count()).select_from(Post)
    )
    total_posts = total_posts.scalar() or 0

    active_posts = await db.execute(
        select(func.count()).select_from(Post).where(Post.status == "published")
    )
    active_posts = active_posts.scalar() or 0

    pending_posts = await db.execute(
        select(func.count()).select_from(Post).where(Post.status == "pending_review")
    )
    pending_posts = pending_posts.scalar() or 0

    total_comments = await db.execute(
        select(func.count()).select_from(Comment)
    )
    total_comments = total_comments.scalar() or 0

    pending_reports = await db.execute(
        select(func.count()).select_from(Report).where(Report.status == "pending")
    )
    pending_reports = pending_reports.scalar() or 0

    return {
        "posts": {
            "total": total_posts,
            "active": active_posts,
            "pending_review": pending_posts,
        },
        "comments": {
            "total": total_comments,
        },
        "reports": {
            "pending": pending_reports,
        }
    }
