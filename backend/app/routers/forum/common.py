"""论坛路由公共工具"""
from __future__ import annotations

import json
from typing import cast

from fastapi import HTTPException, Request, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.forum import Comment, Post
from ...models.lawfirm import Lawyer
from ...models.notification import Notification, NotificationType
from ...models.system import AdminLog, LogAction
from ...models.user import User
from ...schemas.forum import AuthorInfo, CommentResponse, PostResponse, ReactionCount
from ...services.forum_service import forum_service
from ...utils.rate_limiter import get_client_ip
from ...utils.json_parser import parse_attachments_field, parse_images_field


async def _create_notification(
    db: AsyncSession,
    *,
    user_id: int,
    title: str,
    content: str | None = None,
    link: str | None = None,
    related_user_id: int | None = None,
    related_post_id: int | None = None,
    related_comment_id: int | None = None,
) -> Notification:
    from ...services.unified_notification_service import unified_notification_service as uns
    from ...services.unified_notification_service import NotificationType

    notification = await uns.send_notification(
        db,
        user_id=int(user_id),
        title=str(title),
        content=content,
        type=NotificationType.SYSTEM,
        link=link,
        dedupe_key=None,
        notify_ws=True,
    )
    if notification is not None:
        notification.related_user_id = int(
            related_user_id) if related_user_id is not None else None
        notification.related_post_id = int(
            related_post_id) if related_post_id is not None else None
        notification.related_comment_id = int(
            related_comment_id) if related_comment_id is not None else None
        db.add(notification)
    return notification


async def _log_forum_admin_action(
    db: AsyncSession,
    *,
    user_id: int,
    action: str,
    module: str,
    target_id: int | None = None,
    target_type: str | None = None,
    description: str | None = None,
    extra_data: dict[str, object] | None = None,
    request: Request | None = None,
) -> None:
    ip_address = None
    user_agent = None
    if request is not None:
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")[:500]

    log = AdminLog(
        user_id=int(user_id),
        action=str(action),
        module=str(module),
        target_id=(int(target_id) if target_id is not None else None),
        target_type=target_type,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        extra_data=json.dumps(extra_data,
                              ensure_ascii=False) if extra_data else None,
    )
    db.add(log)


async def _build_post_response(
    db: AsyncSession,
    post: Post,
    user_id: int | None,
    *,
    favorite_count: int | None = None,
    reactions_data: list[dict[str, int | str]] | None = None,
    is_liked: bool | None = None,
    is_favorited: bool | None = None,
) -> PostResponse:
    """构建帖子响应"""
    # 使用传入的批量查询结果，避免N+1查询
    if is_liked is None and user_id:
        is_liked = await forum_service.is_post_liked(db, post.id, user_id)
    elif is_liked is None:
        is_liked = False

    if is_favorited is None and user_id:
        is_favorited = await forum_service.is_post_favorited(db, post.id, user_id)
    elif is_favorited is None:
        is_favorited = False

    if favorite_count is None:
        favorite_count = await forum_service.get_post_favorite_count(db, post.id)

    author_info = None
    if post.author:
        author_info = AuthorInfo(
            id=post.author.id,
            username=post.author.username,
            nickname=post.author.nickname,
            avatar=post.author.avatar,
        )

    # 使用JSON解析工具解析图片和附件
    images = parse_images_field(post.images)
    attachments = parse_attachments_field(post.attachments)

    if reactions_data is None:
        reactions_data = await forum_service.get_post_reactions(db, post.id)
    reactions = [
        ReactionCount(
            emoji=str(
                r["emoji"]), count=int(
                r["count"])) for r in reactions_data]

    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        category=post.category,
        user_id=post.user_id,
        view_count=int(post.view_count or 0),
        like_count=int(post.like_count or 0),
        comment_count=int(post.comment_count or 0),
        share_count=int(post.share_count or 0),
        favorite_count=favorite_count,
        is_pinned=bool(post.is_pinned),
        is_hot=bool(post.is_hot),
        is_essence=bool(post.is_essence),
        is_deleted=bool(getattr(post, "is_deleted", False)),
        heat_score=float(post.heat_score or 0.0),
        cover_image=post.cover_image,
        images=images,
        attachments=attachments,
        reactions=reactions,
        created_at=post.created_at,
        updated_at=post.updated_at or post.created_at,
        review_status=getattr(post, "review_status", None),
        review_reason=getattr(post, "review_reason", None),
        reviewed_at=getattr(post, "reviewed_at", None),
        author=author_info,
        is_liked=is_liked,
        is_favorited=is_favorited,
    )


# 最大评论嵌套深度限制
MAX_COMMENT_DEPTH = 5


async def _build_comment_response(
        db: AsyncSession,
        comment: Comment,
        user_id: int | None,
        *,
        liked_comment_ids: set[int] | None = None,
        current_depth: int = 0) -> CommentResponse | None:
    """构建评论响应 - 支持批量查询优化N+1问题
    
    Args:
        db: 数据库会话
        comment: 评论对象
        user_id: 当前用户ID
        liked_comment_ids: 用户已点赞的评论ID集合，用于避免单独查询点赞状态
        current_depth: 当前嵌套深度（用于防止递归过深）
    
    Returns:
        评论响应对象，如果超出深度限制则返回None
    """
    # 防止递归过深导致栈溢出
    if current_depth >= MAX_COMMENT_DEPTH:
        return None
    
    _ = db
    is_liked = False
    if user_id:
        if liked_comment_ids is not None:
            is_liked = int(comment.id) in liked_comment_ids
        else:
            is_liked = await forum_service.is_comment_liked(db, comment.id, user_id)
    author_info = None
    if comment.author:
        author_info = AuthorInfo(
            id=comment.author.id,
            username=comment.author.username,
            nickname=comment.author.nickname,
            avatar=comment.author.avatar,
        )

    images: list[str] = []
    comment_images = comment.images
    if isinstance(comment_images, str) and comment_images:
        try:
            raw_comment_images: object = cast(
                object, json.loads(comment_images))
            if isinstance(raw_comment_images, list):
                images = [
                    str(x) for x in cast(
                        list[object],
                        raw_comment_images) if x]
        except (json.JSONDecodeError, TypeError):
            images = []

    replies: list[CommentResponse] = []
    for child in comment.replies:
        if child.is_deleted:
            continue
        reply = await _build_comment_response(
            db, child, user_id,
            liked_comment_ids=liked_comment_ids,
            current_depth=current_depth + 1
        )
        if reply is not None:
            replies.append(reply)

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        post_id=comment.post_id,
        user_id=comment.user_id,
        parent_id=comment.parent_id,
        like_count=int(comment.like_count or 0),
        images=images,
        created_at=comment.created_at,
        review_status=getattr(comment, "review_status", None),
        review_reason=getattr(comment, "review_reason", None),
        reviewed_at=getattr(comment, "reviewed_at", None),
        author=author_info,
        is_liked=is_liked,
        replies=replies,
    )


async def _build_comments_response_batch(
        db: AsyncSession,
        comments: list[Comment],
        user_id: int | None) -> list[CommentResponse]:
    """批量构建评论响应 - 优化N+1问题
    
    一次性批量查询所有评论的点赞状态，避免递归查询时的N+1问题
    """
    # 收集所有评论ID（包括嵌套回复）
    all_comment_ids: set[int] = set()
    
    def collect_comment_ids(comment_list: list[Comment]) -> None:
        for comment in comment_list:
            all_comment_ids.add(int(comment.id))
            if hasattr(comment, 'replies') and comment.replies:
                # 过滤掉已删除的回复
                active_replies = [r for r in comment.replies if not r.is_deleted]
                collect_comment_ids(active_replies)
    
    collect_comment_ids(comments)
    
    # 批量查询点赞状态
    liked_comment_ids: set[int] = set()
    if user_id and all_comment_ids:
        from ...models.forum import CommentLike
        from sqlalchemy import select as sa_select
        
        result = await db.execute(
            sa_select(CommentLike.comment_id).where(
                CommentLike.user_id == user_id,
                CommentLike.comment_id.in_(list(all_comment_ids))
            )
        )
        liked_comment_ids = {int(row[0]) for row in result.all()}
    
    # 批量构建响应
    items: list[CommentResponse] = []
    for comment in comments:
        response_item = await _build_comment_response(
            db, comment, user_id,
            liked_comment_ids=liked_comment_ids,
            current_depth=0
        )
        # 过滤掉超出深度限制的评论（防御性编程）
        if isinstance(response_item, CommentResponse):
            items.append(response_item)
    
    return items


async def _get_current_lawyer(
    db: AsyncSession,
    current_user: User,
) -> Lawyer:
    """获取当前用户的律师信息"""
    result = await db.execute(
        select(Lawyer).where(
            and_(
                Lawyer.user_id == current_user.id,
                Lawyer.is_verified,
                Lawyer.is_active,
            )
        )
    )
    lawyer = result.scalar_one_or_none()
    if not lawyer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是认证律师或律师账户未激活",
        )
    return lawyer
