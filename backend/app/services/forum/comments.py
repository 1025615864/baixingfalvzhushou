"""论坛评论服务

提供评论 CRUD 和互动功能
"""
import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, func, desc, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ...models.forum import Post, Comment, CommentLike
from ...schemas.forum import CommentCreate
from .core import ForumService


logger = logging.getLogger(__name__)


class ForumCommentService:
    """论坛评论服务"""

    @staticmethod
    async def create_comment(
        db: AsyncSession,
        post_id: int,
        user_id: int,
        comment_data: CommentCreate,
    ) -> Comment:
        """创建评论"""
        from ...utils.content_filter import needs_review

        images_json = json.dumps(
            comment_data.images) if comment_data.images else None

        _ = await ForumService.apply_content_filter_config_from_db(db)

        requires_review = False
        review_reason: str | None = None

        review_enabled = await ForumService.is_comment_review_enabled(db)
        if not review_enabled:
            review_status = "approved"
        else:
            requires_review, review_reason = needs_review(comment_data.content)
            review_status = "pending" if requires_review else "approved"

        comment = Comment(
            content=comment_data.content,
            post_id=post_id,
            user_id=user_id,
            parent_id=comment_data.parent_id,
            images=images_json,
            review_status=review_status,
            review_reason=review_reason if requires_review else None,
        )
        db.add(comment)

        if review_status == "approved":
            _ = await db.execute(
                update(Post)
                .where(Post.id == post_id)
                .values(comment_count=func.coalesce(Post.comment_count, 0) + 1)
            )

        await db.commit()
        await db.refresh(comment)
        return comment

    @staticmethod
    async def get_comments(
        db: AsyncSession,
        post_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Comment], int]:
        """获取帖子评论列表"""
        from sqlalchemy.orm.attributes import set_committed_value

        approved_filter = or_(
            Comment.review_status.is_(None),
            Comment.review_status == "approved")
        result = await db.execute(
            select(Comment)
            .options(joinedload(Comment.author))
            .where(
                and_(
                    Comment.post_id == post_id,
                    approved_filter,
                    Comment.is_deleted == False,
                )
            )
            .order_by(desc(Comment.created_at))
        )

        all_comments = list(result.scalars().all())
        top_level = [c for c in all_comments if c.parent_id is None]
        total = len(top_level)

        start = max(0, (page - 1) * page_size)
        end = start + page_size
        page_top = top_level[start:end]

        children_by_parent: dict[int, list[Comment]] = {}
        for c in all_comments:
            if c.parent_id is None:
                continue
            children_by_parent.setdefault(int(c.parent_id), []).append(c)

        def _created_at_ts(value: Comment) -> float:
            created_at = getattr(value, "created_at", None)
            if isinstance(created_at, datetime):
                try:
                    return float(created_at.timestamp())
                except (OSError, ValueError, OverflowError):
                    return 0.0
            return 0.0

        for children in children_by_parent.values():
            children.sort(key=_created_at_ts)

        def attach_replies(node: Comment) -> None:
            replies = children_by_parent.get(int(node.id), [])
            set_committed_value(node, "replies", replies)

        for node in page_top:
            attach_replies(node)

        return page_top, total

    @staticmethod
    async def get_comments_visible(
        db: AsyncSession,
        post_id: int,
        page: int = 1,
        page_size: int = 50,
        viewer_user_id: int | None = None,
        viewer_role: str | None = None,
        include_unapproved: bool = False,
    ) -> tuple[list[Comment], int]:
        """获取帖子可见评论列表（后台管理用）"""
        if not include_unapproved or not viewer_user_id:
            return await ForumCommentService.get_comments(db, post_id, page, page_size)
        result = await db.execute(
            select(Comment)
            .options(joinedload(Comment.author))
            .where(
                and_(
                    Comment.post_id == post_id,
                    Comment.is_deleted == False,
                )
            )
            .order_by(desc(Comment.created_at))
        )

        all_comments = list(result.scalars().all())
        top_level = [c for c in all_comments if c.parent_id is None]
        total = len(top_level)

        start = max(0, (page - 1) * page_size)
        end = start + page_size
        page_top = top_level[start:end]

        children_by_parent: dict[int, list[Comment]] = {}
        for c in all_comments:
            if c.parent_id is None:
                continue
            children_by_parent.setdefault(int(c.parent_id), []).append(c)

        def _created_at_ts(value: Comment) -> float:
            created_at = getattr(value, "created_at", None)
            if isinstance(created_at, datetime):
                try:
                    return float(created_at.timestamp())
                except (OSError, ValueError, OverflowError):
                    return 0.0
            return 0.0

        for children in children_by_parent.values():
            children.sort(key=_created_at_ts)

        for parent_id, children in children_by_parent.items():
            children.sort(key=_created_at_ts)

        def attach_replies(node: Comment) -> None:
            replies = children_by_parent.get(int(node.id), [])
            # pyright: ignore[reportAttributeAccessIssue]
            setattr(node, "replies", replies)

        for node in page_top:
            attach_replies(node)

        return page_top, total

    @staticmethod
    async def delete_comment(db: AsyncSession, comment: Comment) -> None:
        """删除评论"""
        comment.is_deleted = True
        db.add(comment)

        if comment.review_status == "approved":
            _ = await db.execute(
                update(Post)
                .where(Post.id == comment.post_id)
                .values(comment_count=func.greatest(Post.comment_count - 1, 0))
            )

        await db.commit()

    @staticmethod
    async def restore_comment(db: AsyncSession, comment: Comment) -> Comment:
        """恢复评论"""
        comment.is_deleted = False
        db.add(comment)

        if comment.review_status == "approved":
            _ = await db.execute(
                update(Post)
                .where(Post.id == comment.post_id)
                .values(comment_count=func.coalesce(Post.comment_count, 0) + 1)
            )

        await db.commit()
        await db.refresh(comment)
        return comment

    @staticmethod
    async def get_comment(db: AsyncSession, comment_id: int) -> Comment | None:
        """获取评论详情"""
        approved_filter = or_(
            Comment.review_status.is_(None),
            Comment.review_status == "approved")
        result = await db.execute(
            select(Comment)
            .options(selectinload(Comment.author))
            .where(
                and_(
                    Comment.id == comment_id,
                    Comment.is_deleted == False,
                    approved_filter,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_comment_any(db: AsyncSession,
                              comment_id: int) -> Comment | None:
        """获取评论详情（包含已删除）"""
        result = await db.execute(
            select(Comment)
            .options(selectinload(Comment.author))
            .where(Comment.id == comment_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def is_comment_liked(
            db: AsyncSession, comment_id: int, user_id: int) -> bool:
        """检查用户是否已点赞评论"""
        result = await db.execute(
            select(CommentLike).where(
                CommentLike.comment_id == comment_id, CommentLike.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def toggle_comment_like(
            db: AsyncSession, comment_id: int, user_id: int) -> tuple[bool, int]:
        """切换评论点赞状态"""
        result = await db.execute(
            select(CommentLike).where(
                CommentLike.comment_id == comment_id, CommentLike.user_id == user_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            await db.delete(existing)
            await db.commit()
            return False, 0

        comment_like = CommentLike(comment_id=comment_id, user_id=user_id)
        db.add(comment_like)
        await db.commit()

        count_result = await db.execute(
            select(func.count(CommentLike.id)).where(
                CommentLike.comment_id == comment_id)
        )
        count = count_result.scalar() or 0

        return True, count


# 单例
forum_comment_service = ForumCommentService()
