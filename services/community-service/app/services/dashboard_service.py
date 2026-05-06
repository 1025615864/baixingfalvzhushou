"""数据看板服务"""
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.post import Post
from ..models.comment import Comment
from ..models.topic import Topic, ModerationQueue


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview_stats(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)

        total_posts = await self.db.execute(
            select(func.count()).select_from(Post).where(Post.status != "deleted")
        )
        total_posts = total_posts.scalar() or 0

        published_posts = await self.db.execute(
            select(func.count()).select_from(Post).where(Post.status == "published")
        )
        published_posts = published_posts.scalar() or 0

        today_posts = await self.db.execute(
            select(func.count()).select_from(Post).where(
                and_(
                    Post.created_at >= today_start,
                    Post.status != "deleted"
                )
            )
        )
        today_posts = today_posts.scalar() or 0

        week_posts = await self.db.execute(
            select(func.count()).select_from(Post).where(
                and_(
                    Post.created_at >= week_ago,
                    Post.status != "deleted"
                )
            )
        )
        week_posts = week_posts.scalar() or 0

        total_comments = await self.db.execute(
            select(func.count()).select_from(Comment)
        )
        total_comments = total_comments.scalar() or 0

        pending_moderation = await self.db.execute(
            select(func.count()).select_from(ModerationQueue).where(
                ModerationQueue.status == "pending"
            )
        )
        pending_moderation = pending_moderation.scalar() or 0

        return {
            "posts": {
                "total": total_posts,
                "published": published_posts,
                "today": today_posts,
                "this_week": week_posts
            },
            "comments": {
                "total": total_comments
            },
            "moderation": {
                "pending": pending_moderation
            }
        }

    async def get_trending_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(Topic, func.count(Post.id).label("post_count"))
            .join(Post, Post.category == Topic.name, isouter=True)
            .group_by(Topic.id)
            .order_by(desc("post_count"))
            .limit(limit)
        )
        topics = result.all()

        return [
            {
                "id": topic.id,
                "name": topic.name,
                "description": topic.description,
                "post_count": post_count
            }
            for topic, post_count in topics
        ]

    async def get_user_activity_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)

        result = await self.db.execute(
            select(
                func.date(Post.created_at).label("date"),
                func.count(Post.id).label("count")
            )
            .where(
                and_(
                    Post.created_at >= start_date,
                    Post.status == "published"
                )
            )
            .group_by(func.date(Post.created_at))
            .order_by("date")
        )

        return [
            {"date": str(row.date), "count": row.count}
            for row in result.all()
        ]

    async def get_top_posts(self, metric: str = "views", limit: int = 10) -> List[Dict[str, Any]]:
        if metric == "views":
            order_col = Post.view_count
        elif metric == "likes":
            order_col = Post.like_count
        elif metric == "comments":
            order_col = Post.comment_count
        elif metric == "hot":
            order_col = Post.hot_score
        else:
            order_col = Post.created_at

        result = await self.db.execute(
            select(Post)
            .where(Post.status == "published")
            .order_by(desc(order_col))
            .limit(limit)
        )
        posts = result.scalars().all()

        return [
            {
                "id": post.id,
                "title": post.title[:50] + "..." if len(post.title) > 50 else post.title,
                "views": post.view_count,
                "likes": post.like_count,
                "comments": post.comment_count,
                "hot_score": round(post.hot_score, 2)
            }
            for post in posts
        ]

    async def get_category_distribution(self) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(
                Post.category,
                func.count(Post.id).label("count")
            )
            .where(Post.status == "published")
            .group_by(Post.category)
            .order_by(desc("count"))
        )

        total = sum(row.count for row in result.all())

        result = await self.db.execute(
            select(
                Post.category,
                func.count(Post.id).label("count")
            )
            .where(Post.status == "published")
            .group_by(Post.category)
            .order_by(desc("count"))
        )

        return [
            {
                "category": row.category or "uncategorized",
                "count": row.count,
                "percentage": round(row.count / total * 100, 2) if total > 0 else 0
            }
            for row in result.all()
        ]
