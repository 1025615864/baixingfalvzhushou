"""论坛帖子服务

提供帖子 CRUD 和互动功能
"""
import json
import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.forum import Post, Comment, PostLike, PostFavorite, PostReaction, CommentLike
from ...schemas.forum import PostCreate, PostUpdate, CommentCreate
from .core import ForumService, forum_service


logger = logging.getLogger(__name__)


class ForumPostService:
    """论坛帖子服务"""

    @staticmethod
    async def create_post(db: AsyncSession, user_id: int,
                          post_data: PostCreate) -> Post:
        """创建帖子"""
        from ...utils.content_filter import needs_review

        images_json = json.dumps(
            post_data.images) if post_data.images else None
        attachments_json = json.dumps(
            post_data.attachments) if post_data.attachments else None

        _ = await ForumService.apply_content_filter_config_from_db(db)

        requires_review = False
        review_reason: str | None = None

        review_enabled = await ForumService.is_post_review_enabled(db)
        if not review_enabled:
            review_status = "approved"
        else:
            review_mode = await ForumService.get_post_review_mode(db)
            if review_mode == "all":
                requires_review = True
                review_reason = "全量审核"
                review_status = "pending"
            else:
                requires_review, review_reason = needs_review(
                    f"{post_data.title}\n{post_data.content}")
                review_status = "pending" if requires_review else "approved"

        post = Post(
            title=post_data.title,
            content=post_data.content,
            category=post_data.category,
            user_id=user_id,
            cover_image=post_data.cover_image,
            images=images_json,
            attachments=attachments_json,
            review_status=review_status,
            review_reason=review_reason if requires_review else None,
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    @staticmethod
    async def get_post(db: AsyncSession, post_id: int) -> Post | None:
        """获取帖子详情"""
        approved_filter = or_(
            Post.review_status.is_(None),
            Post.review_status == "approved")
        result = await db.execute(
            select(Post)
            .options(selectinload(Post.author))
            .where(and_(Post.id == post_id, Post.is_deleted == False, approved_filter))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_post_any(db: AsyncSession, post_id: int) -> Post | None:
        """获取帖子详情（包含已删除）"""
        result = await db.execute(
            select(Post)
            .options(selectinload(Post.author))
            .where(Post.id == post_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_posts(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        keyword: str | None = None,
        is_essence: bool | None = None,
        include_deleted: bool = False,
        deleted: bool | None = None,
        approved_only: bool = True,
    ) -> tuple[list[Post], int]:
        """获取帖子列表"""
        query = select(Post).options(selectinload(Post.author))
        count_query = select(func.count(Post.id))

        if deleted is True:
            query = query.where(Post.is_deleted)
            count_query = count_query.where(Post.is_deleted)
        elif deleted is False:
            query = query.where(Post.is_deleted == False)
            count_query = count_query.where(Post.is_deleted == False)
        else:
            if not include_deleted:
                query = query.where(Post.is_deleted == False)
                count_query = count_query.where(Post.is_deleted == False)

        if approved_only and deleted is not True:
            approved_filter = or_(
                Post.review_status.is_(None),
                Post.review_status == "approved")
            query = query.where(approved_filter)
            count_query = count_query.where(approved_filter)

        if category:
            query = query.where(Post.category == category)
            count_query = count_query.where(Post.category == category)

        if keyword:
            search_filter = Post.title.contains(
                keyword) | Post.content.contains(keyword)
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if is_essence is True:
            query = query.where(Post.is_essence)
            count_query = count_query.where(Post.is_essence)
        elif is_essence is False:
            query = query.where(Post.is_essence == False)
            count_query = count_query.where(Post.is_essence == False)

        query = query.order_by(desc(Post.is_pinned), desc(Post.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        posts = result.scalars().all()

        count_result = await db.execute(count_query)
        total = int(count_result.scalar() or 0)

        return list(posts), total

    @staticmethod
    async def get_user_deleted_posts(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        keyword: str | None = None,
    ) -> tuple[list[Post], int]:
        """获取用户删除的帖子列表（回收站）"""
        query = (
            select(Post)
            .options(selectinload(Post.author))
            .where(and_(Post.user_id == user_id, Post.is_deleted))
        )
        count_query = select(
            func.count(
                Post.id)).where(
            and_(
                Post.user_id == user_id,
                Post.is_deleted))

        if category:
            query = query.where(Post.category == category)
            count_query = count_query.where(Post.category == category)

        if keyword:
            search_filter = Post.title.contains(
                keyword) | Post.content.contains(keyword)
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        query = query.order_by(desc(Post.updated_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        posts = result.scalars().all()

        count_result = await db.execute(count_query)
        total = int(count_result.scalar() or 0)

        return list(posts), total

    @staticmethod
    async def get_user_posts(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        keyword: str | None = None,
    ) -> tuple[list[Post], int]:
        """获取用户发布的帖子列表"""
        query = (
            select(Post)
            .options(selectinload(Post.author))
            .where(and_(Post.user_id == user_id, Post.is_deleted == False))
        )
        count_query = select(
            func.count(
                Post.id)).where(
            and_(
                Post.user_id == user_id,
                Post.is_deleted == False))

        if category:
            query = query.where(Post.category == category)
            count_query = count_query.where(Post.category == category)

        if keyword:
            search_filter = Post.title.contains(
                keyword) | Post.content.contains(keyword)
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        query = query.order_by(desc(Post.is_pinned), desc(Post.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        posts = result.scalars().all()

        count_result = await db.execute(count_query)
        total = int(count_result.scalar() or 0)

        return list(posts), total

    @staticmethod
    async def update_post(db: AsyncSession, post: Post,
                          post_data: PostUpdate) -> Post:
        """更新帖子"""
        update_data: dict[str, object] = post_data.model_dump(
            exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(post, field, value)

        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    @staticmethod
    async def delete_post(db: AsyncSession, post: Post) -> None:
        """删除帖子（软删除）"""
        post.is_deleted = True
        db.add(post)
        await db.commit()

    @staticmethod
    async def restore_post(db: AsyncSession, post: Post) -> Post:
        """恢复帖子"""
        post.is_deleted = False
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    @staticmethod
    async def purge_post(db: AsyncSession, post: Post) -> None:
        """彻底删除帖子"""
        await db.delete(post)
        await db.commit()

    @staticmethod
    async def increment_view(db: AsyncSession, post: Post) -> None:
        """增加浏览量"""
        post.view_count = (post.view_count or 0) + 1
        db.add(post)
        await db.commit()

    # === 帖子互动 ===

    @staticmethod
    async def toggle_post_like(
            db: AsyncSession, post_id: int, user_id: int) -> tuple[bool, int]:
        """切换帖子点赞状态"""
        result = await db.execute(
            select(PostLike).where(
                PostLike.post_id == post_id,
                PostLike.user_id == user_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            await db.delete(existing)
            await db.commit()
            return False, 0

        post_like = PostLike(post_id=post_id, user_id=user_id)
        db.add(post_like)
        await db.commit()

        count_result = await db.execute(
            select(func.count(PostLike.id)).where(PostLike.post_id == post_id)
        )
        count = count_result.scalar() or 0

        return True, count

    @staticmethod
    async def is_post_liked(
            db: AsyncSession, post_id: int, user_id: int) -> bool:
        """检查用户是否已点赞帖子"""
        result = await db.execute(
            select(PostLike).where(
                PostLike.post_id == post_id,
                PostLike.user_id == user_id)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def toggle_post_favorite(
            db: AsyncSession, post_id: int, user_id: int) -> tuple[bool, int]:
        """切换帖子收藏状态"""
        result = await db.execute(
            select(PostFavorite).where(
                PostFavorite.post_id == post_id,
                PostFavorite.user_id == user_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            await db.delete(existing)
            await db.commit()
            return False, 0

        favorite = PostFavorite(post_id=post_id, user_id=user_id)
        db.add(favorite)
        await db.commit()

        count_result = await db.execute(
            select(
                func.count(
                    PostFavorite.id)).where(
                PostFavorite.post_id == post_id)
        )
        count = count_result.scalar() or 0

        return True, count

    @staticmethod
    async def is_post_favorited(
            db: AsyncSession, post_id: int, user_id: int) -> bool:
        """检查用户是否已收藏帖子"""
        result = await db.execute(
            select(PostFavorite).where(
                PostFavorite.post_id == post_id,
                PostFavorite.user_id == user_id)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_posts_liked_status(
            db: AsyncSession, post_ids: Sequence[int], user_id: int) -> dict[int, bool]:
        """批量获取用户点赞状态"""
        if not post_ids or not user_id:
            return {}
        result = await db.execute(
            select(PostLike.post_id).where(
                PostLike.post_id.in_(post_ids),
                PostLike.user_id == user_id
            )
        )
        liked_post_ids = {row[0] for row in result.all()}
        return {post_id: post_id in liked_post_ids for post_id in post_ids}

    @staticmethod
    async def get_posts_favorited_status(
            db: AsyncSession, post_ids: Sequence[int], user_id: int) -> dict[int, bool]:
        """批量获取用户收藏状态"""
        if not post_ids or not user_id:
            return {}
        result = await db.execute(
            select(PostFavorite.post_id).where(
                PostFavorite.post_id.in_(post_ids),
                PostFavorite.user_id == user_id
            )
        )
        favorited_post_ids = {row[0] for row in result.all()}
        return {post_id: post_id in favorited_post_ids for post_id in post_ids}

    @staticmethod
    async def get_post_favorite_count(db: AsyncSession, post_id: int) -> int:
        """获取帖子收藏数量"""
        result = await db.execute(
            select(
                func.count(
                    PostFavorite.id)).where(
                PostFavorite.post_id == post_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def get_posts_favorite_counts(
            db: AsyncSession, post_ids: Sequence[int]) -> dict[int, int]:
        """批量获取帖子收藏数量"""
        if not post_ids:
            return {}

        result = await db.execute(
            select(PostFavorite.post_id, func.count(PostFavorite.id))
            .where(PostFavorite.post_id.in_(post_ids))
            .group_by(PostFavorite.post_id)
        )
        return {row[0]: int(row[1]) for row in result.all()}

    @staticmethod
    async def get_user_favorites(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        keyword: str | None = None,
    ) -> tuple[list[Post], int]:
        """获取用户收藏的帖子"""
        query = (
            select(Post)
            .join(PostFavorite, Post.id == PostFavorite.post_id)
            .where(PostFavorite.user_id == user_id, Post.is_deleted == False)
            .order_by(PostFavorite.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(query)
        posts = list(result.scalars().all())

        count_result = await db.execute(
            select(
                func.count(
                    PostFavorite.id)).where(
                PostFavorite.user_id == user_id)
        )
        total = count_result.scalar() or 0

        return posts, total

    @staticmethod
    async def get_user_stats(db: AsyncSession, user_id: int) -> dict[str, int]:
        """获取用户论坛统计数据"""
        posts_result = await db.execute(
            select(
                func.count(
                    Post.id)).where(
                and_(
                    Post.user_id == user_id,
                    Post.is_deleted == False))
        )
        posts_count = posts_result.scalar() or 0

        comments_result = await db.execute(
            select(
                func.count(
                    Comment.id)).where(
                and_(
                    Comment.user_id == user_id,
                    Comment.is_deleted == False))
        )
        comments_count = comments_result.scalar() or 0

        likes_result = await db.execute(
            select(func.count(PostLike.id)).where(PostLike.user_id == user_id)
        )
        likes_count = likes_result.scalar() or 0

        favorites_result = await db.execute(
            select(
                func.count(
                    PostFavorite.id)).where(
                PostFavorite.user_id == user_id)
        )
        favorites_count = favorites_result.scalar() or 0

        return {
            "posts": posts_count,
            "comments": comments_count,
            "likes": likes_count,
            "favorites": favorites_count,
        }

    # === 热门与推荐 ===

    @staticmethod
    async def update_heat_scores(db: AsyncSession) -> int:
        """更新帖子热度分数
        
        性能优化：使用单个UPDATE语句批量更新，避免N+1查询问题
        """
        from sqlalchemy import update, case

        # 使用CASE语句批量计算和更新热度分数
        # 公式：热度 = 浏览量 + 点赞数*3 + 评论数*5
        await db.execute(
            update(Post).values(
                heat_score=(
                    func.coalesce(Post.view_count, 0) +
                    func.coalesce(Post.like_count, 0) * 3 +
                    func.coalesce(Post.comment_count, 0) * 5
                )
            ).where(
                Post.is_deleted == False
            )
        )

        await db.commit()
        
        # 返回更新的记录数
        result = await db.execute(
            select(func.count()).select_from(Post).where(Post.is_deleted == False)
        )
        return result.scalar() or 0

    @staticmethod
    async def get_hot_posts(
            db: AsyncSession,
            days: int = 7,
            limit: int = 10,
            category: str | None = None) -> list[Post]:
        """获取热门帖子"""
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=days)

        query = (
            select(Post)
            .options(selectinload(Post.author))
            .where(
                and_(
                    Post.is_deleted == False,
                    Post.created_at >= start_date,
                    or_(Post.review_status == "approved",
                        Post.review_status is None),
                )
            )
            .order_by(desc(Post.heat_score), desc(Post.like_count), desc(Post.comment_count))
            .limit(limit)
        )

        if category:
            query = query.where(Post.category == category)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def set_post_hot(db: AsyncSession, post_id: int,
                           is_hot: bool) -> bool:
        """设置帖子为热门"""
        post = await ForumPostService.get_post_any(db, post_id)
        if not post:
            return False

        post.is_hot = is_hot
        db.add(post)
        await db.commit()
        return True

    @staticmethod
    async def set_post_essence(
            db: AsyncSession, post_id: int, is_essence: bool) -> bool:
        """设置帖子为精华"""
        post = await ForumPostService.get_post_any(db, post_id)
        if not post:
            return False

        post.is_essence = is_essence
        db.add(post)
        await db.commit()
        return True

    @staticmethod
    async def set_post_pinned(
            db: AsyncSession, post_id: int, is_pinned: bool) -> bool:
        """设置帖子为置顶"""
        post = await ForumPostService.get_post_any(db, post_id)
        if not post:
            return False

        post.is_pinned = is_pinned
        db.add(post)
        await db.commit()
        return True

    # === 反应（Reaction） ===

    @staticmethod
    async def toggle_reaction(
        db: AsyncSession, post_id: int, user_id: int, emoji: str
    ) -> tuple[bool, int]:
        """切换帖子反应状态"""
        result = await db.execute(
            select(PostReaction).where(
                PostReaction.post_id == post_id,
                PostReaction.user_id == user_id,
                PostReaction.emoji == emoji,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            await db.delete(existing)
            await db.commit()
            return False, 0

        reaction = PostReaction(post_id=post_id, user_id=user_id, emoji=emoji)
        db.add(reaction)
        await db.commit()

        count_result = await db.execute(
            select(func.count(PostReaction.id)).where(
                PostReaction.post_id == post_id, PostReaction.emoji == emoji
            )
        )
        count = count_result.scalar() or 0

        return True, count

    @staticmethod
    async def get_post_reactions(
            db: AsyncSession, post_id: int) -> list[dict[str, int | str]]:
        """获取帖子反应统计"""
        result = await db.execute(
            select(PostReaction.emoji, func.count(PostReaction.id))
            .where(PostReaction.post_id == post_id)
            .group_by(PostReaction.emoji)
        )
        return [{"type": row[0], "count": int(row[1])} for row in result.all()]

    @staticmethod
    async def get_posts_reactions(
        db: AsyncSession, post_ids: Sequence[int]
    ) -> dict[int, list[dict[str, int | str]]]:
        """批量获取帖子反应统计"""
        if not post_ids:
            return {}

        result = await db.execute(
            select(
                PostReaction.post_id,
                PostReaction.emoji,
                func.count(
                    PostReaction.id))
            .where(PostReaction.post_id.in_(post_ids))
            .group_by(PostReaction.post_id, PostReaction.emoji)
        )

        reactions_by_post: dict[int, list[dict[str, int | str]]] = {
            pid: [] for pid in post_ids}
        for row in result.all():
            post_id = row[0]
            emoji = row[1]
            count = int(row[2])
            reactions_by_post[post_id].append({"type": emoji, "count": count})

        return reactions_by_post


# 单例
forum_post_service = ForumPostService()
