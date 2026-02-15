"""论坛内容审核相关路由"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, cast
from typing_extensions import TypedDict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import and_, case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.forum import Comment, Post
from ...models.system import LogAction
from ...models.user import User
from ...services.forum_service import forum_service
from ...utils.deps import require_admin
from .common import _create_notification, _log_forum_admin_action

router = APIRouter()


class ReviewAction(BaseModel):
    action: str  # approve / reject / delete
    reason: str | None = None


class PendingCommentItem(TypedDict):
    id: int
    content: str
    user_id: int
    username: str | None
    post_id: int
    post_title: str | None
    created_at: datetime


class PendingCommentListResponse(TypedDict):
    items: list[PendingCommentItem]
    total: int


class PendingPostItem(TypedDict):
    id: int
    title: str
    user_id: int
    username: str | None
    category: str | None
    created_at: datetime
    review_reason: str | None


class PendingPostListResponse(TypedDict):
    items: list[PendingPostItem]
    total: int


@router.get("/admin/pending-comments", summary="获取待审核评论")
async def get_pending_comments(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PendingCommentListResponse:
    """获取待审核的评论列表"""
    base_filter = and_(
        Comment.is_deleted == False,
        Comment.review_status == "pending")

    total_result = await db.execute(select(func.count(Comment.id)).where(base_filter))
    total = total_result.scalar() or 0

    query = (
        select(
            Comment.id,
            Comment.content,
            Comment.user_id,
            User.username,
            Comment.post_id,
            Post.title.label("post_title"),
            Comment.created_at,
        )
        .select_from(Comment)
        .outerjoin(User, User.id == Comment.user_id)
        .outerjoin(Post, Post.id == Comment.post_id)
        .where(base_filter)
        .order_by(Comment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    rows = result.all()

    items: list[PendingCommentItem] = []
    for row in rows:
        items.append(
            {
                "id": int(cast(int, row.id)),
                "content": str(cast(str, row.content)),
                "user_id": int(cast(int, row.user_id)),
                "username": cast(str | None, row.username),
                "post_id": int(cast(int, row.post_id)),
                "post_title": cast(str | None, row.post_title),
                "created_at": cast(datetime, row.created_at),
            }
        )

    # type: PendingCommentListResponse
    return {"items": items, "total": int(total)}


@router.get("/admin/pending-posts", summary="获取待审核帖子")
async def get_pending_posts(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PendingPostListResponse:
    base_filter = and_(
        Post.is_deleted == False,
        Post.review_status == "pending")

    total_result = await db.execute(select(func.count(Post.id)).where(base_filter))
    total = total_result.scalar() or 0

    query = (
        select(
            Post.id,
            Post.title,
            Post.user_id,
            User.username,
            Post.category,
            Post.created_at,
            Post.review_reason,
        )
        .select_from(Post)
        .outerjoin(User, User.id == Post.user_id)
        .where(base_filter)
        .order_by(Post.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    rows = result.all()

    items: list[PendingPostItem] = []
    for row in rows:
        items.append(
            {
                "id": int(cast(int, row.id)),
                "title": str(cast(str, row.title)),
                "user_id": int(cast(int, row.user_id)),
                "username": cast(str | None, row.username),
                "category": cast(str | None, row.category),
                "created_at": cast(datetime, row.created_at),
                "review_reason": cast(str | None, row.review_reason),
            }
        )

    # type: PendingPostListResponse
    return {"items": items, "total": int(total)}


@router.post("/admin/posts/{post_id}/review", summary="审核帖子")
async def review_post(
    post_id: int,
    data: ReviewAction,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    result = await db.execute(select(Post).where(and_(Post.id == post_id, Post.is_deleted == False)))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    now = datetime.now(timezone.utc)

    if data.action == "delete":
        post.is_deleted = True
        post.review_status = "rejected"
        post.review_reason = data.reason
        post.reviewed_at = now

        await _log_forum_admin_action(
            db,
            user_id=current_user.id,
            action=LogAction.DELETE,
            module="forum",
            target_id=post.id,
            target_type="post",
            description="审核删除帖子",
            extra_data={"action": "delete", "reason": data.reason},
            request=request,
        )

        content_lines = [f"标题：{post.title}"]
        if data.reason:
            content_lines.append(f"原因：{data.reason}")
        await _create_notification(
            db,
            user_id=int(post.user_id),
            title="你的帖子已被删除",
            content="\n".join(content_lines) if content_lines else None,
            link=f"/forum/post/{int(post.id)}?deleted=1",
            related_post_id=int(post.id),
        )
        await db.commit()
        return {"message": "帖子已删除"}

    if data.action == "approve":
        post.review_status = "approved"
        post.review_reason = data.reason
        post.reviewed_at = now

        await _log_forum_admin_action(
            db,
            user_id=current_user.id,
            action=LogAction.UPDATE,
            module="forum",
            target_id=post.id,
            target_type="post",
            description="审核通过帖子",
            extra_data={"action": "approve", "reason": data.reason},
            request=request,
        )

        content_lines = [f"标题：{post.title}"]
        if data.reason:
            content_lines.append(f"原因：{data.reason}")
        await _create_notification(
            db,
            user_id=int(post.user_id),
            title="你的帖子已通过审核",
            content="\n".join(content_lines) if content_lines else None,
            link=f"/forum/post/{int(post.id)}",
            related_post_id=int(post.id),
        )
        await db.commit()
        return {"message": "帖子已通过审核"}

    if data.action == "reject":
        post.review_status = "rejected"
        post.review_reason = data.reason
        post.reviewed_at = now

        await _log_forum_admin_action(
            db,
            user_id=current_user.id,
            action=LogAction.UPDATE,
            module="forum",
            target_id=post.id,
            target_type="post",
            description="审核驳回帖子",
            extra_data={"action": "reject", "reason": data.reason},
            request=request,
        )

        content_lines = [f"标题：{post.title}"]
        if data.reason:
            content_lines.append(f"原因：{data.reason}")
        await _create_notification(
            db,
            user_id=int(post.user_id),
            title="你的帖子未通过审核",
            content="\n".join(content_lines) if content_lines else None,
            link=f"/forum/post/{int(post.id)}",
            related_post_id=int(post.id),
        )
        await db.commit()
        return {"message": "帖子已驳回"}

    raise HTTPException(status_code=400, detail="无效操作")


@router.post("/admin/comments/{comment_id}/review", summary="审核评论")
async def review_comment(
    comment_id: int,
    data: ReviewAction,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """审核评论"""
    result = await db.execute(select(Comment).where(and_(Comment.id == comment_id, Comment.is_deleted == False)))
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    if data.action == "delete":
        if comment.review_status in (None, "approved"):
            _ = await db.execute(
                update(Post)
                .where(Post.id == comment.post_id)
                .values(
                    comment_count=case(
                        (
                            func.coalesce(Post.comment_count, 0) > 0,
                            func.coalesce(Post.comment_count, 0) - 1,
                        ),
                        else_=0,
                    )
                )
            )

        comment.is_deleted = True
        comment.review_status = "rejected"
        comment.review_reason = data.reason
        comment.reviewed_at = datetime.now(timezone.utc)

        await _log_forum_admin_action(
            db,
            user_id=current_user.id,
            action=LogAction.DELETE,
            module="forum",
            target_id=comment.id,
            target_type="comment",
            description="审核删除评论",
            extra_data={
                "action": "delete",
                "reason": data.reason,
                "post_id": comment.post_id},
            request=request,
        )

        content_lines = [f"评论ID：{int(comment.id)}",
                         f"帖子ID：{int(comment.post_id)}"]
        if data.reason:
            content_lines.append(f"原因：{data.reason}")
        await _create_notification(
            db,
            user_id=int(comment.user_id),
            title="你的评论已被删除",
            content="\n".join(content_lines) if content_lines else None,
            link=f"/forum/post/{int(comment.post_id)}?commentId={int(comment.id)}#comment-{int(comment.id)}",
            related_post_id=int(comment.post_id),
            related_comment_id=int(comment.id),
        )
        await db.commit()
        return {"message": "评论已删除"}

    if data.action == "approve":
        if comment.review_status == "pending":
            _ = await db.execute(
                update(Post)
                .where(Post.id == comment.post_id)
                .values(comment_count=func.coalesce(Post.comment_count, 0) + 1)
            )

        comment.review_status = "approved"
        comment.review_reason = data.reason
        comment.reviewed_at = datetime.now(timezone.utc)

        await _log_forum_admin_action(
            db,
            user_id=current_user.id,
            action=LogAction.UPDATE,
            module="forum",
            target_id=comment.id,
            target_type="comment",
            description="审核通过评论",
            extra_data={
                "action": "approve",
                "reason": data.reason,
                "post_id": comment.post_id},
            request=request,
        )

        content_lines = [f"评论ID：{int(comment.id)}",
                         f"帖子ID：{int(comment.post_id)}"]
        if data.reason:
            content_lines.append(f"原因：{data.reason}")
        await _create_notification(
            db,
            user_id=int(comment.user_id),
            title="你的评论已通过审核",
            content="\n".join(content_lines) if content_lines else None,
            link=f"/forum/post/{int(comment.post_id)}?commentId={int(comment.id)}#comment-{int(comment.id)}",
            related_post_id=int(comment.post_id),
            related_comment_id=int(comment.id),
        )
        await db.commit()
        return {"message": "评论已通过审核"}

    if data.action == "reject":
        if comment.review_status in (None, "approved"):
            _ = await db.execute(
                update(Post)
                .where(Post.id == comment.post_id)
                .values(
                    comment_count=case(
                        (
                            func.coalesce(Post.comment_count, 0) > 0,
                            func.coalesce(Post.comment_count, 0) - 1,
                        ),
                        else_=0,
                    )
                )
            )

        comment.review_status = "rejected"
        comment.review_reason = data.reason
        comment.reviewed_at = datetime.now(timezone.utc)
        comment.is_deleted = True

        await _log_forum_admin_action(
            db,
            user_id=current_user.id,
            action=LogAction.UPDATE,
            module="forum",
            target_id=comment.id,
            target_type="comment",
            description="审核驳回评论",
            extra_data={
                "action": "reject",
                "reason": data.reason,
                "post_id": comment.post_id},
            request=request,
        )

        content_lines = [f"评论ID：{int(comment.id)}",
                         f"帖子ID：{int(comment.post_id)}"]
        if data.reason:
            content_lines.append(f"原因：{data.reason}")
        await _create_notification(
            db,
            user_id=int(comment.user_id),
            title="你的评论未通过审核",
            content="\n".join(content_lines) if content_lines else None,
            link=f"/forum/post/{int(comment.post_id)}?commentId={int(comment.id)}#comment-{int(comment.id)}",
            related_post_id=int(comment.post_id),
            related_comment_id=int(comment.id),
        )
        await db.commit()
        return {"message": "评论已驳回并删除"}

    raise HTTPException(status_code=400, detail="无效操作")


class BatchReviewAction(BaseModel):
    ids: list[int]
    action: str
    reason: str | None = None


class BatchReviewResponse(TypedDict):
    processed: list[int]
    missing: list[int]
    action: str
    reason: str | None
    requested: list[int]
    counts: dict[str, int]
    message: str


class ContentStatsResponse(TypedDict):
    posts: dict[str, int]
    comments: dict[str, int]
    sensitive_words_count: int
    ad_words_count: int


@router.post("/admin/posts/review/batch", summary="批量审核帖子")
async def batch_review_posts(
    data: BatchReviewAction,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
) -> BatchReviewResponse:
    ids = [int(x) for x in (data.ids or []) if int(x) > 0]
    if not ids:
        raise HTTPException(status_code=400, detail="ids 不能为空")

    action = (data.action or "").strip().lower()
    if action not in ("approve", "reject", "delete"):
        raise HTTPException(status_code=400,
                            detail="action 仅支持 approve / reject / delete")

    result = await db.execute(select(Post).where(and_(Post.id.in_(ids), Post.is_deleted == False)))
    posts = list(result.scalars().all())
    found_ids = {int(p.id) for p in posts}
    missing_ids = [int(i) for i in ids if int(i) not in found_ids]

    now = datetime.now(timezone.utc)
    processed: list[int] = []
    for post in posts:
        if action == "delete":
            post.is_deleted = True
            post.review_status = "rejected"
            post.review_reason = data.reason
            post.reviewed_at = now
        elif action == "approve":
            post.review_status = "approved"
            post.review_reason = data.reason
            post.reviewed_at = now
        elif action == "reject":
            post.review_status = "rejected"
            post.review_reason = data.reason
            post.reviewed_at = now
        processed.append(int(post.id))

    max_individual = 10
    title_single = (
        "你的帖子已通过审核"
        if action == "approve"
        else "你的帖子未通过审核"
        if action == "reject"
        else "你的帖子已被删除"
    )
    by_user: dict[int, list[Post]] = {}
    for post in posts:
        by_user.setdefault(int(post.user_id), []).append(post)

    notifications_created = 0
    for user_id, user_posts in by_user.items():
        if len(user_posts) <= max_individual:
            for post in user_posts:
                content_lines = [f"标题：{post.title}"]
                if data.reason:
                    content_lines.append(f"原因：{data.reason}")
                link = f"/forum/post/{int(post.id)}?deleted=1" if action == "delete" else f"/forum/post/{int(post.id)}"
                await _create_notification(
                    db,
                    user_id=int(user_id),
                    title=f"{title_single}（批量）",
                    content="\n".join(
                        content_lines) if content_lines else None,
                    link=link,
                    related_post_id=int(post.id),
                )
                notifications_created += 1
        else:
            post_ids = [int(p.id) for p in user_posts]
            content_lines = [f"帖子ID：{', '.join(str(i) for i in post_ids)}"]
            if data.reason:
                content_lines.append(f"原因：{data.reason}")
            first = user_posts[0]
            link = f"/forum/post/{int(first.id)}?deleted=1" if action == "delete" else f"/forum/post/{int(first.id)}"
            await _create_notification(
                db,
                user_id=int(user_id),
                title=f"{title_single}（批量）",
                content="\n".join(content_lines) if content_lines else None,
                link=link,
                related_post_id=int(first.id),
            )
            notifications_created += 1

    await _log_forum_admin_action(
        db,
        user_id=current_user.id,
        action=LogAction.UPDATE if action in (
            "approve", "reject") else LogAction.DELETE,
        module="forum",
        target_type="post",
        description="批量审核帖子",
        extra_data={
            "action": action,
            "ids": ids,
            "processed": processed,
            "missing": missing_ids,
            "reason": data.reason},
        request=request,
    )

    await db.commit()
    counts = {
        "requested": len(ids),
        "processed": len(processed),
        "missing": len(missing_ids),
        "notifications_created": int(notifications_created),
    }
    message = f"已处理 {counts['processed']} 条，缺失 {counts['missing']} 条"
    return {
        "processed": processed,
        "missing": missing_ids,
        "action": action,
        "reason": data.reason,
        "requested": ids,
        "counts": counts,
        "message": message,
    }  # type: BatchReviewResponse


@router.post("/admin/comments/review/batch", summary="批量审核评论")
async def batch_review_comments(
    data: BatchReviewAction,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
) -> BatchReviewResponse:
    ids = [int(x) for x in (data.ids or []) if int(x) > 0]
    if not ids:
        raise HTTPException(status_code=400, detail="ids 不能为空")

    action = (data.action or "").strip().lower()
    if action not in ("approve", "reject", "delete"):
        raise HTTPException(status_code=400,
                            detail="action 仅支持 approve / reject / delete")

    result = await db.execute(select(Comment).where(and_(Comment.id.in_(ids), Comment.is_deleted == False)))
    comments = list(result.scalars().all())
    found_ids = {int(c.id) for c in comments}
    missing_ids = [int(i) for i in ids if int(i) not in found_ids]

    processed: list[int] = []
    now = datetime.now(timezone.utc)

    for comment in comments:
        if action == "delete":
            if comment.review_status in (None, "approved"):
                _ = await db.execute(
                    update(Post)
                    .where(Post.id == comment.post_id)
                    .values(
                        comment_count=case(
                            (
                                func.coalesce(Post.comment_count, 0) > 0,
                                func.coalesce(Post.comment_count, 0) - 1,
                            ),
                            else_=0,
                        )
                    )
                )

            comment.is_deleted = True
            comment.review_status = "rejected"
            comment.review_reason = data.reason
            comment.reviewed_at = now

        elif action == "approve":
            if comment.review_status == "pending":
                _ = await db.execute(
                    update(Post)
                    .where(Post.id == comment.post_id)
                    .values(comment_count=func.coalesce(Post.comment_count, 0) + 1)
                )

            comment.review_status = "approved"
            comment.review_reason = data.reason
            comment.reviewed_at = now

        elif action == "reject":
            if comment.review_status in (None, "approved"):
                _ = await db.execute(
                    update(Post)
                    .where(Post.id == comment.post_id)
                    .values(
                        comment_count=case(
                            (
                                func.coalesce(Post.comment_count, 0) > 0,
                                func.coalesce(Post.comment_count, 0) - 1,
                            ),
                            else_=0,
                        )
                    )
                )

            comment.review_status = "rejected"
            comment.review_reason = data.reason
            comment.reviewed_at = now
            comment.is_deleted = True

        processed.append(int(comment.id))

    max_individual = 10
    title_single = (
        "你的评论已通过审核"
        if action == "approve"
        else "你的评论未通过审核"
        if action == "reject"
        else "你的评论已被删除"
    )
    by_user: dict[int, list[Comment]] = {}
    for comment in comments:
        by_user.setdefault(int(comment.user_id), []).append(comment)

    notifications_created = 0
    for user_id, items in by_user.items():
        if len(items) <= max_individual:
            for comment in items:
                content_lines = [
                    f"评论ID：{int(comment.id)}", f"帖子ID：{int(comment.post_id)}"]
                if data.reason:
                    content_lines.append(f"原因：{data.reason}")
                link = f"/forum/post/{int(comment.post_id)}?commentId={int(comment.id)}#comment-{int(comment.id)}"
                await _create_notification(
                    db,
                    user_id=int(user_id),
                    title=f"{title_single}（批量）",
                    content="\n".join(
                        content_lines) if content_lines else None,
                    link=link,
                    related_post_id=int(comment.post_id),
                    related_comment_id=int(comment.id),
                )
                notifications_created += 1
        else:
            comment_ids = [int(c.id) for c in items]
            content_lines = [f"评论ID：{', '.join(str(i) for i in comment_ids)}"]
            if data.reason:
                content_lines.append(f"原因：{data.reason}")
            first = items[0]
            link = f"/forum/post/{int(first.post_id)}?commentId={int(first.id)}#comment-{int(first.id)}"
            await _create_notification(
                db,
                user_id=int(user_id),
                title=f"{title_single}（批量）",
                content="\n".join(content_lines) if content_lines else None,
                link=link,
                related_post_id=int(first.post_id),
                related_comment_id=int(first.id),
            )
            notifications_created += 1

    await _log_forum_admin_action(
        db,
        user_id=current_user.id,
        action=LogAction.UPDATE if action in (
            "approve", "reject") else LogAction.DELETE,
        module="forum",
        target_type="comment",
        description="批量审核评论",
        extra_data={
            "action": action,
            "ids": ids,
            "processed": processed,
            "missing": missing_ids,
            "reason": data.reason},
        request=request,
    )

    await db.commit()
    counts = {
        "requested": len(ids),
        "processed": len(processed),
        "missing": len(missing_ids),
        "notifications_created": int(notifications_created),
    }
    message = f"已处理 {counts['processed']} 条，缺失 {counts['missing']} 条"
    return {
        "processed": processed,
        "missing": missing_ids,
        "action": action,
        "reason": data.reason,
        "requested": ids,
        "counts": counts,
        "message": message,
    }  # type: BatchReviewResponse


@router.get("/admin/content-stats", summary="内容审核统计")
async def get_content_stats(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ContentStatsResponse:
    """获取内容审核统计数据"""
    config = await forum_service.apply_content_filter_config_from_db(db)

    total_posts = await db.scalar(select(func.count()).select_from(Post)) or 0
    deleted_posts = await db.scalar(select(func.count()).select_from(Post).where(Post.is_deleted)) or 0

    total_comments = await db.scalar(select(func.count()).select_from(Comment)) or 0
    deleted_comments = await db.scalar(select(func.count()).select_from(Comment).where(Comment.is_deleted)) or 0

    return {
        "posts": {
            "total": total_posts,
            "deleted": deleted_posts,
            "active": total_posts -
            deleted_posts,
        },
        "comments": {
            "total": total_comments,
            "deleted": deleted_comments,
            "active": total_comments -
            deleted_comments,
        },
        "sensitive_words_count": len(
            cast(
                list[str],
                config.get("sensitive_words") or [])),
        "ad_words_count": len(
            cast(
                list[str],
                config.get("ad_words") or [])),
    }  # type: ContentStatsResponse
