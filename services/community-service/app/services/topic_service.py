"""Topic 服务 - 话题/板块业务逻辑层"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from fastapi import HTTPException

from ..models.topic import Topic, BestAnswer
from ..models.post import Post
from ..middleware.auth import AuthUser


def utc_now():
    return datetime.now(timezone.utc)


class TopicService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_topic(
        self,
        name: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        sort_order: int = 0,
        is_legal_category: bool = False,
        created_by: int = 0
    ) -> Topic:
        existing = await self.db.execute(
            select(Topic).where(Topic.name == name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="话题名称已存在")

        topic = Topic(
            name=name,
            description=description,
            icon=icon,
            sort_order=sort_order,
            is_legal_category=is_legal_category,
        )
        self.db.add(topic)
        await self.db.commit()
        await self.db.refresh(topic)
        return topic

    async def get_topic(self, topic_id: int) -> Optional[Topic]:
        result = await self.db.execute(
            select(Topic).where(Topic.id == topic_id)
        )
        return result.scalar_one_or_none()

    async def get_topic_by_name(self, name: str) -> Optional[Topic]:
        result = await self.db.execute(
            select(Topic).where(Topic.name == name)
        )
        return result.scalar_one_or_none()

    async def list_topics(
        self,
        is_active: Optional[bool] = None,
        is_legal_category: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Topic], int]:
        conditions = []
        if is_active is not None:
            conditions.append(Topic.is_active == is_active)
        if is_legal_category is not None:
            conditions.append(Topic.is_legal_category == is_legal_category)

        query = select(Topic)
        if conditions:
            query = query.where(and_(*conditions))

        count_result = await self.db.execute(
            select(func.count()).select_from(Topic)
        )
        total = count_result.scalar() or 0

        query = query.order_by(desc(Topic.sort_order), Topic.id)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update_topic(
        self,
        topic_id: int,
        current_user: AuthUser,
        name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        sort_order: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_legal_category: Optional[bool] = None
    ) -> Topic:
        if current_user.role not in ("admin", "moderator"):
            raise HTTPException(status_code=403, detail="需要管理员权限")

        result = await self.db.execute(
            select(Topic).where(Topic.id == topic_id)
        )
        topic = result.scalar_one_or_none()
        if not topic:
            raise HTTPException(status_code=404, detail="话题不存在")

        if name is not None:
            topic.name = name
        if description is not None:
            topic.description = description
        if icon is not None:
            topic.icon = icon
        if sort_order is not None:
            topic.sort_order = sort_order
        if is_active is not None:
            topic.is_active = is_active
        if is_legal_category is not None:
            topic.is_legal_category = is_legal_category

        topic.updated_at = utc_now()
        await self.db.commit()
        await self.db.refresh(topic)
        return topic

    async def delete_topic(self, topic_id: int, current_user: AuthUser) -> bool:
        if current_user.role not in ("admin", "moderator"):
            raise HTTPException(status_code=403, detail="需要管理员权限")

        result = await self.db.execute(
            select(Topic).where(Topic.id == topic_id)
        )
        topic = result.scalar_one_or_none()
        if not topic:
            raise HTTPException(status_code=404, detail="话题不存在")

        topic.is_active = False
        topic.updated_at = utc_now()
        await self.db.commit()
        return True

    async def get_topic_posts(
        self,
        topic_name: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Post], int]:
        topic = await self.get_topic_by_name(topic_name)
        if not topic:
            raise HTTPException(status_code=404, detail="话题不存在")

        conditions = [
            Post.category == topic_name,
            Post.status == "published"
        ]

        query = select(Post).where(and_(*conditions))

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        query = query.order_by(desc(Post.is_pinned), desc(Post.hot_score))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total


class BestAnswerService:
    def __init__(self, db: AsyncSession, event_bus=None):
        self.db = db
        self.event_bus = event_bus

    async def mark_best_answer(
        self,
        post_id: int,
        comment_id: int,
        selected_by: int
    ) -> BestAnswer:
        post_result = await self.db.execute(
            select(Post).where(Post.id == post_id)
        )
        post = post_result.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        if post.user_id != selected_by:
            raise HTTPException(status_code=403, detail="只有帖子作者可以标记最佳回答")

        comment_result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = comment_result.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        existing = await self.db.execute(
            select(BestAnswer).where(BestAnswer.post_id == post_id)
        )
        best_answer = existing.scalar_one_or_none()

        if best_answer:
            best_answer.comment_id = comment_id
            best_answer.selected_by = selected_by
            best_answer.selected_at = utc_now()
        else:
            best_answer = BestAnswer(
                post_id=post_id,
                comment_id=comment_id,
                selected_by=selected_by
            )
            self.db.add(best_answer)

        post.is_best_answer = True
        await self.db.commit()
        await self.db.refresh(best_answer)

        if self.event_bus:
            await self.event_bus.publish_best_answer_selected(post, comment, selected_by)

        return best_answer

    async def get_best_answer(self, post_id: int) -> Optional[BestAnswer]:
        result = await self.db.execute(
            select(BestAnswer).where(BestAnswer.post_id == post_id)
        )
        return result.scalar_one_or_none()

    async def remove_best_answer(self, post_id: int, current_user: AuthUser) -> bool:
        if current_user.role not in ("admin", "moderator"):
            raise HTTPException(status_code=403, detail="需要管理员权限")

        result = await self.db.execute(
            select(BestAnswer).where(BestAnswer.post_id == post_id)
        )
        best_answer = result.scalar_one_or_none()
        if not best_answer:
            raise HTTPException(status_code=404, detail="最佳回答不存在")

        post_result = await self.db.execute(
            select(Post).where(Post.id == post_id)
        )
        post = post_result.scalar_one_or_none()
        if post:
            post.is_best_answer = False

        await self.db.delete(best_answer)
        await self.db.commit()
        return True
