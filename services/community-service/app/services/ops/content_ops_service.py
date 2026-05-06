"""内容审核工作台服务"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from app.models.moderation import ModerationQueue
from app.models.post import Post
from app.models.comment import Comment
from app.models.user_penalty import UserPenalty


class ContentOpsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_review_queue(
        self,
        status: str = None,
        priority: str = None,
        assigned_to: int = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        conditions = []
        if status:
            conditions.append(ModerationQueue.status == status)
        if priority:
            conditions.append(ModerationQueue.priority == priority)
        if assigned_to is not None:
            conditions.append(ModerationQueue.assigned_to == assigned_to)

        query = select(ModerationQueue)
        if conditions:
            query = query.where(and_(*conditions))

        from sqlalchemy import func
        count_result = await self.db.execute(
            select(func.count()).select_from(ModerationQueue)
            .where(and_(*conditions)) if conditions else select(func.count()).select_from(ModerationQueue)
        )
        total = count_result.scalar() or 0

        query = query.order_by(
            ModerationQueue.priority.desc(),
            ModerationQueue.created_at.asc()
        )
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = []
        for row in result.scalars().all():
            items.append({
                "id": row.id,
                "content_type": row.content_type,
                "content_id": row.content_id,
                "content_preview": row.content_preview[:100] if row.content_preview else None,
                "priority": row.priority,
                "status": row.status,
                "assigned_to": row.assigned_to,
                "ai_confidence": row.ai_confidence,
                "ai_analysis": row.ai_analysis,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })

        return items, total

    async def get_review_detail(self, queue_id: int) -> Optional[Dict[str, Any]]:
        result = await self.db.execute(
            select(ModerationQueue).where(ModerationQueue.id == queue_id)
        )
        queue = result.scalar_one_or_none()
        if not queue:
            return None

        content = None
        if queue.content_type == "post" and queue.content_id:
            post_result = await self.db.execute(
                select(Post).where(Post.id == queue.content_id)
            )
            post = post_result.scalar_one_or_none()
            if post:
                content = {
                    "type": "post",
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "author_id": post.user_id,
                    "author_name": post.author_name,
                    "created_at": post.created_at.isoformat() if post.created_at else None
                }
        elif queue.content_type == "comment" and queue.content_id:
            comment_result = await self.db.execute(
                select(Comment).where(Comment.id == queue.content_id)
            )
            comment = comment_result.scalar_one_or_none()
            if comment:
                content = {
                    "type": "comment",
                    "id": comment.id,
                    "content": comment.content,
                    "author_id": comment.user_id,
                    "author_name": comment.author_name,
                    "post_id": comment.post_id,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None
                }

        violation_count_result = await self.db.execute(
            select(UserPenalty).where(
                UserPenalty.user_id == (content.get("author_id") if content else 0),
                UserPenalty.is_active == True
            )
        )
        violation_count = len(violation_count_result.scalars().all())

        return {
            "id": queue.id,
            "content": content,
            "content_type": queue.content_type,
            "content_id": queue.content_id,
            "priority": queue.priority,
            "status": queue.status,
            "assigned_to": queue.assigned_to,
            "ai_confidence": queue.ai_confidence,
            "ai_analysis": queue.ai_analysis,
            "created_at": queue.created_at.isoformat() if queue.created_at else None,
            "author_violation_count": violation_count
        }

    async def review_content(
        self,
        queue_id: int,
        action: str,
        reason: str = None,
        modified_content: str = None,
        penalty: str = None,
        operator_id: int = 0,
        operator_role: str = "content_mod"
    ) -> Dict[str, Any]:
        result = await self.db.execute(
            select(ModerationQueue).where(ModerationQueue.id == queue_id)
        )
        queue = result.scalar_one_or_none()
        if not queue:
            return {"success": False, "error": "审核项不存在"}

        queue.status = "reviewed"
        queue.review_decision = action
        queue.review_reason = reason
        queue.reviewed_by = operator_id
        queue.reviewed_at = datetime.now()

        if modified_content and action == "modify":
            if queue.content_type == "post":
                await self.db.execute(
                    update(Post)
                    .where(Post.id == queue.content_id)
                    .values(content=modified_content)
                )
            elif queue.content_type == "comment":
                await self.db.execute(
                    update(Comment)
                    .where(Comment.id == queue.content_id)
                    .values(content=modified_content)
                )

        if action == "reject" and penalty:
            author_id = None
            if queue.content_type == "post":
                post_result = await self.db.execute(
                    select(Post).where(Post.id == queue.content_id)
                )
                post = post_result.scalar_one_or_none()
                if post:
                    author_id = post.user_id
            elif queue.content_type == "comment":
                comment_result = await self.db.execute(
                    select(Comment).where(Comment.id == queue.content_id)
                )
                comment = comment_result.scalar_one_or_none()
                if comment:
                    author_id = comment.user_id

            if author_id:
                duration_hours = None
                expires_at = None
                if penalty == "mute_1d":
                    duration_hours = 24
                    expires_at = datetime.now() + timedelta(hours=24)
                elif penalty == "mute_7d":
                    duration_hours = 168
                    expires_at = datetime.now() + timedelta(hours=168)

                user_penalty = UserPenalty(
                    user_id=author_id,
                    type=penalty,
                    reason=reason,
                    related_post_id=queue.content_id if queue.content_type == "post" else None,
                    related_comment_id=queue.content_id if queue.content_type == "comment" else None,
                    operator_id=operator_id,
                    duration_hours=duration_hours,
                    expires_at=expires_at,
                    is_active=True
                )
                self.db.add(user_penalty)

        await self.db.commit()
        return {"success": True, "action": action}

    async def batch_review(
        self,
        queue_ids: List[int],
        action: str,
        reason: str = None,
        operator_id: int = 0,
        operator_role: str = "content_mod"
    ) -> Dict[str, Any]:
        success_count = 0
        for queue_id in queue_ids:
            result = await self.review_content(
                queue_id=queue_id,
                action=action,
                reason=reason,
                operator_id=operator_id,
                operator_role=operator_role
            )
            if result.get("success"):
                success_count += 1

        return {"success_count": success_count, "total": len(queue_ids)}

    async def assign_reviewer(self, queue_id: int, assignee_id: int, operator_id: int):
        await self.db.execute(
            update(ModerationQueue)
            .where(ModerationQueue.id == queue_id)
            .values(assigned_to=assignee_id)
        )
        await self.db.commit()

    async def get_moderation_stats(self) -> Dict[str, Any]:
        from sqlalchemy import func

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)

        pending_result = await self.db.execute(
            select(func.count()).select_from(ModerationQueue)
            .where(ModerationQueue.status == "pending")
        )
        pending_count = pending_result.scalar() or 0

        reviewed_today_result = await self.db.execute(
            select(func.count()).select_from(ModerationQueue)
            .where(
                ModerationQueue.status == "reviewed",
                ModerationQueue.reviewed_at >= today
            )
        )
        reviewed_today = reviewed_today_result.scalar() or 0

        approved_result = await self.db.execute(
            select(func.count()).select_from(ModerationQueue)
            .where(
                ModerationQueue.status == "reviewed",
                ModerationQueue.review_decision == "approve",
                ModerationQueue.reviewed_at >= today
            )
        )
        approved_today = approved_result.scalar() or 0

        approved_rate = approved_today / reviewed_today if reviewed_today > 0 else 0

        return {
            "total_pending": pending_count,
            "reviewed_today": reviewed_today,
            "approved_today": approved_today,
            "approved_rate": round(approved_rate, 2)
        }
