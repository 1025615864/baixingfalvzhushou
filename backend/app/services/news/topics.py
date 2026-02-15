"""新闻专题服务

提供新闻专题(NewsTopic)管理功能
"""
from collections.abc import Mapping, Sequence
from typing import Any, cast

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.news import NewsTopic, NewsTopicItem


class NewsTopicService:
    """新闻专题服务"""

    async def list_topics(self, db: AsyncSession,
                          active_only: bool = True) -> list[NewsTopic]:
        """获取专题列表"""
        query = select(NewsTopic)

        if active_only:
            query = query.where(NewsTopic.is_active)

        query = query.order_by(NewsTopic.sort_order, NewsTopic.created_at)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_topic(self, db: AsyncSession,
                        topic_id: int) -> NewsTopic | None:
        """获取专题"""
        result = await db.execute(select(NewsTopic).where(NewsTopic.id == topic_id))
        return result.scalar_one_or_none()

    async def create_topic(self, db: AsyncSession,
                           data: Mapping[str, Any]) -> NewsTopic:
        """创建专题"""
        is_active = data.get("is_active", True)
        sort_order = data.get("sort_order", 0)
        auto_limit = data.get("auto_limit")
        topic = NewsTopic(
            title=cast(str, data.get("title")),
            description=cast(str | None, data.get("description")),
            cover_image=cast(str | None, data.get("cover_image")),
            is_active=bool(is_active) if is_active is not None else True,
            sort_order=int(sort_order or 0),
            auto_category=cast(str | None, data.get("auto_category")),
            auto_keyword=cast(str | None, data.get("auto_keyword")),
            auto_limit=int(auto_limit or 0),
        )
        db.add(topic)
        await db.commit()
        await db.refresh(topic)
        return topic

    async def update_topic(
        self, db: AsyncSession, topic: NewsTopic, data: Mapping[str, Any]
    ) -> NewsTopic:
        """更新专题"""
        if "title" in data:
            title = data.get("title")
            if title is not None:
                topic.title = cast(str, title)
        if "description" in data:
            topic.description = cast(str | None, data.get("description"))
        if "cover_image" in data:
            topic.cover_image = cast(str | None, data.get("cover_image"))
        if "is_active" in data:
            is_active = data.get("is_active")
            if is_active is not None:
                topic.is_active = bool(is_active)
        if "sort_order" in data:
            sort_order = data.get("sort_order")
            if sort_order is not None:
                topic.sort_order = int(sort_order)
        if "auto_category" in data:
            topic.auto_category = cast(str | None, data.get("auto_category"))
        if "auto_keyword" in data:
            topic.auto_keyword = cast(str | None, data.get("auto_keyword"))
        if "auto_limit" in data:
            auto_limit = data.get("auto_limit")
            if auto_limit is not None:
                topic.auto_limit = int(auto_limit)

        db.add(topic)
        await db.commit()
        await db.refresh(topic)
        return topic

    async def delete_topic(self, db: AsyncSession, topic_id: int) -> None:
        """删除专题"""
        topic = await self.get_topic(db, topic_id)
        if topic:
            await db.delete(topic)
            await db.commit()

    async def list_topic_items_brief(
        self, db: AsyncSession, topic_id: int, active_only: bool = True
    ) -> list[NewsTopicItem]:
        """获取专题项简要列表"""
        query = select(NewsTopicItem).where(NewsTopicItem.topic_id == topic_id)

        query = query.order_by(
            NewsTopicItem.position,
            NewsTopicItem.created_at)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def add_topic_item(
            self,
            db: AsyncSession,
            topic_id: int,
            news_id: int,
            position: int | None = None) -> NewsTopicItem:
        """添加专题项"""
        if position is None:
            max_pos = await db.execute(
                select(func.max(NewsTopicItem.position)).where(
                    NewsTopicItem.topic_id == topic_id)
            )
            position = (max_pos.scalar() or 0) + 1

        item = NewsTopicItem(
            topic_id=topic_id,
            news_id=news_id,
            position=position)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def add_topic_items_bulk(
        self, db: AsyncSession, topic_id: int, news_ids: Sequence[int]
    ) -> list[NewsTopicItem]:
        """批量添加专题项"""
        items = []
        for idx, news_id in enumerate(news_ids):
            item = NewsTopicItem(
                topic_id=topic_id,
                news_id=news_id,
                position=idx + 1)
            db.add(item)
            items.append(item)  # pyright: ignore

        await db.commit()
        for item in items:  # pyright: ignore
            await db.refresh(item)  # pyright: ignore

        return items  # pyright: ignore

    async def update_topic_item_position(
        self, db: AsyncSession, topic_id: int, item_id: int, position: int
    ) -> bool:
        """更新专题项位置"""
        result = await db.execute(
            select(NewsTopicItem).where(
                NewsTopicItem.id == item_id, NewsTopicItem.topic_id == topic_id
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return False

        item.position = position
        db.add(item)
        await db.commit()
        return True

    async def remove_topic_item(
            self, db: AsyncSession, topic_id: int, item_id: int) -> bool:
        """移除专题项"""
        result = await db.execute(
            select(NewsTopicItem).where(
                NewsTopicItem.id == item_id, NewsTopicItem.topic_id == topic_id
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return False

        await db.delete(item)
        await db.commit()
        return True

    async def remove_topic_items_bulk(
        self, db: AsyncSession, topic_id: int, item_ids: Sequence[int]
    ) -> int:
        """批量移除专题项"""
        result = await db.execute(
            delete(NewsTopicItem).where(
                NewsTopicItem.topic_id == topic_id, NewsTopicItem.id.in_(
                    item_ids)
            )
        )
        await db.commit()
        return int(getattr(result, "rowcount", 0) or 0)

    async def reindex_topic_items(
            self, db: AsyncSession, topic_id: int) -> int:
        """重新索引专题项"""
        items = await self.list_topic_items_brief(db, topic_id, active_only=False)

        reindexed = 0
        for idx, item in enumerate(items):
            item.position = idx + 1
            db.add(item)
            reindexed += 1

        await db.commit()
        return reindexed

    async def reorder_topic_items(
        self, db: AsyncSession, topic_id: int, item_ids: Sequence[int]
    ) -> int:
        """重新排序专题项"""
        reordered = 0
        for idx, item_id in enumerate(item_ids):
            result = await db.execute(
                select(NewsTopicItem).where(
                    NewsTopicItem.id == item_id, NewsTopicItem.topic_id == topic_id
                )
            )
            item = result.scalar_one_or_none()
            if item:
                item.position = idx + 1
                db.add(item)
                reordered += 1

        await db.commit()
        return reordered


# 单例
news_topic_service = NewsTopicService()
