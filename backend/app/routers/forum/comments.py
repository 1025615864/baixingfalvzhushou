"""论坛评论相关路由"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.forum import Comment, Post
from ...models.user import User
from ...schemas.forum import CommentCreate, CommentListResponse, CommentResponse, LikeResponse
from ...services.forum_service import forum_service
from ...utils.content_filter import check_comment_content
from ...utils.xss_sanitizer import check_comment_content_with_sanitization
from ...utils.deps import get_current_user, get_current_user_optional
from .common import _build_comment_response, _create_notification

router = APIRouter()


@router.post("/posts/{post_id}/comments",
             response_model=CommentResponse, summary="发表评论")
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """发表评论（需登录）"""
    _ = await forum_service.apply_content_filter_config_from_db(db)

    passed, error_msg = check_comment_content(comment_data.content)
    if not passed:
        raise HTTPException(status_code=400, detail=error_msg)

    # XSS 清理
    passed, error_msg, cleaned_content = check_comment_content_with_sanitization(
        comment_data.content)
    if not passed:
        raise HTTPException(status_code=400, detail=error_msg)

    # 使用清理后的内容
    comment_data.content = cleaned_content

    post = await forum_service.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    if comment_data.parent_id is not None:
        parent = await forum_service.get_comment(db, comment_data.parent_id)
        if not parent or parent.post_id != post_id:
            raise HTTPException(status_code=400, detail="父评论不存在")

    comment = await forum_service.create_comment(db, post_id, current_user.id, comment_data)
    if getattr(comment, "review_status", None) == "pending":
        content_lines: list[str] = [f"帖子ID：{int(post_id)}"]
        if getattr(comment, "review_reason", None):
            content_lines.append(f"原因：{comment.review_reason}")
        # Fire and forget the notification - don't await it
        _ = _create_notification(
            db,
            user_id=int(comment.user_id),
            title="你的评论已提交审核",
            content="\n".join(content_lines) if content_lines else None,
            link=f"/forum/post/{int(post_id)}?commentId={int(comment.id)}#comment-{int(comment.id)}",
            related_post_id=int(post_id),
            related_comment_id=int(comment.id),
        )
        await db.commit()
    return await _build_comment_response(db, comment, current_user.id)


@router.get("/posts/{post_id}/comments",
            response_model=CommentListResponse, summary="获取评论列表")
async def get_comments(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    include_unapproved: Annotated[bool, Query()] = False,
):
    """获取帖子的评论列表 - 使用批量查询优化N+1问题"""
    post = await forum_service.get_post(db, post_id)
    if not post and current_user is not None:
        post_any = await forum_service.get_post_any(db, post_id)
        if post_any and not post_any.is_deleted:
            from ...utils.permissions import is_owner_or_admin

            if is_owner_or_admin(current_user, post_any.user_id):
                post = post_any

    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    user_id = current_user.id if current_user else None
    viewer_role = current_user.role if current_user else None

    comments, total = await forum_service.get_comments_visible(
        db,
        post_id,
        page,
        page_size,
        viewer_user_id=user_id,
        viewer_role=viewer_role,
        include_unapproved=bool(include_unapproved),
    )

    # 使用批量查询方法避免N+1问题
    from .common import _build_comments_response_batch
    items = await _build_comments_response_batch(db, comments, user_id)

    return CommentListResponse(items=items, total=total)


@router.delete("/comments/{comment_id}", summary="删除评论")
async def delete_comment(
    comment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """删除评论（仅作者、版主或管理员可操作）"""
    from ...utils.permissions import is_owner_or_admin

    comment = await forum_service.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    if not is_owner_or_admin(current_user, comment.user_id):
        raise HTTPException(status_code=403, detail="只有作者、版主或管理员可以删除评论")

    await forum_service.delete_comment(db, comment)
    return {"message": "删除成功"}


@router.post("/comments/{comment_id}/restore", summary="恢复评论")
async def restore_comment(
    comment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """恢复评论（撤销删除，仅作者、版主或管理员可操作）"""
    from ...utils.permissions import is_owner_or_admin

    comment = await forum_service.get_comment_any(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    if not is_owner_or_admin(current_user, comment.user_id):
        raise HTTPException(status_code=403, detail="只有作者、版主或管理员可以恢复评论")

    _ = await forum_service.restore_comment(db, comment)
    return {"message": "已恢复"}


@router.post("/comments/{comment_id}/like",
             response_model=LikeResponse, summary="点赞/取消点赞评论")
async def toggle_comment_like(
    comment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    comment = await forum_service.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    liked, like_count = await forum_service.toggle_comment_like(db, comment_id, current_user.id)
    message = "点赞成功" if liked else "取消点赞"
    return LikeResponse(liked=liked, like_count=like_count, message=message)


class MyCommentItem(BaseModel):
    id: int
    post_id: int
    post_title: str | None = None
    content: str
    created_at: datetime
    review_status: str | None = None
    review_reason: str | None = None


class MyCommentListResponse(BaseModel):
    items: list[MyCommentItem]
    total: int
    page: int
    page_size: int


@router.get("/me/comments", response_model=MyCommentListResponse,
            summary="获取我发布的评论")
async def get_my_comments(db: Annotated[AsyncSession,
                                        Depends(get_db)],
                          current_user: Annotated[User,
                                                  Depends(get_current_user)],
                          page: Annotated[int,
                                          Query(ge=1)] = 1,
                          page_size: Annotated[int,
                                               Query(ge=1,
                                                     le=100)] = 20,
                          status_param: Annotated[str | None,
                                                  Query(alias="status",
                                                        description="筛选状态：all/pending/approved/rejected"),
                                                  ] = None,
                          ):
    status_filter = (status_param or "all").strip().lower()
    if status_filter not in ("all", "pending", "approved", "rejected"):
        raise HTTPException(
            status_code=400,
            detail="status 仅支持 all / pending / approved / rejected")

    base_filter = and_(Comment.user_id == current_user.id)
    if status_filter == "all":
        base_filter = and_(
            base_filter,
            or_(Comment.is_deleted == False,
                Comment.review_status == "rejected"),
        )
    elif status_filter == "pending":
        base_filter = and_(
            base_filter,
            Comment.review_status == "pending",
            Comment.is_deleted == False)
    elif status_filter == "approved":
        approved_filter = or_(
            Comment.review_status.is_(None),
            Comment.review_status == "approved")
        base_filter = and_(
            base_filter,
            approved_filter,
            Comment.is_deleted == False)
    elif status_filter == "rejected":
        base_filter = and_(base_filter, Comment.review_status == "rejected")

    total_result = await db.execute(select(func.count(Comment.id)).where(base_filter))
    total = int(total_result.scalar() or 0)

    query = (
        select(
            Comment.id,
            Comment.post_id,
            Post.title.label("post_title"),
            Comment.content,
            Comment.created_at,
            Comment.review_status,
            Comment.review_reason,
        )
        .select_from(Comment)
        .outerjoin(Post, Post.id == Comment.post_id)
        .where(base_filter)
        .order_by(desc(Comment.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    rows = result.all()

    items: list[MyCommentItem] = []
    for row in rows:
        items.append(
            MyCommentItem(
                id=int(cast(int, row.id)),
                post_id=int(cast(int, row.post_id)),
                post_title=cast(str | None, row.post_title),
                content=str(cast(str, row.content)),
                created_at=cast(datetime, row.created_at),
                review_status=cast(str | None, row.review_status),
                review_reason=cast(str | None, row.review_reason),
            )
        )

    return MyCommentListResponse(
        items=items, total=total, page=page, page_size=page_size)
