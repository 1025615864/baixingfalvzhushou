"""热门内容服务"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from ..models import Post
from ..utils import calculate_hot_score, recalculate_post_hot_score
from ..cache import hot_cache


class HotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_hot_posts(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        use_cache: bool = True
    ) -> List[Post]:
        if use_cache:
            cached = await hot_cache.get_hot_posts(category)
            if cached:
                return cached

        query = select(Post).where(
            and_(
                Post.status == "published",
                Post.is_deleted == False
            )
        )

        if category:
            query = query.where(Post.category == category)

        query = query.order_by(desc(Post.hot_score)).limit(limit)
        result = await self.db.execute(query)
        posts = list(result.scalars().all())

        if use_cache and posts:
            post_dicts = [
                {
                    "id": p.id,
                    "title": p.title,
                    "author_name": p.author_name,
                    "is_lawyer": p.is_lawyer,
                    "like_count": p.like_count,
                    "comment_count": p.comment_count,
                    "hot_score": p.hot_score,
                }
                for p in posts
            ]
            await hot_cache.set_hot_posts(post_dicts, category)

        return posts

    async def update_hot_scores(self, post_ids: List[int] = None):
        if post_ids:
            query = select(Post).where(
                and_(
                    Post.id.in_(post_ids),
                    Post.status == "published"
                )
            )
        else:
            query = select(Post).where(
                Post.status == "published"
            )

        result = await self.db.execute(query)
        posts = result.scalars().all()

        for post in posts:
            post.hot_score = recalculate_post_hot_score(post)

        await self.db.commit()

        await hot_cache.invalidate()
