"""审核服务 - 人工审核队列"""
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from fastapi import HTTPException

from ..models.moderation import ModerationQueue
from ..models.post import Post
from ..models.comment import Comment
from ..middleware.auth import AuthUser


def utc_now():
    return datetime.now(timezone.utc)


class ModerationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_to_queue(
        self,
        content_type: str,
        content_id: int,
        content_preview: str,
        priority: int = 5,
        report_reason: Optional[str] = None,
        reporter_id: Optional[int] = None,
        ai_confidence: Optional[float] = None,
        ai_analysis: Optional[str] = None
    ) -> ModerationQueue:
        existing = await self.db.execute(
            select(ModerationQueue).where(
                and_(
                    ModerationQueue.content_type == content_type,
                    ModerationQueue.content_id == content_id,
                    ModerationQueue.status == "pending"
                )
            )
        )
        if existing.scalar_one_or_none():
            return existing.scalar_one_or_none()

        item = ModerationQueue(
            content_type=content_type,
            content_id=content_id,
            content_preview=content_preview[:500] if content_preview else None,
            priority=priority,
            report_reason=report_reason,
            reporter_id=reporter_id,
            ai_confidence=ai_confidence,
            ai_analysis=ai_analysis,
            status="pending"
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_queue(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> Tuple[List[ModerationQueue], int]:
        conditions = []
        if status:
            conditions.append(ModerationQueue.status == status)

        query = select(ModerationQueue)
        if conditions:
            query = query.where(and_(*conditions))

        count_query = select(func.count()).select_from(ModerationQueue)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        query = query.order_by(
            desc(ModerationQueue.priority),
            ModerationQueue.created_at
        )
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_queue_item(self, item_id: int) -> Optional[ModerationQueue]:
        result = await self.db.execute(
            select(ModerationQueue).where(ModerationQueue.id == item_id)
        )
        return result.scalar_one_or_none()

    async def review(
        self,
        item_id: int,
        decision: str,
        reviewer_id: int,
        reason: Optional[str] = None
    ) -> ModerationQueue:
        if decision not in ("approve", "reject", "modify"):
            raise HTTPException(status_code=400, detail="无效的审核决定")

        item = await self.get_queue_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="审核项不存在")

        if item.status != "pending":
            raise HTTPException(status_code=400, detail="该项已审核过")

        item.status = "reviewed"
        item.review_decision = decision
        item.reviewed_by = reviewer_id
        item.review_reason = reason
        item.reviewed_at = utc_now()

        if decision == "approve":
            await self._approve_content(item)
        elif decision == "reject":
            await self._reject_content(item)

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def _approve_content(self, item: ModerationQueue):
        if item.content_type == "post":
            result = await self.db.execute(
                select(Post).where(Post.id == item.content_id)
            )
            post = result.scalar_one_or_none()
            if post and post.status == "pending_review":
                post.status = "published"
                post.updated_at = utc_now()
        elif item.content_type == "comment":
            result = await self.db.execute(
                select(Comment).where(Comment.id == item.content_id)
            )
            comment = result.scalar_one_or_none()
            if comment and comment.status == "pending_review":
                comment.status = "published"
                comment.updated_at = utc_now()

    async def _reject_content(self, item: ModerationQueue):
        if item.content_type == "post":
            result = await self.db.execute(
                select(Post).where(Post.id == item.content_id)
            )
            post = result.scalar_one_or_none()
            if post:
                post.status = "rejected"
                post.updated_at = utc_now()
        elif item.content_type == "comment":
            result = await self.db.execute(
                select(Comment).where(Comment.id == item.content_id)
            )
            comment = result.scalar_one_or_none()
            if comment:
                comment.status = "rejected"
                comment.updated_at = utc_now()

    async def get_stats(self) -> dict:
        pending_count = await self.db.execute(
            select(func.count()).select_from(ModerationQueue).where(
                ModerationQueue.status == "pending"
            )
        )
        reviewed_count = await self.db.execute(
            select(func.count()).select_from(ModerationQueue).where(
                ModerationQueue.status == "reviewed"
            )
        )
        approved_count = await self.db.execute(
            select(func.count()).select_from(ModerationQueue).where(
                and_(
                    ModerationQueue.status == "reviewed",
                    ModerationQueue.review_decision == "approve"
                )
            )
        )
        rejected_count = await self.db.execute(
            select(func.count()).select_from(ModerationQueue).where(
                and_(
                    ModerationQueue.status == "reviewed",
                    ModerationQueue.review_decision == "reject"
                )
            )
        )

        total = pending_count.scalar() + reviewed_count.scalar()
        approval_rate = (approved_count.scalar() / reviewed_count.scalar() * 100) if reviewed_count.scalar() > 0 else 0

        return {
            "total": total,
            "pending": pending_count.scalar(),
            "reviewed": reviewed_count.scalar(),
            "approved": approved_count.scalar(),
            "rejected": rejected_count.scalar(),
            "approval_rate": round(approval_rate, 2)
        }

    async def auto_submit_for_review(
        self,
        content_type: str,
        content_id: int,
        content_preview: str,
        ai_confidence: float,
        ai_analysis: str
    ):
        if 0.5 <= ai_confidence < 0.9:
            priority = 3
        elif ai_confidence >= 0.9:
            priority = 1
        else:
            priority = 5

        await self.add_to_queue(
            content_type=content_type,
            content_id=content_id,
            content_preview=content_preview,
            priority=priority,
            ai_confidence=ai_confidence,
            ai_analysis=ai_analysis
        )
