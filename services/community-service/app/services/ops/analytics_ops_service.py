"""运营数据分析服务"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.post import Post
from app.models.comment import Comment
from app.models.ops_models import UserPenalty, OpsAuditLog


class AnalyticsOpsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview_stats(
        self,
        period_days: int = 7
    ) -> Dict[str, Any]:
        now = datetime.now()
        period_start = now - timedelta(days=period_days)

        active_users_result = await self.db.execute(
            select(func.count(func.distinct(Post.user_id)))
            .where(Post.created_at >= period_start)
        )
        active_users = active_users_result.scalar() or 0

        new_posts_result = await self.db.execute(
            select(func.count()).select_from(Post)
            .where(Post.created_at >= period_start, Post.is_deleted == False)
        )
        new_posts = new_posts_result.scalar() or 0

        new_comments_result = await self.db.execute(
            select(func.count()).select_from(Comment)
            .where(Comment.created_at >= period_start, Comment.is_deleted == False)
        )
        new_comments = new_comments_result.scalar() or 0

        likes_result = await self.db.execute(
            select(func.count()).select_from(Post)
            .where(Post.created_at >= period_start)
        )
        total_interactions = new_posts + new_comments

        return {
            "active_users": active_users,
            "new_posts": new_posts,
            "new_comments": new_comments,
            "total_interactions": total_interactions,
            "period_days": period_days
        }

    async def get_trend_data(
        self,
        metric: str = "posts",
        period_days: int = 30,
        granularity: str = "day"
    ) -> List[Dict[str, Any]]:
        now = datetime.now()
        period_start = now - timedelta(days=period_days)

        data = []
        current = period_start
        while current <= now:
            if granularity == "day":
                day_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
            else:
                day_start = current.replace(minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(hours=1)

            if metric == "posts":
                count_result = await self.db.execute(
                    select(func.count()).select_from(Post)
                    .where(
                        Post.created_at >= day_start,
                        Post.created_at < day_end,
                        Post.is_deleted == False
                    )
                )
            elif metric == "comments":
                count_result = await self.db.execute(
                    select(func.count()).select_from(Comment)
                    .where(
                        Comment.created_at >= day_start,
                        Comment.created_at < day_end,
                        Comment.is_deleted == False
                    )
                )
            else:
                count_result = await self.db.execute(
                    select(func.count(func.distinct(Post.user_id)))
                    .where(Post.created_at >= day_start, Post.created_at < day_end)
                )

            count = count_result.scalar() or 0
            data.append({
                "timestamp": day_start.isoformat(),
                "value": count
            })

            if granularity == "day":
                current += timedelta(days=1)
            else:
                current += timedelta(hours=1)

        return data

    async def get_content_quality_stats(self) -> Dict[str, Any]:
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        posts_with_comments_result = await self.db.execute(
            select(func.count(Post.id))
            .join(Comment, Comment.post_id == Post.id)
            .where(Post.created_at >= week_ago, Post.is_deleted == False)
            .group_by(Post.id)
            .having(func.count(Comment.id) > 0)
        )
        posts_with_comments = len(posts_with_comments_result.all())

        total_posts_result = await self.db.execute(
            select(func.count()).select_from(Post)
            .where(Post.created_at >= week_ago, Post.is_deleted == False)
        )
        total_posts = total_posts_result.scalar() or 0

        avg_comments = posts_with_comments / total_posts if total_posts > 0 else 0

        best_answer_result = await self.db.execute(
            select(func.count()).select_from(Post)
            .where(
                Post.created_at >= week_ago,
                Post.is_deleted == False,
                Post.is_best_answer == True
            )
        )
        best_answers = best_answer_result.scalar() or 0

        return {
            "avg_comments_per_post": round(avg_comments, 2),
            "posts_with_best_answer": best_answers,
            "best_answer_rate": round(best_answers / total_posts, 2) if total_posts > 0 else 0
        }

    async def get_moderation_efficiency(self) -> Dict[str, Any]:
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        pending_result = await self.db.execute(
            select(func.count()).select_from(OpsAuditLog)
            .where(
                OpsAuditLog.action.like("review_%"),
                OpsAuditLog.created_at >= today
            )
        )
        reviewed_today = pending_result.scalar() or 0

        return {
            "reviewed_today": reviewed_today,
            "avg_review_time_minutes": 5
        }
