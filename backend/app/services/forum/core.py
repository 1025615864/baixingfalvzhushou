from __future__ import annotations

import json
import time
from typing import Optional

from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.forum import Post, Comment, CommentLike
from app.models.system import SystemConfig
from app.services.cache_service import cache_service


class ForumService:
    def __init__(self):
        self._posts: dict[int, dict] = {}
        self._next_post_id = 1

    @staticmethod
    def _parse_bool_value(value, default=True) -> bool:
        if value is None or value == "":
            return default
        if isinstance(value, bool):
            return value
        v = str(value).strip().lower()
        if v in ("true", "1", "yes", "on"):
            return True
        if v in ("false", "0", "no", "off"):
            return False
        return default

    @staticmethod
    def _parse_int_value(value, default=0) -> int:
        if value is None or value == "":
            return default
        try:
            result = int(str(value).strip())
            return result if result > 0 else default
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _parse_json_list(value) -> Optional[list[str]]:
        if value is None or value == "":
            return None
        if isinstance(value, list):
            return value
        try:
            parsed = json.loads(value)
            if not isinstance(parsed, list):
                return None
            result = list(dict.fromkeys(item.strip() for item in parsed if item and item.strip()))
            return result if result else None
        except (json.JSONDecodeError, TypeError):
            return None

    @staticmethod
    async def is_comment_review_enabled(db: AsyncSession) -> bool:
        stmt = select(SystemConfig.value).where(SystemConfig.key == "forum_comment_review_enabled")
        result = await db.execute(stmt)
        val = result.scalar_one_or_none()
        return ForumService._parse_bool_value(val, default=True)

    @staticmethod
    async def is_post_review_enabled(db: AsyncSession) -> bool:
        stmt = select(SystemConfig.value).where(SystemConfig.key == "forum_post_review_enabled")
        result = await db.execute(stmt)
        val = result.scalar_one_or_none()
        return ForumService._parse_bool_value(val, default=False)

    @staticmethod
    async def get_post_review_mode(db: AsyncSession) -> str:
        stmt = select(SystemConfig.value).where(SystemConfig.key == "forum_post_review_mode")
        result = await db.execute(stmt)
        val = result.scalar_one_or_none()
        if val in ("rule", "all"):
            return val
        return "rule"

    @staticmethod
    async def get_content_filter_config(db: AsyncSession) -> dict:
        cached = await cache_service.get("forum:content_filter_config:v1")
        if cached is not None:
            try:
                return json.loads(cached)
            except (json.JSONDecodeError, TypeError):
                pass

        queries = [
            ("forum_sensitive_words", "sensitive_words"),
            ("forum_ad_words", "ad_words"),
            ("forum_ad_threshold", "ad_threshold"),
            ("forum_check_url", "check_url"),
            ("forum_check_phone", "check_phone"),
        ]
        values = {}
        for key, _ in queries:
            stmt = select(SystemConfig.value).where(SystemConfig.key == key)
            result = await db.execute(stmt)
            values[key] = result.scalar_one_or_none()

        config = {
            "sensitive_words": ForumService._parse_json_list(values.get("forum_sensitive_words")) or [],
            "ad_words": ForumService._parse_json_list(values.get("forum_ad_words")) or [],
            "ad_threshold": ForumService._parse_int_value(values.get("forum_ad_threshold"), default=3),
            "check_url": ForumService._parse_bool_value(values.get("forum_check_url"), default=True),
            "check_phone": ForumService._parse_bool_value(values.get("forum_check_phone"), default=True),
        }

        await cache_service.set("forum:content_filter_config:v1", json.dumps(config, ensure_ascii=False), 300)
        return config

    @staticmethod
    async def _upsert_system_config(db: AsyncSession, key: str, value: str, updated_by: int = None) -> None:
        stmt = select(SystemConfig).where(SystemConfig.key == key)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        if config:
            config.value = value
        else:
            config = SystemConfig(key=key, value=value)
            db.add(config)

    @staticmethod
    async def update_content_filter_rules(
        db: AsyncSession,
        sensitive_words: list[str] = None,
        ad_words: list[str] = None,
        ad_threshold: int = None,
        check_url: bool = None,
        check_phone: bool = None,
        updated_by: int = None,
    ) -> dict:
        if sensitive_words is not None:
            await ForumService._upsert_system_config(db, "forum_sensitive_words", json.dumps(sensitive_words, ensure_ascii=False), updated_by)
        if ad_words is not None:
            await ForumService._upsert_system_config(db, "forum_ad_words", json.dumps(ad_words, ensure_ascii=False), updated_by)
        if ad_threshold is not None:
            await ForumService._upsert_system_config(db, "forum_ad_threshold", str(ad_threshold), updated_by)
        if check_url is not None:
            await ForumService._upsert_system_config(db, "forum_check_url", str(check_url).lower(), updated_by)
        if check_phone is not None:
            await ForumService._upsert_system_config(db, "forum_check_phone", str(check_phone).lower(), updated_by)
        await db.commit()
        return await ForumService.apply_content_filter_config_from_db(db)

    @staticmethod
    async def add_sensitive_word(db: AsyncSession, word: str, updated_by: int = None) -> dict:
        config = await ForumService.get_content_filter_config(db)
        words = config.get("sensitive_words", [])
        if word not in words:
            words.append(word)
        config["sensitive_words"] = words
        return await ForumService.update_content_filter_rules(db, sensitive_words=words, ad_words=config.get("ad_words"), ad_threshold=config.get("ad_threshold"), check_url=config.get("check_url"), check_phone=config.get("check_phone"), updated_by=updated_by)

    @staticmethod
    async def remove_sensitive_word(db: AsyncSession, word: str, updated_by: int = None) -> dict:
        config = await ForumService.get_content_filter_config(db)
        words = [w for w in config.get("sensitive_words", []) if w != word]
        return await ForumService.update_content_filter_rules(db, sensitive_words=words, ad_words=config.get("ad_words"), ad_threshold=config.get("ad_threshold"), check_url=config.get("check_url"), check_phone=config.get("check_phone"), updated_by=updated_by)

    @staticmethod
    async def add_ad_word(db: AsyncSession, word: str, updated_by: int = None) -> dict:
        config = await ForumService.get_content_filter_config(db)
        words = config.get("ad_words", [])
        if word not in words:
            words.append(word)
        config["ad_words"] = words
        return await ForumService.update_content_filter_rules(db, sensitive_words=config.get("sensitive_words"), ad_words=words, ad_threshold=config.get("ad_threshold"), check_url=config.get("check_url"), check_phone=config.get("check_phone"), updated_by=updated_by)

    @staticmethod
    async def remove_ad_word(db: AsyncSession, word: str, updated_by: int = None) -> dict:
        config = await ForumService.get_content_filter_config(db)
        words = [w for w in config.get("ad_words", []) if w != word]
        return await ForumService.update_content_filter_rules(db, sensitive_words=config.get("sensitive_words"), ad_words=words, ad_threshold=config.get("ad_threshold"), check_url=config.get("check_url"), check_phone=config.get("check_phone"), updated_by=updated_by)

    @staticmethod
    async def invalidate_content_filter_config_cache() -> None:
        await cache_service.delete("forum:content_filter_config:v1")

    @staticmethod
    async def apply_content_filter_config_from_db(db: AsyncSession) -> dict:
        await ForumService.invalidate_content_filter_config_cache()
        return await ForumService.get_content_filter_config(db)

    async def create_post(self, db: AsyncSession = None, user_id: int = None, post_data=None, title: str = None, content: str = None, category: str = "general", tags: Optional[list[str]] = None) -> object:
        from app.models.forum import Post as PostModel
        _title = title
        _content = content
        _category = category
        _cover_image = None
        if post_data is not None:
            _title = getattr(post_data, "title", title)
            _content = getattr(post_data, "content", content)
            _category = getattr(post_data, "category", category)
            _cover_image = getattr(post_data, "cover_image", None)

        if db is not None:
            post = PostModel(
                title=_title,
                content=_content,
                category=_category,
                cover_image=_cover_image,
                user_id=user_id,
                review_status="approved",
                is_deleted=False,
            )
            db.add(post)
            await db.commit()
            await db.refresh(post)
            return post

        post_id = self._next_post_id
        self._next_post_id += 1
        self._posts[post_id] = {
            "id": post_id, "user_id": user_id, "title": _title,
            "content": _content, "category": _category,
            "tags": tags or [], "status": "published",
            "created_at": time.time(), "view_count": 0,
            "like_count": 0, "comment_count": 0,
        }
        return type("Post", (), {"id": post_id, "title": _title, "content": _content, "category": _category})()

    async def get_post(self, db: AsyncSession, post_id: int) -> Optional[object]:
        stmt = select(Post).where(Post.id == post_id, Post.is_deleted.is_(False))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_post_any(self, db: AsyncSession, post_id: int):
        stmt = select(Post).where(Post.id == post_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_comment(self, db: AsyncSession, comment_id: int):
        stmt = select(Comment).where(Comment.id == comment_id, Comment.is_deleted.is_(False))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_comment_any(self, db: AsyncSession, comment_id: int):
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def restore_comment(self, db: AsyncSession, comment) -> bool:
        comment.is_deleted = False
        await db.commit()
        return True

    async def get_comments_visible(self, db: AsyncSession, post_id: int, page: int = 1, page_size: int = 10, viewer_user_id: int | None = None, viewer_role: str | None = None, include_unapproved: bool = False) -> tuple[list, int]:
        conditions = [Comment.post_id == post_id, Comment.is_deleted.is_(False)]
        if not include_unapproved:
            conditions.append(Comment.review_status == "approved")
        count_stmt = select(func.count()).select_from(Comment).where(*conditions)
        result = await db.execute(count_stmt)
        total = result.scalar() or 0
        stmt = select(Comment).where(*conditions).order_by(Comment.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(stmt)
        comments = result.scalars().all()
        return comments, total

    async def get_user_favorites(self, db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10, category: str | None = None, keyword: str | None = None) -> tuple[list, int]:
        from app.models.forum import PostFavorite
        conditions = [PostFavorite.user_id == user_id]
        count_stmt = select(func.count()).select_from(PostFavorite).where(*conditions)
        total = (await db.execute(count_stmt)).scalar() or 0
        stmt = select(PostFavorite).where(*conditions).order_by(PostFavorite.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        favorites = (await db.execute(stmt)).scalars().all()
        return favorites, total

    async def toggle_post_like(self, db: AsyncSession, post_id: int, user_id: int) -> tuple[bool, int]:
        return await ForumPostService.toggle_post_like(db, post_id, user_id)

    async def toggle_post_favorite(self, db: AsyncSession, post_id: int, user_id: int) -> tuple[bool, int]:
        return await ForumPostService.toggle_post_favorite(db, post_id, user_id)

    async def toggle_reaction(self, db: AsyncSession, post_id: int, user_id: int, emoji: str) -> tuple[bool, int]:
        return await ForumPostService.toggle_reaction(db, post_id, user_id, emoji)

    async def get_post_reactions(self, db: AsyncSession, post_id: int) -> list[dict]:
        return await ForumPostService.get_post_reactions(db, post_id)

    async def toggle_comment_like(self, db: AsyncSession, comment_id: int, user_id: int) -> tuple[bool, int]:
        return await ForumCommentService.toggle_comment_like(db, comment_id, user_id)

    async def create_comment(self, db: AsyncSession, post_id: int, user_id: int, content: str = None, parent_id: int | None = None, **kwargs) -> object:
        return await ForumCommentService.create_comment(db, post_id=post_id, user_id=user_id, content=content, parent_id=parent_id, **kwargs)

    async def delete_comment(self, db: AsyncSession, comment) -> None:
        comment.is_deleted = True
        await db.commit()

    async def list_posts(self, category: Optional[str] = None, limit: int = 20, offset: int = 0) -> list[dict]:
        posts = list(self._posts.values())
        if category:
            posts = [p for p in posts if p["category"] == category]
        return posts[offset:offset + limit]

    async def delete_post(self, post_id: int, user_id: int) -> dict:
        post = self._posts.get(post_id)
        if not post:
            return {"success": False, "error": "帖子不存在"}
        if post["user_id"] != user_id:
            return {"success": False, "error": "无权删除"}
        del self._posts[post_id]
        return {"success": True}


class ForumPostService:
    def __init__(self):
        self._forum_service = ForumService()

    @staticmethod
    async def get_posts(db: AsyncSession, page: int = 1, page_size: int = 10, category: str = None, keyword: str = None, is_essence: bool = None, **kwargs) -> tuple[list, int]:
        conditions = [Post.is_deleted.is_(False)]
        if category:
            conditions.append(Post.category == category)
        if keyword:
            conditions.append(Post.title.ilike(f"%{keyword}%"))
        if is_essence is not None:
            conditions.append(Post.is_essence.is_(is_essence))
        stmt = select(Post).where(*conditions).order_by(Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(stmt)
        posts = result.scalars().all()
        count_stmt = select(func.count()).select_from(Post).where(*conditions)
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0
        return posts, total

    @staticmethod
    def _safe_int(value, default=0) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, (float, str)):
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        return default

    @staticmethod
    async def toggle_post_like(db: AsyncSession, post_id: int, user_id: int) -> tuple[bool, int]:
        from app.models.forum import PostLike
        stmt = select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            await db.delete(existing)
            await db.commit()
            count_stmt = select(func.count()).select_from(PostLike).where(PostLike.post_id == post_id)
            count_result = await db.execute(count_stmt)
            count = ForumPostService._safe_int(count_result.scalar(), 0)
            return False, count
        else:
            like = PostLike(post_id=post_id, user_id=user_id)
            db.add(like)
            await db.commit()
            count_stmt = select(func.count()).select_from(PostLike).where(PostLike.post_id == post_id)
            count_result = await db.execute(count_stmt)
            count = ForumPostService._safe_int(count_result.scalar(), 1)
            return True, count

    @staticmethod
    async def toggle_post_favorite(db: AsyncSession, post_id: int, user_id: int) -> tuple[bool, int]:
        from app.models.forum import PostFavorite
        stmt = select(PostFavorite).where(PostFavorite.post_id == post_id, PostFavorite.user_id == user_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            await db.delete(existing)
            await db.commit()
            count_stmt = select(func.count()).select_from(PostFavorite).where(PostFavorite.post_id == post_id)
            count_result = await db.execute(count_stmt)
            count = ForumPostService._safe_int(count_result.scalar(), 0)
            return False, count
        else:
            fav = PostFavorite(post_id=post_id, user_id=user_id)
            db.add(fav)
            await db.commit()
            count_stmt = select(func.count()).select_from(PostFavorite).where(PostFavorite.post_id == post_id)
            count_result = await db.execute(count_stmt)
            count = ForumPostService._safe_int(count_result.scalar(), 1)
            return True, count

    @staticmethod
    async def delete_post(db: AsyncSession, post) -> None:
        post.is_deleted = True
        await db.commit()

    @staticmethod
    async def update_post(db: AsyncSession, post, post_data=None, **kwargs) -> object:
        if post_data:
            for field, value in post_data:
                if value is not None and hasattr(post, field):
                    setattr(post, field, value)
        await db.commit()
        await db.refresh(post)
        return post

    @staticmethod
    async def is_post_liked(db: AsyncSession, post_id: int, user_id: int) -> bool:
        from app.models.forum import PostLike
        stmt = select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_post_favorite_count(db: AsyncSession, post_id: int) -> int:
        from app.models.forum import PostFavorite
        stmt = select(func.count()).select_from(PostFavorite).where(PostFavorite.post_id == post_id)
        result = await db.execute(stmt)
        return ForumPostService._safe_int(result.scalar(), 0)

    @staticmethod
    async def get_posts_favorite_counts(db: AsyncSession, post_ids: list[int]) -> dict:
        if not post_ids:
            return {}
        from app.models.forum import PostFavorite
        stmt = select(PostFavorite.post_id, func.count()).where(PostFavorite.post_id.in_(post_ids)).group_by(PostFavorite.post_id)
        result = await db.execute(stmt)
        try:
            return dict(result.all())
        except (TypeError, ValueError):
            return {}

    @staticmethod
    async def get_user_stats(db: AsyncSession, user_id: int) -> dict:
        posts_count = ForumPostService._safe_int((await db.execute(select(func.count()).select_from(Post).where(Post.user_id == user_id, Post.is_deleted.is_(False)))).scalar(), 0)
        comments_count = ForumPostService._safe_int((await db.execute(select(func.count()).select_from(Comment).where(Comment.user_id == user_id, Comment.is_deleted.is_(False)))).scalar(), 0)
        from app.models.forum import PostLike
        likes_count = ForumPostService._safe_int((await db.execute(select(func.count()).select_from(PostLike).where(PostLike.post_id.in_(select(Post.id).where(Post.user_id == user_id))))).scalar(), 0)
        from app.models.forum import PostFavorite
        favorites_count = ForumPostService._safe_int((await db.execute(select(func.count()).select_from(PostFavorite).where(PostFavorite.post_id.in_(select(Post.id).where(Post.user_id == user_id))))).scalar(), 0)
        return {"posts": posts_count, "comments": comments_count, "likes": likes_count, "favorites": favorites_count}

    @staticmethod
    async def set_post_hot(db: AsyncSession, post_id: int, is_hot: bool = True) -> bool:
        stmt = select(Post).where(Post.id == post_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        if not post:
            return False
        post.is_hot = is_hot
        await db.commit()
        return True

    @staticmethod
    async def set_post_essence(db: AsyncSession, post_id: int, is_essence: bool = True) -> bool:
        stmt = select(Post).where(Post.id == post_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        if not post:
            return False
        post.is_essence = is_essence
        await db.commit()
        return True

    @staticmethod
    async def set_post_pinned(db: AsyncSession, post_id: int, is_pinned: bool = True) -> bool:
        stmt = select(Post).where(Post.id == post_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        if not post:
            return False
        post.is_pinned = is_pinned
        await db.commit()
        return True

    @staticmethod
    async def toggle_reaction(db: AsyncSession, post_id: int, user_id: int, emoji: str) -> tuple[bool, int]:
        from app.models.forum import PostReaction
        stmt = select(PostReaction).where(PostReaction.post_id == post_id, PostReaction.user_id == user_id, PostReaction.emoji == emoji)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            await db.delete(existing)
            await db.commit()
            count_stmt = select(func.count()).select_from(PostReaction).where(PostReaction.post_id == post_id, PostReaction.emoji == emoji)
            count_result = await db.execute(count_stmt)
            count = ForumPostService._safe_int(count_result.scalar(), 0)
            return False, count
        else:
            reaction = PostReaction(post_id=post_id, user_id=user_id, emoji=emoji)
            db.add(reaction)
            await db.commit()
            count_stmt = select(func.count()).select_from(PostReaction).where(PostReaction.post_id == post_id, PostReaction.emoji == emoji)
            count_result = await db.execute(count_stmt)
            count = ForumPostService._safe_int(count_result.scalar(), 1)
            return True, count

    @staticmethod
    async def get_post_reactions(db: AsyncSession, post_id: int) -> list[dict]:
        from app.models.forum import PostReaction
        try:
            stmt = select(PostReaction.emoji, func.count()).where(PostReaction.post_id == post_id).group_by(PostReaction.emoji)
            result = await db.execute(stmt)
            return [{"type": emoji, "count": count} for emoji, count in result.all()]
        except (TypeError, ValueError):
            return []

    @staticmethod
    async def get_posts_reactions(db: AsyncSession, post_ids: list[int]) -> dict:
        if not post_ids:
            return {}
        from app.models.forum import PostReaction
        try:
            stmt = select(PostReaction.post_id, PostReaction.emoji, func.count()).where(PostReaction.post_id.in_(post_ids)).group_by(PostReaction.post_id, PostReaction.emoji)
            result = await db.execute(stmt)
            reactions = {}
            for post_id, emoji, count in result.all():
                if post_id not in reactions:
                    reactions[post_id] = []
                reactions[post_id].append({"type": emoji, "count": count})
            return reactions
        except (TypeError, ValueError):
            return {}


class ForumCommentService:
    def __init__(self):
        self._comments: dict[int, dict] = {}
        self._next_comment_id = 1

    @staticmethod
    async def create_comment(db: AsyncSession, post_id: int, user_id: int, comment_data=None, content: str = None, parent_id: int | None = None, **kwargs) -> object:
        _content = content or (getattr(comment_data, "content", "") if comment_data else "")
        _parent_id = parent_id or (getattr(comment_data, "parent_id", None) if comment_data else None)
        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            content=_content,
            parent_id=_parent_id,
            review_status="pending",
            is_deleted=False,
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment

    @staticmethod
    async def get_comments(db: AsyncSession, post_id: int, page: int = 1, page_size: int = 10, **kwargs) -> tuple[list, int]:
        conditions = [Comment.post_id == post_id, Comment.is_deleted.is_(False)]
        stmt = select(Comment).where(*conditions).order_by(Comment.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(stmt)
        comments = result.scalars().all()
        count_stmt = select(func.count()).select_from(Comment).where(*conditions)
        count_result = await db.execute(count_stmt)
        total_raw = count_result.scalar()
        if isinstance(total_raw, int):
            total = total_raw
        else:
            total = len(comments)
        return comments, total

    @staticmethod
    async def delete_comment(db: AsyncSession, comment) -> None:
        comment.is_deleted = True
        await db.commit()

    @staticmethod
    async def toggle_comment_like(db: AsyncSession, comment_id: int, user_id: int) -> tuple[bool, int]:
        stmt = select(CommentLike).where(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            await db.delete(existing)
            await db.commit()
            count_stmt = select(func.count()).select_from(CommentLike).where(CommentLike.comment_id == comment_id)
            count_result = await db.execute(count_stmt)
            count = ForumPostService._safe_int(count_result.scalar(), 0)
            return False, count
        else:
            like = CommentLike(comment_id=comment_id, user_id=user_id)
            db.add(like)
            await db.commit()
            count_stmt = select(func.count()).select_from(CommentLike).where(CommentLike.comment_id == comment_id)
            count_result = await db.execute(count_stmt)
            count = ForumPostService._safe_int(count_result.scalar(), 1)
            return True, count


forum_service = ForumService()
forum_service.get_posts = ForumPostService.get_posts
forum_service.get_posts_favorite_counts = ForumPostService.get_posts_favorite_counts
forum_service.get_posts_reactions = ForumPostService.get_posts_reactions
forum_service.get_post_favorite_count = ForumPostService.get_post_favorite_count
forum_service.get_post_reactions = ForumPostService.get_post_reactions
forum_service.toggle_post_like = ForumPostService.toggle_post_like
forum_service.toggle_post_favorite = ForumPostService.toggle_post_favorite
forum_service.is_post_liked = ForumPostService.is_post_liked
forum_service.get_user_stats = ForumPostService.get_user_stats
forum_service.set_post_hot = ForumPostService.set_post_hot
forum_service.set_post_essence = ForumPostService.set_post_essence
forum_service.set_post_pinned = ForumPostService.set_post_pinned
forum_service.toggle_reaction = ForumPostService.toggle_reaction
forum_service.create_comment = ForumCommentService.create_comment
forum_service.get_comments = ForumCommentService.get_comments
forum_service.delete_comment = ForumCommentService.delete_comment
forum_service.toggle_comment_like = ForumCommentService.toggle_comment_like
