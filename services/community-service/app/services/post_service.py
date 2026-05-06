"""帖子服务 - 业务逻辑层"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from fastapi import HTTPException

from ..models.post import Post, PostLike, PostFavorite
from ..middleware.auth import AuthUser
from ..utils import calculate_hot_score


def utc_now():
    return datetime.now(timezone.utc)


class PostService:
    def __init__(self, db: AsyncSession, user_client=None, event_bus=None, cache=None):
        self.db = db
        self.user_client = user_client
        self.event_bus = event_bus
        self.cache = cache

    async def create_post(
        self,
        user_id: int,
        title: str,
        content: str,
        category: Optional[str] = "general",
        tags: Optional[List[str]] = None,
        moderation_service=None
    ) -> Post:
        from .ops.user_ops_service import UserOpsService
        ops_service = UserOpsService(self.db)
        if await ops_service.is_user_penalized(user_id, ["mute", "ban"]):
            raise HTTPException(status_code=403, detail="您因违规已被禁言或封禁，无法发帖")

        if moderation_service:
            mod_result = await moderation_service.check_content(title + content)
            if mod_result.blocked:
                raise HTTPException(status_code=400, detail=mod_result.reason)
            if mod_result.needs_review:
                status = "pending_review"
            else:
                status = "published"
        else:
            status = "published"

        user_info = None
        if self.user_client:
            user_info = await self.user_client.get_user_info(user_id)

        author_name = user_info.get("nickname") if user_info else f"用户{user_id}"
        author_avatar = user_info.get("avatar") if user_info else None
        is_lawyer = user_info.get("is_lawyer", False) if user_info else False

        post = Post(
            user_id=user_id,
            author_name=author_name,
            author_avatar=author_avatar,
            is_lawyer=is_lawyer,
            title=title,
            content=content,
            category=category,
            status=status,
            hot_score=0.0
        )

        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)

        if self.event_bus:
            await self.event_bus.publish_post_created(post)

        return post

    async def get_post(self, post_id: int) -> Optional[Post]:
        cached = None
        if self.cache:
            cached = await self.cache.get_post_detail(post_id)

        result = await self.db.execute(
            select(Post).where(
                and_(Post.id == post_id, Post.status != "deleted")
            )
        )
        post = result.scalar_one_or_none()

        if not post:
            return None

        if not cached:
            post.view_count += 1
            post.hot_score = calculate_hot_score(
                likes=post.like_count,
                comments=post.comment_count,
                views=post.view_count,
                favorites=post.favorite_count,
                is_lawyer_post=post.is_lawyer,
                created_at=post.created_at
            )
            await self.db.commit()

            if self.cache:
                await self.cache.set_post_detail(post_id, {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "author_name": post.author_name,
                    "view_count": post.view_count,
                    "like_count": post.like_count,
                    "comment_count": post.comment_count,
                })
        else:
            post.view_count += 1
            await self.db.commit()

        return post

    async def update_post(
        self,
        post_id: int,
        current_user: AuthUser,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None
    ) -> Post:
        result = await self.db.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        if post.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="无权修改此帖子")

        if title is not None:
            post.title = title
        if content is not None:
            post.content = content
        if category is not None:
            post.category = category

        post.updated_at = utc_now()
        await self.db.commit()
        await self.db.refresh(post)

        if self.cache:
            await self.cache.invalidate_post(post_id)
            await self.cache.invalidate_post_list(post.category)

        if self.event_bus:
            await self.event_bus.publish_post_updated(post)

        return post

    async def delete_post(self, post_id: int, current_user: AuthUser) -> bool:
        result = await self.db.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        if post.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="无权删除此帖子")

        post.status = "deleted"
        post.is_deleted = True
        post.deleted_at = utc_now()
        await self.db.commit()

        if self.cache:
            await self.cache.invalidate_post(post_id)
            await self.cache.invalidate_post_list(post.category)

        if self.event_bus:
            await self.event_bus.publish_post_deleted(post)

        return True

    async def like_post(self, post_id: int, user_id: int) -> dict:
        result = await self.db.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        existing_like = await self.db.execute(
            select(PostLike).where(
                and_(
                    PostLike.post_id == post_id,
                    PostLike.user_id == user_id
                )
            )
        )
        existing = existing_like.scalar_one_or_none()

        if existing:
            post.like_count = max(0, post.like_count - 1)
            await self.db.delete(existing)
            action = "unliked"
            if self.cache:
                await self.cache.decr_like_count(post_id)
        else:
            like = PostLike(post_id=post_id, user_id=user_id)
            self.db.add(like)
            post.like_count += 1
            action = "liked"
            if self.cache:
                await self.cache.incr_like_count(post_id)

        post.hot_score = calculate_hot_score(
            likes=post.like_count,
            comments=post.comment_count,
            views=post.view_count,
            favorites=post.favorite_count,
            is_lawyer_post=post.is_lawyer,
            created_at=post.created_at
        )

        await self.db.commit()

        if self.event_bus and action == "liked":
            await self.event_bus.publish_post_liked(post, user_id)

        return {"action": action, "like_count": post.like_count}

    async def favorite_post(self, post_id: int, user_id: int) -> dict:
        result = await self.db.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        existing = await self.db.execute(
            select(PostFavorite).where(
                and_(
                    PostFavorite.post_id == post_id,
                    PostFavorite.user_id == user_id
                )
            )
        )
        favorite = existing.scalar_one_or_none()

        if favorite:
            post.favorite_count = max(0, post.favorite_count - 1)
            await self.db.delete(favorite)
            action = "unfavorited"
        else:
            fav = PostFavorite(post_id=post_id, user_id=user_id)
            self.db.add(fav)
            post.favorite_count += 1
            action = "favorited"

        post.hot_score = calculate_hot_score(
            likes=post.like_count,
            comments=post.comment_count,
            views=post.view_count,
            favorites=post.favorite_count,
            is_lawyer_post=post.is_lawyer,
            created_at=post.created_at
        )

        await self.db.commit()

        if self.event_bus and action == "favorited":
            await self.event_bus.publish_post_favorited(post, user_id)

        return {"action": action, "favorite_count": post.favorite_count}

    async def get_user_posts(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Post], int]:
        query = select(Post).where(
            and_(
                Post.user_id == user_id,
                Post.status != "deleted"
            )
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        query = query.order_by(desc(Post.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        posts = result.scalars().all()

        return list(posts), total

    async def list_posts(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        user_id: Optional[int] = None,
        sort_by: str = "latest"
    ) -> tuple[List[Post], int]:
        conditions = [Post.status == "published"]

        if category:
            conditions.append(Post.category == category)
        if user_id:
            conditions.append(Post.user_id == user_id)

        query = select(Post).where(and_(*conditions))

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        if sort_by == "hot":
            query = query.order_by(
                desc(Post.is_pinned),
                desc(Post.hot_score),
                desc(Post.created_at)
            )
        elif sort_by == "featured":
            query = query.where(Post.is_featured == True)
            query = query.order_by(
                desc(Post.is_pinned),
                desc(Post.hot_score),
                desc(Post.created_at)
            )
        elif sort_by == "latest":
            query = query.order_by(
                desc(Post.is_pinned),
                desc(Post.created_at)
            )
        else:
            query = query.order_by(desc(Post.created_at))

        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        posts = result.scalars().all()

        return list(posts), total

    async def get_hot_posts(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Post]:
        conditions = [
            Post.status == "published",
            Post.hot_score > 0
        ]

        if category:
            conditions.append(Post.category == category)

        query = select(Post).where(and_(*conditions))
        query = query.order_by(desc(Post.hot_score)).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_posts(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None
    ) -> tuple[List[Post], int]:
        if not keyword or len(keyword.strip()) < 2:
            raise HTTPException(status_code=400, detail="搜索关键词至少2个字符")

        keyword = keyword.strip()

        if category:
            search_query = select(Post).where(
                and_(
                    Post.status == "published",
                    Post.search_vector.op('@@')(
                        func.plainto_tsquery('simple', keyword)
                    ),
                    Post.category == category
                )
            )
        else:
            search_query = select(Post).where(
                and_(
                    Post.status == "published",
                    Post.search_vector.op('@@')(
                        func.plainto_tsquery('simple', keyword)
                    )
                )
            )

        count_query = select(func.count()).select_from(search_query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        search_query = search_query.order_by(
            desc(func.ts_rank(Post.search_vector, func.plainto_tsquery('simple', keyword)))
        )
        search_query = search_query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(search_query)
        return list(result.scalars().all()), total

    async def list_posts_cursor(
        self,
        cursor: Optional[str] = None,
        limit: int = 20,
        category: Optional[str] = None,
        sort_by: str = "latest"
    ) -> tuple[List[Post], Optional[str], bool]:
        conditions = [Post.status == "published"]

        if category:
            conditions.append(Post.category == category)

        if cursor:
            try:
                cursor_id = int(cursor)
                if sort_by == "latest":
                    conditions.append(Post.id < cursor_id)
            except ValueError:
                pass

        query = select(Post).where(and_(*conditions))

        if sort_by == "hot":
            query = query.order_by(
                desc(Post.is_pinned),
                desc(Post.hot_score),
                desc(Post.id)
            )
        elif sort_by == "featured":
            query = query.where(Post.is_featured == True)
            query = query.order_by(
                desc(Post.is_pinned),
                desc(Post.hot_score),
                desc(Post.id)
            )
        else:
            query = query.order_by(
                desc(Post.is_pinned),
                desc(Post.id)
            )

        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        posts = list(result.scalars().all())

        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]

        next_cursor = str(posts[-1].id) if posts else None

        return posts, next_cursor, has_more
