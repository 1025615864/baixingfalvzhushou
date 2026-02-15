"""新闻评论服务

提供新闻评论 CRUD 和管理功能
"""
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.news import NewsComment
from ...schemas.news import NewsCommentCreate


logger = logging.getLogger(__name__)


class NewsCommentService:
    """新闻评论服务"""

    async def create_comment(
            self,
            db: AsyncSession,
            news_id: int,
            user_id: int,
            data: NewsCommentCreate) -> NewsComment:
        """创建评论"""
        comment = NewsComment(
            news_id=news_id,
            user_id=user_id,
            content=data.content,
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment

    async def get_comment(self, db: AsyncSession,
                          comment_id: int) -> NewsComment | None:
        """获取评论"""
        result = await db.execute(select(NewsComment).where(NewsComment.id == comment_id))
        return result.scalar_one_or_none()

    async def delete_comment(self, db: AsyncSession,
                             comment: NewsComment) -> None:
        """删除评论"""
        await db.delete(comment)
        await db.commit()

    async def get_comments(
        self,
        db: AsyncSession,
        news_id: int,
        page: int = 1,
        page_size: int = 20,
        parent_id: int | None = None,
    ) -> tuple[list[NewsComment], int]:
        """获取评论列表"""
        query = select(NewsComment).where(NewsComment.news_id == news_id)
        count_query = select(
            func.count(
                NewsComment.id)).where(
            NewsComment.news_id == news_id)

        if parent_id is not None:
            query = query.where(NewsComment.id == parent_id)
            count_query = count_query.where(NewsComment.id == parent_id)
        else:
            query = query.where(NewsComment.id is None)
            count_query = count_query.where(NewsComment.id is None)

        query = query.order_by(
            NewsComment.created_at.desc()).offset(
            (page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        comments = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return comments, total

    async def list_comments_admin(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        review_status: str | None = None,
    ) -> tuple[list[NewsComment], int]:
        """管理后台评论列表"""
        query = select(NewsComment)
        count_query = select(func.count(NewsComment.id))

        if keyword:
            pattern = f"%{keyword}%"
            query = query.where(NewsComment.content.ilike(pattern))
            count_query = count_query.where(NewsComment.content.ilike(pattern))

        if review_status:
            query = query.where(NewsComment.review_status == review_status)
            count_query = count_query.where(
                NewsComment.review_status == review_status)

        query = query.order_by(
            NewsComment.created_at.desc()).offset(
            (page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        comments = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return comments, total

    async def review_comment_admin(
            self,
            db: AsyncSession,
            comment: NewsComment,
            action: str,
            reason: str | None = None) -> NewsComment:
        """审核评论（管理员）"""
        comment.review_status = action
        comment.review_reason = reason

        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment


# 单例
news_comment_service = NewsCommentService()
