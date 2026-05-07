"""评论服务 - 服务层"""
from typing import List, Tuple, Optional
from datetime import datetime

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NewsComment


class CommentService:
    """新闻评论服务"""

    async def list_comments(
        self,
        session: AsyncSession,
        news_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str = "approved",
    ) -> Tuple[List[NewsComment], int]:
        """获取新闻评论列表"""
        query = select(NewsComment).where(
            NewsComment.news_id == news_id,
            NewsComment.status == status,
        ).order_by(desc(NewsComment.created_at))

        # 总数
        count_query = select(func.count()).where(
            NewsComment.news_id == news_id,
            NewsComment.status == status,
        )
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(query)
        comments = result.scalars().all()

        return list(comments), total

    async def create_comment(
        self,
        session: AsyncSession,
        news_id: int,
        user_id: int,
        content: str,
    ) -> NewsComment:
        """创建评论"""
        comment = NewsComment(
            news_id=news_id,
            user_id=user_id,
            content=content,
            status="pending",
        )
        session.add(comment)
        await session.flush()
        return comment

    async def get_comment(
        self,
        session: AsyncSession,
        comment_id: int,
    ) -> Optional[NewsComment]:
        """获取评论详情"""
        query = select(NewsComment).where(NewsComment.id == comment_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def approve_comment(
        self,
        session: AsyncSession,
        comment_id: int,
    ) -> bool:
        """审核通过评论"""
        comment = await self.get_comment(session, comment_id)
        if not comment:
            raise ValueError(f"Comment {comment_id} not found")

        comment.status = "approved"
        await session.flush()
        return True

    async def reject_comment(
        self,
        session: AsyncSession,
        comment_id: int,
    ) -> bool:
        """审核拒绝评论"""
        comment = await self.get_comment(session, comment_id)
        if not comment:
            raise ValueError(f"Comment {comment_id} not found")

        comment.status = "rejected"
        await session.flush()
        return True

    async def delete_comment(
        self,
        session: AsyncSession,
        comment_id: int,
    ) -> bool:
        """删除评论"""
        comment = await self.get_comment(session, comment_id)
        if not comment:
            raise ValueError(f"Comment {comment_id} not found")

        await session.delete(comment)
        await session.flush()
        return True


comment_service = CommentService()
