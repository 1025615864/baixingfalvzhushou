"""论坛服务核心

提供论坛配置、缓存、统计等核心功能
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.forum import Post, Comment, PostLike, PostFavorite, PostReaction, CommentLike
from ...models.system import SystemConfig
from ...schemas.forum import PostCreate, PostUpdate, CommentCreate
from ...services.cache_service import cache_service


logger = logging.getLogger(__name__)


class ForumService:
    """论坛服务核心"""

    _CONTENT_FILTER_SENSITIVE_KEY = "forum.content_filter.sensitive_words"
    _CONTENT_FILTER_AD_KEY = "forum.content_filter.ad_words"
    _CONTENT_FILTER_AD_THRESHOLD_KEY = "forum.content_filter.ad_words_threshold"
    _CONTENT_FILTER_CHECK_URL_KEY = "forum.content_filter.check_url"
    _CONTENT_FILTER_CHECK_PHONE_KEY = "forum.content_filter.check_phone"

    _CONTENT_FILTER_CACHE_KEY = "forum:content_filter_config:v1"
    _CONTENT_FILTER_CACHE_EXPIRE_SECONDS = 60

    @staticmethod
    def _parse_bool_value(value: str | None, default: bool = True) -> bool:
        if value is None:
            return default
        v = value.strip().lower()
        if v in ("1", "true", "yes", "y", "on"):
            return True
        if v in ("0", "false", "no", "n", "off"):
            return False
        return default

    @staticmethod
    def _parse_int_value(value: str | None, default: int) -> int:
        if value is None:
            return int(default)
        try:
            v = int(str(value).strip())
        except (TypeError, ValueError):
            return int(default)
        return v if v > 0 else int(default)

    @staticmethod
    def _parse_json_list(value: str | None) -> list[str] | None:
        if not value:
            return None
        try:
            loaded = json.loads(value)
        except Exception:
            return None
        if not isinstance(loaded, list):
            return None
        result: list[str] = []
        seen: set[str] = set()
        for item in loaded:
            s = str(item).strip()
            if not s:
                continue
            if s in seen:
                continue
            seen.add(s)
            result.append(s)
        return result

    # === 配置管理 ===

    @staticmethod
    async def is_comment_review_enabled(db: AsyncSession) -> bool:
        result = await db.execute(
            select(
                SystemConfig.value).where(
                SystemConfig.key == "forum.review.enabled")
        )
        value: str | None = result.scalar_one_or_none()
        return ForumService._parse_bool_value(value, default=True)

    @staticmethod
    async def is_post_review_enabled(db: AsyncSession) -> bool:
        result = await db.execute(
            select(
                SystemConfig.value).where(
                SystemConfig.key == "forum.post_review.enabled")
        )
        value: str | None = result.scalar_one_or_none()
        return ForumService._parse_bool_value(value, default=False)

    @staticmethod
    async def get_post_review_mode(db: AsyncSession) -> str:
        result = await db.execute(
            select(
                SystemConfig.value).where(
                SystemConfig.key == "forum.post_review.mode")
        )
        value: str | None = result.scalar_one_or_none()
        if not value:
            return "rule"
        mode = value.strip().lower()
        if mode in ("all", "rule"):
            return mode
        return "rule"

    @staticmethod
    async def _upsert_system_config(
        db: AsyncSession,
        *,
        key: str,
        value: str,
        description: str,
        updated_by: int | None,
        category: str = "forum",
    ) -> None:
        result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
        config = result.scalar_one_or_none()
        if config:
            config.value = value
            config.updated_by = updated_by
            if not config.description:
                config.description = description
            if not config.category:
                config.category = category
        else:
            db.add(
                SystemConfig(
                    key=key,
                    value=value,
                    description=description,
                    category=category,
                    updated_by=updated_by,
                )
            )

    @staticmethod
    async def get_content_filter_config(db: AsyncSession) -> dict[str, Any]:
        try:
            cached = await cache_service.get(ForumService._CONTENT_FILTER_CACHE_KEY)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

        sensitive_words_result = await db.execute(
            select(SystemConfig.value).where(
                SystemConfig.key == ForumService._CONTENT_FILTER_SENSITIVE_KEY
            )
        )
        sensitive_words_str = sensitive_words_result.scalar_one_or_none()
        sensitive_words = ForumService._parse_json_list(sensitive_words_str)

        ad_words_result = await db.execute(
            select(
                SystemConfig.value).where(
                SystemConfig.key == ForumService._CONTENT_FILTER_AD_KEY)
        )
        ad_words_str = ad_words_result.scalar_one_or_none()
        ad_words = ForumService._parse_json_list(ad_words_str)

        ad_threshold_result = await db.execute(
            select(SystemConfig.value).where(
                SystemConfig.key == ForumService._CONTENT_FILTER_AD_THRESHOLD_KEY
            )
        )
        ad_threshold_str = ad_threshold_result.scalar_one_or_none()
        ad_threshold = ForumService._parse_int_value(ad_threshold_str, 3)

        check_url_result = await db.execute(
            select(SystemConfig.value).where(SystemConfig.key ==
                                             ForumService._CONTENT_FILTER_CHECK_URL_KEY)
        )
        check_url_str = check_url_result.scalar_one_or_none()
        check_url = ForumService._parse_bool_value(check_url_str, True)

        check_phone_result = await db.execute(
            select(SystemConfig.value).where(SystemConfig.key ==
                                             ForumService._CONTENT_FILTER_CHECK_PHONE_KEY)
        )
        check_phone_str = check_phone_result.scalar_one_or_none()
        check_phone = ForumService._parse_bool_value(check_phone_str, True)

        config = {
            "sensitive_words": sensitive_words or [],
            "ad_words": ad_words or [],
            "ad_threshold": ad_threshold,
            "check_url": check_url,
            "check_phone": check_phone,
        }

        try:
            await cache_service.set(
                ForumService._CONTENT_FILTER_CACHE_KEY,
                json.dumps(config, ensure_ascii=False),
                ForumService._CONTENT_FILTER_CACHE_EXPIRE_SECONDS,
            )
        except Exception:
            pass

        return config

    @staticmethod
    async def invalidate_content_filter_config_cache() -> None:
        try:
            await cache_service.delete(ForumService._CONTENT_FILTER_CACHE_KEY)
        except Exception:
            pass

    @staticmethod
    async def apply_content_filter_config_from_db(
            db: AsyncSession) -> dict[str, Any]:
        await ForumService.invalidate_content_filter_config_cache()
        return await ForumService.get_content_filter_config(db)

    @staticmethod
    async def update_content_filter_rules(
        db: AsyncSession,
        *,
        sensitive_words: list[str] | None = None,
        ad_words: list[str] | None = None,
        ad_threshold: int | None = None,
        check_url: bool | None = None,
        check_phone: bool | None = None,
        updated_by: int | None = None,
    ) -> dict[str, Any]:
        if sensitive_words is not None:
            await ForumService._upsert_system_config(
                db,
                key=ForumService._CONTENT_FILTER_SENSITIVE_KEY,
                value=json.dumps(sensitive_words, ensure_ascii=False),
                description="论坛内容过滤敏感词",
                updated_by=updated_by,
            )

        if ad_words is not None:
            await ForumService._upsert_system_config(
                db,
                key=ForumService._CONTENT_FILTER_AD_KEY,
                value=json.dumps(ad_words, ensure_ascii=False),
                description="论坛内容过滤广告词",
                updated_by=updated_by,
            )

        if ad_threshold is not None:
            await ForumService._upsert_system_config(
                db,
                key=ForumService._CONTENT_FILTER_AD_THRESHOLD_KEY,
                value=str(ad_threshold),
                description="论坛内容过滤广告词阈值",
                updated_by=updated_by,
            )

        if check_url is not None:
            await ForumService._upsert_system_config(
                db,
                key=ForumService._CONTENT_FILTER_CHECK_URL_KEY,
                value=str(int(check_url)),
                description="论坛内容过滤是否检查URL",
                updated_by=updated_by,
            )

        if check_phone is not None:
            await ForumService._upsert_system_config(
                db,
                key=ForumService._CONTENT_FILTER_CHECK_PHONE_KEY,
                value=str(int(check_phone)),
                description="论坛内容过滤是否检查手机号",
                updated_by=updated_by,
            )

        await db.commit()
        return await ForumService.apply_content_filter_config_from_db(db)

    @staticmethod
    async def add_sensitive_word(
            db: AsyncSession, *, word: str, updated_by: int | None) -> dict[str, Any]:
        config = await ForumService.get_content_filter_config(db)
        sensitive_words = config.get("sensitive_words", [])
        if word not in sensitive_words:
            sensitive_words.append(word)
        return await ForumService.update_content_filter_rules(
            db, sensitive_words=sensitive_words, updated_by=updated_by
        )

    @staticmethod
    async def remove_sensitive_word(
            db: AsyncSession, *, word: str, updated_by: int | None) -> dict[str, Any]:
        config = await ForumService.get_content_filter_config(db)
        sensitive_words = config.get("sensitive_words", [])
        if word in sensitive_words:
            sensitive_words.remove(word)
        return await ForumService.update_content_filter_rules(
            db, sensitive_words=sensitive_words, updated_by=updated_by
        )

    @staticmethod
    async def add_ad_word(db: AsyncSession, *, word: str,
                          updated_by: int | None) -> dict[str, Any]:
        config = await ForumService.get_content_filter_config(db)
        ad_words = config.get("ad_words", [])
        if word not in ad_words:
            ad_words.append(word)
        return await ForumService.update_content_filter_rules(db, ad_words=ad_words, updated_by=updated_by)

    @staticmethod
    async def remove_ad_word(db: AsyncSession, *, word: str, updated_by: int | None) -> dict[str, Any]:
        config = await ForumService.get_content_filter_config(db)
        ad_words = config.get("ad_words", [])
        if word in ad_words:
            ad_words.remove(word)
        return await ForumService.update_content_filter_rules(db, ad_words=ad_words, updated_by=updated_by)

    # === 帖子方法（代理到 ForumPostService）===

    @staticmethod
    async def create_post(db: AsyncSession, user_id: int,
                          post_data: Any) -> Any:
        """创建帖子（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.create_post(db, user_id, post_data)

    @staticmethod
    async def get_post(db: AsyncSession, post_id: int) -> Any:
        """获取帖子详情（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.get_post(db, post_id)

    @staticmethod
    async def get_post_any(db: AsyncSession, post_id: int) -> Any:
        """获取帖子详情（包含已删除）（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.get_post_any(db, post_id)

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
    ) -> tuple[list, int]:
        """获取帖子列表（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.get_posts(
            db, page, page_size, category, keyword, is_essence, include_deleted, deleted, approved_only
        )

    @staticmethod
    async def get_user_deleted_posts(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        keyword: str | None = None,
    ) -> tuple[list, int]:
        """获取用户删除的帖子列表（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.get_user_deleted_posts(db, user_id, page, page_size, category, keyword)

    @staticmethod
    async def get_user_posts(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        keyword: str | None = None,
    ) -> tuple[list, int]:
        """获取用户发布的帖子列表（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.get_user_posts(db, user_id, page, page_size, category, keyword)

    @staticmethod
    async def update_post(db: AsyncSession, post: Any, post_data: Any) -> Any:
        """更新帖子（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.update_post(db, post, post_data)

    @staticmethod
    async def delete_post(db: AsyncSession, post: Any) -> None:
        """删除帖子（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.delete_post(db, post)

    @staticmethod
    async def restore_post(db: AsyncSession, post: Any) -> Any:
        """恢复帖子（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.restore_post(db, post)

    @staticmethod
    async def purge_post(db: AsyncSession, post: Any) -> None:
        """彻底删除帖子（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.purge_post(db, post)

    @staticmethod
    async def increment_view(db: AsyncSession, post: Any) -> None:
        """增加浏览量（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.increment_view(db, post)

    @staticmethod
    async def toggle_post_like(
            db: AsyncSession, post_id: int, user_id: int) -> tuple[bool, int]:
        """切换帖子点赞状态（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.toggle_post_like(db, post_id, user_id)

    @staticmethod
    async def is_post_liked(
            db: AsyncSession, post_id: int, user_id: int) -> bool:
        """检查用户是否已点赞帖子（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.is_post_liked(db, post_id, user_id)

    @staticmethod
    async def toggle_post_favorite(
            db: AsyncSession, post_id: int, user_id: int) -> tuple[bool, int]:
        """切换帖子收藏状态（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.toggle_post_favorite(db, post_id, user_id)

    @staticmethod
    async def is_post_favorited(
            db: AsyncSession, post_id: int, user_id: int) -> bool:
        """检查用户是否已收藏帖子（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.is_post_favorited(db, post_id, user_id)

    @staticmethod
    async def get_post_favorite_count(db: AsyncSession, post_id: int) -> int:
        """获取帖子收藏数量（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.get_post_favorite_count(db, post_id)

    @staticmethod
    async def get_posts_favorite_counts(
            db: AsyncSession, post_ids: Any) -> dict[int, int]:
        """批量获取帖子收藏数量（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.get_posts_favorite_counts(db, post_ids)

    @staticmethod
    async def get_user_favorites(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        keyword: str | None = None,
    ) -> tuple[list, int]:
        """获取用户收藏的帖子（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.get_user_favorites(db, user_id, page, page_size, category, keyword)

    @staticmethod
    async def get_user_stats(db: AsyncSession, user_id: int) -> dict[str, int]:
        """获取用户论坛统计数据（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.get_user_stats(db, user_id)

    @staticmethod
    async def update_heat_scores(db: AsyncSession) -> int:
        """更新帖子热度分数（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.update_heat_scores(db)

    @staticmethod
    async def get_hot_posts(
            db: AsyncSession,
            days: int = 7,
            limit: int = 10,
            category: str | None = None) -> list:
        """获取热门帖子（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.get_hot_posts(db, days, limit, category)

    @staticmethod
    async def set_post_hot(db: AsyncSession, post_id: int,
                           is_hot: bool) -> bool:
        """设置帖子为热门（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.set_post_hot(db, post_id, is_hot)

    @staticmethod
    async def set_post_essence(
            db: AsyncSession, post_id: int, is_essence: bool) -> bool:
        """设置帖子为精华（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.set_post_essence(db, post_id, is_essence)

    @staticmethod
    async def set_post_pinned(
            db: AsyncSession, post_id: int, is_pinned: bool) -> bool:
        """设置帖子为置顶（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.set_post_pinned(db, post_id, is_pinned)

    @staticmethod
    async def toggle_reaction(
        db: AsyncSession, post_id: int, user_id: int, emoji: str
    ) -> tuple[bool, int]:
        """切换帖子反应状态（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.toggle_reaction(db, post_id, user_id, emoji)

    @staticmethod
    async def get_post_reactions(
            db: AsyncSession, post_id: int) -> list[dict[str, int | str]]:
        """获取帖子反应统计（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.get_post_reactions(db, post_id)

    @staticmethod
    async def get_posts_reactions(
            db: AsyncSession, post_ids: Any) -> dict[int, list[dict[str, int | str]]]:
        """批量获取帖子反应统计（代理）"""
        from .posts import forum_post_service
        return await forum_post_service.get_posts_reactions(db, post_ids)

    # === 评论方法（代理到 ForumCommentService）===

    @staticmethod
    async def create_comment(
        db: AsyncSession,
        post_id: int,
        user_id: int,
        comment_data: Any,
    ) -> Any:
        """创建评论（代理）"""
        from .comments import forum_comment_service
        return await forum_comment_service.create_comment(db, post_id, user_id, comment_data)

    @staticmethod
    async def get_comments(
        db: AsyncSession,
        post_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list, int]:
        """获取帖子评论列表（代理）"""
        from .comments import forum_comment_service
        return await forum_comment_service.get_comments(db, post_id, page, page_size)

    @staticmethod
    async def get_comments_visible(
        db: AsyncSession,
        post_id: int,
        page: int = 1,
        page_size: int = 50,
        viewer_user_id: int | None = None,
        viewer_role: str | None = None,
        include_unapproved: bool = False,
    ) -> tuple[list, int]:
        """获取帖子可见评论列表（代理）"""
        from .comments import forum_comment_service
        return await forum_comment_service.get_comments_visible(
            db, post_id, page, page_size, viewer_user_id, viewer_role, include_unapproved
        )

    @staticmethod
    async def delete_comment(db: AsyncSession, comment: Any) -> None:
        """删除评论（代理）"""
        from .comments import forum_comment_service
        return await forum_comment_service.delete_comment(db, comment)

    @staticmethod
    async def restore_comment(db: AsyncSession, comment: Any) -> Any:
        """恢复评论（代理）"""
        from .comments import forum_comment_service
        return await forum_comment_service.restore_comment(db, comment)

    @staticmethod
    async def get_comment(db: AsyncSession, comment_id: int) -> Any:
        """获取评论详情（代理）"""
        from .comments import forum_comment_service
        return await forum_comment_service.get_comment(db, comment_id)

    @staticmethod
    async def get_comment_any(db: AsyncSession, comment_id: int) -> Any:
        """获取评论详情（包含已删除）（代理）"""
        from .comments import forum_comment_service
        return await forum_comment_service.get_comment_any(db, comment_id)

    @staticmethod
    async def is_comment_liked(
            db: AsyncSession, comment_id: int, user_id: int) -> bool:
        """检查用户是否已点赞评论（代理）"""
        from .comments import forum_comment_service
        return await forum_comment_service.is_comment_liked(db, comment_id, user_id)

    @staticmethod
    async def toggle_comment_like(
            db: AsyncSession, comment_id: int, user_id: int) -> tuple[bool, int]:
        """切换评论点赞状态（代理）"""
        from .comments import forum_comment_service
        return await forum_comment_service.toggle_comment_like(db, comment_id, user_id)
        """获取论坛统计信息"""
        total_posts_result = await db.execute(select(func.count(Post.id)))
        total_posts = total_posts_result.scalar() or 0

        total_comments_result = await db.execute(select(func.count(Comment.id)))
        total_comments = total_comments_result.scalar() or 0

        active_posts_result = await db.execute(
            select(func.count(Post.id)).where(Post.is_deleted == False)
        )
        active_posts = active_posts_result.scalar() or 0

        posts_today_result = await db.execute(
            select(func.count(Post.id)).where(
                and_(
                    Post.created_at >= datetime.now().replace(
                        hour=0, minute=0, second=0, microsecond=0),
                    Post.is_deleted == False,
                )
            )
        )
        posts_today = posts_today_result.scalar() or 0

        comments_today_result = await db.execute(
            select(func.count(Comment.id)).where(
                Comment.created_at >= datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0)
            )
        )
        comments_today = comments_today_result.scalar() or 0

        users_count_result = await db.execute(
            select(func.count(Post.user_id.distinct()))
        )
        users_count = users_result.scalar() or 0

        return {
            "total_posts": posts_count,
            "posts_today": posts_today,
            "total_comments": comments_count,
            "comments_today": comments_today,
            "active_users_today": users_count,
        }

    @staticmethod
    async def get_forum_stats(db: AsyncSession) -> dict[str, int]:
        """获取论坛统计数据"""
        from datetime import datetime, timedelta
        from sqlalchemy import and_

        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        posts_result = await db.execute(
            select(func.count(Post.id)).where(Post.is_deleted == False)
        )
        posts_count = posts_result.scalar() or 0

        posts_today_result = await db.execute(
            select(
                func.count(
                    Post.id)).where(
                and_(
                    Post.is_deleted == False,
                    Post.created_at >= today))
        )
        posts_today = posts_today_result.scalar() or 0

        comments_result = await db.execute(
            select(func.count(Comment.id)).where(Comment.is_deleted == False)
        )
        comments_count = comments_result.scalar() or 0

        comments_today_result = await db.execute(
            select(
                func.count(
                    Comment.id)).where(
                and_(
                    Comment.is_deleted == False,
                    Comment.created_at >= today))
        )
        comments_today = comments_today_result.scalar() or 0

        users_result = await db.execute(
            select(func.count(func.distinct(Post.user_id))).where(
                and_(Post.is_deleted == False, Post.created_at >= today))
        )
        users_count = users_result.scalar() or 0

        return {
            "total_posts": posts_count,
            "posts_today": posts_today,
            "total_comments": comments_count,
            "comments_today": comments_today,
            "active_users_today": users_count,
        }


# 单例
_forum_service: ForumService | None = None


def get_forum_service() -> ForumService:
    """获取论坛服务实例"""
    global _forum_service
    if _forum_service is None:
        _forum_service = ForumService()
    return _forum_service


forum_service = get_forum_service()
