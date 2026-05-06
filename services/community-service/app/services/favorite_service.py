"""帖子收藏服务"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException

from ..models import Post, PostFavorite


class FavoriteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_favorites(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[dict], int]:
        from sqlalchemy import func, desc

        query = select(PostFavorite).where(
            and_(
                PostFavorite.user_id == user_id
            )
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        query = query.order_by(desc(PostFavorite.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        favorites = result.scalars().all()

        post_ids = [f.post_id for f in favorites]
        if post_ids:
            posts_result = await self.db.execute(
                select(Post).where(Post.id.in_(post_ids))
            )
            posts = {p.id: p for p in posts_result.scalars().all()}
        else:
            posts = {}

        items = []
        for fav in favorites:
            post = posts.get(fav.post_id)
            if post:
                items.append({
                    "post": post,
                    "favorited_at": fav.created_at
                })

        return items, total

    async def is_favorited(self, post_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(PostFavorite).where(
                and_(
                    PostFavorite.post_id == post_id,
                    PostFavorite.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none() is not None
