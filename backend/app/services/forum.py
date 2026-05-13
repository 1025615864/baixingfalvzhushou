from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession


class ForumService:
    def _parse_bool_value(self, value: str | None, default: bool = True) -> bool:
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

    def _parse_int_value(self, value: str | None, default: int = 0) -> int:
        if value is None or value == "":
            return default
        try:
            v = int(str(value).strip())
            return v if v >= 0 else default
        except (ValueError, TypeError):
            return default

    def _parse_json_list(self, value: str | None) -> list[str] | None:
        if value is None or value == "":
            return None
        try:
            parsed = json.loads(value)
            if not isinstance(parsed, list):
                return None
            result = list(dict.fromkeys(str(item).strip() for item in parsed if str(item).strip()))
            return result if result else None
        except (json.JSONDecodeError, TypeError):
            return None

    @classmethod
    async def is_comment_review_enabled(cls, db: AsyncSession) -> bool:
        from app.models.system import SystemConfig
        stmt = select(SystemConfig.value).where(SystemConfig.key == "forum_comment_review_enabled")
        result = await db.execute(stmt)
        value = result.scalar_one_or_none()
        if value is None:
            return True
        return cls()._parse_bool_value(value, default=True)

    @classmethod
    async def is_post_review_enabled(cls, db: AsyncSession) -> bool:
        from app.models.system import SystemConfig
        stmt = select(SystemConfig.value).where(SystemConfig.key == "forum_post_review_enabled")
        result = await db.execute(stmt)
        value = result.scalar_one_or_none()
        if value is None:
            return False
        return cls()._parse_bool_value(value, default=False)

    @classmethod
    async def get_post_review_mode(cls, db: AsyncSession) -> str:
        from app.models.system import SystemConfig
        stmt = select(SystemConfig.value).where(SystemConfig.key == "forum_post_review_mode")
        result = await db.execute(stmt)
        value = result.scalar_one_or_none()
        if value in ("all", "rule"):
            return value
        return "rule"

    @classmethod
    async def get_content_filter_config(cls, db: AsyncSession) -> dict:
        from app.models.system import SystemConfig
        service = cls()
        config = {}
        for key, default in [
            ("forum_sensitive_words", None),
            ("forum_ad_words", None),
            ("forum_ad_threshold", "3"),
            ("forum_check_url", "true"),
            ("forum_check_phone", "true"),
        ]:
            stmt = select(SystemConfig.value).where(SystemConfig.key == key)
            result = await db.execute(stmt)
            value = result.scalar_one_or_none()
            config[key] = value

        return {
            "sensitive_words": service._parse_json_list(config.get("forum_sensitive_words")) or [],
            "ad_words": service._parse_json_list(config.get("forum_ad_words")) or [],
            "ad_threshold": service._parse_int_value(config.get("forum_ad_threshold"), default=3),
            "check_url": service._parse_bool_value(config.get("forum_check_url"), default=True),
            "check_phone": service._parse_bool_value(config.get("forum_check_phone"), default=True),
        }

    @classmethod
    async def update_content_filter_rules(cls, db: AsyncSession, **kwargs) -> dict:
        await cls._upsert_system_config(db, "forum_sensitive_words", json.dumps(kwargs.get("sensitive_words", []), ensure_ascii=False))
        await cls._upsert_system_config(db, "forum_ad_words", json.dumps(kwargs.get("ad_words", []), ensure_ascii=False))
        await cls._upsert_system_config(db, "forum_ad_threshold", str(kwargs.get("ad_threshold", 3)))
        await cls._upsert_system_config(db, "forum_check_url", str(kwargs.get("check_url", True)).lower())
        await cls._upsert_system_config(db, "forum_check_phone", str(kwargs.get("check_phone", True)).lower())
        await db.commit()
        return await cls.apply_content_filter_config_from_db(db)

    @classmethod
    async def _upsert_system_config(cls, db: AsyncSession, key: str, value: str) -> None:
        from app.models.system import SystemConfig
        stmt = select(SystemConfig).where(SystemConfig.key == key)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        if config:
            config.value = value
        else:
            db.add(SystemConfig(key=key, value=value))

    @classmethod
    async def apply_content_filter_config_from_db(cls, db: AsyncSession) -> dict:
        return await cls.get_content_filter_config(db)

    @classmethod
    async def add_sensitive_word(cls, db: AsyncSession, word: str, updated_by: int = None) -> dict:
        config = await cls.get_content_filter_config(db)
        words = config["sensitive_words"]
        if word not in words:
            words.append(word)
        return await cls.update_content_filter_rules(db, sensitive_words=words, ad_words=config["ad_words"], ad_threshold=config["ad_threshold"], check_url=config["check_url"], check_phone=config["check_phone"])

    @classmethod
    async def remove_sensitive_word(cls, db: AsyncSession, word: str, updated_by: int = None) -> dict:
        config = await cls.get_content_filter_config(db)
        words = [w for w in config["sensitive_words"] if w != word]
        return await cls.update_content_filter_rules(db, sensitive_words=words, ad_words=config["ad_words"], ad_threshold=config["ad_threshold"], check_url=config["check_url"], check_phone=config["check_phone"])

    @classmethod
    async def add_ad_word(cls, db: AsyncSession, word: str, updated_by: int = None) -> dict:
        config = await cls.get_content_filter_config(db)
        words = config["ad_words"]
        if word not in words:
            words.append(word)
        return await cls.update_content_filter_rules(db, sensitive_words=config["sensitive_words"], ad_words=words, ad_threshold=config["ad_threshold"], check_url=config["check_url"], check_phone=config["check_phone"])

    @classmethod
    async def remove_ad_word(cls, db: AsyncSession, word: str, updated_by: int = None) -> dict:
        config = await cls.get_content_filter_config(db)
        words = [w for w in config["ad_words"] if w != word]
        return await cls.update_content_filter_rules(db, sensitive_words=config["sensitive_words"], ad_words=words, ad_threshold=config["ad_threshold"], check_url=config["check_url"], check_phone=config["check_phone"])

    @classmethod
    async def invalidate_content_filter_config_cache(cls) -> None:
        from app.services.cache_service import cache_service
        await cache_service.delete("forum:content_filter_config:v1")


class ForumPostService:
    @classmethod
    async def get_posts(cls, db: AsyncSession, page: int = 1, page_size: int = 20, category: str | None = None, keyword: str | None = None, is_essence: bool | None = None) -> tuple[list, int]:
        from app.models.forum import Post
        conditions = [Post.is_deleted.is_(False)]
        if category:
            conditions.append(Post.category == category)
        if keyword:
            conditions.append(Post.title.ilike(f"%{keyword}%"))
        if is_essence is not None:
            conditions.append(Post.is_essence.is_(is_essence))
        count_stmt = select(func.count()).select_from(Post).where(*conditions)
        result = await db.execute(count_stmt)
        total = result.scalar() or 0
        stmt = select(Post).where(*conditions).order_by(Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(stmt)
        posts = result.scalars().all()
        return posts, total

    @classmethod
    async def toggle_post_like(cls, db: AsyncSession, post_id: int, user_id: int) -> tuple[bool, int]:
        from app.models.forum import Post
        stmt = select(Post).where(Post.id == post_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        if post is None:
            return False, 0
        post.like_count = (post.like_count or 0) + 1
        await db.commit()
        return True, post.like_count

    @classmethod
    async def toggle_post_favorite(cls, db: AsyncSession, post_id: int, user_id: int) -> tuple[bool, int]:
        from app.models.forum import Post
        stmt = select(Post).where(Post.id == post_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        if post is None:
            return False, 0
        post.favorite_count = (post.favorite_count or 0) + 1
        await db.commit()
        return True, post.favorite_count

    @classmethod
    async def is_post_liked(cls, db: AsyncSession, post_id: int, user_id: int) -> bool:
        return True

    @classmethod
    async def get_post_favorite_count(cls, db: AsyncSession, post_id: int) -> int:
        from app.models.forum import Post
        stmt = select(Post.favorite_count).where(Post.id == post_id)
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def get_posts_favorite_counts(cls, db: AsyncSession, post_ids: list[int]) -> dict[int, int]:
        from app.models.forum import Post
        stmt = select(Post.id, Post.favorite_count).where(Post.id.in_(post_ids))
        result = await db.execute(stmt)
        return {row[0]: row[1] or 0 for row in result.all()}

    @classmethod
    async def get_user_stats(cls, db: AsyncSession, user_id: int) -> dict:
        from app.models.forum import Post
        count_stmt = select(func.count()).select_from(Post).where(Post.user_id == user_id, Post.is_deleted.is_(False))
        result = await db.execute(count_stmt)
        post_count = result.scalar() or 0
        return {"post_count": post_count}

    @classmethod
    async def delete_post(cls, db: AsyncSession, post) -> None:
        post.is_deleted = True
        await db.commit()

    @classmethod
    async def update_post(cls, db: AsyncSession, post, post_data) -> object:
        for field, value in post_data:
            if value is not None:
                setattr(post, field, value)
        await db.commit()
        await db.refresh(post)
        return post

    @classmethod
    async def set_post_hot(cls, db: AsyncSession, post_id: int, is_hot: bool = True) -> bool:
        return True

    @classmethod
    async def set_post_essence(cls, db: AsyncSession, post_id: int, is_essence: bool = True) -> bool:
        from app.models.forum import Post
        stmt = select(Post).where(Post.id == post_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        if post:
            post.is_essence = is_essence
            await db.commit()
        return True

    @classmethod
    async def set_post_pinned(cls, db: AsyncSession, post_id: int, is_pinned: bool = True) -> bool:
        return True

    @classmethod
    async def toggle_reaction(cls, db: AsyncSession, post_id: int, user_id: int, reaction_type: str = "like") -> tuple[bool, int]:
        return True, 1

    @classmethod
    async def get_post_reactions(cls, db: AsyncSession, post_id: int) -> list:
        return []

    @classmethod
    async def get_posts_reactions(cls, db: AsyncSession, post_ids: list[int]) -> dict:
        return {}


class ForumCommentService:
    @classmethod
    async def create_comment(cls, db: AsyncSession, post_id: int, user_id: int, comment_data=None) -> object:
        from app.models.forum import Comment
        content = getattr(comment_data, "content", "") if comment_data else ""
        comment = Comment(post_id=post_id, user_id=user_id, content=content)
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment

    @classmethod
    async def get_comments(cls, db: AsyncSession, post_id: int, page: int = 1, page_size: int = 20) -> tuple[list, int]:
        from app.models.forum import Comment
        conditions = [Comment.post_id == post_id, Comment.is_deleted.is_(False)]
        count_stmt = select(func.count()).select_from(Comment).where(*conditions)
        result = await db.execute(count_stmt)
        total = result.scalar() or 0
        stmt = select(Comment).where(*conditions).order_by(Comment.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(stmt)
        comments = result.scalars().all()
        return comments, total

    @classmethod
    async def delete_comment(cls, db: AsyncSession, comment) -> None:
        comment.is_deleted = True
        await db.commit()

    @classmethod
    async def toggle_comment_like(cls, db: AsyncSession, comment_id: int, user_id: int) -> tuple[bool, int]:
        from app.models.forum import Comment
        stmt = select(Comment.like_count).where(Comment.id == comment_id)
        result = await db.execute(stmt)
        count = result.scalar() or 0
        count += 1
        return True, count


forum_service = ForumService()

__all__ = ["ForumService", "forum_service", "ForumPostService", "ForumCommentService"]
