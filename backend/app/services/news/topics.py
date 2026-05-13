from __future__ import annotations

from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsTopic, NewsTopicItem, News


class NewsTopicService:
    async def list_topics(self, db: AsyncSession, active_only=True):
        conditions = []
        if active_only:
            conditions.append(NewsTopic.is_active.is_(True))
        if conditions:
            stmt = select(NewsTopic).where(*conditions).order_by(NewsTopic.sort_order, NewsTopic.created_at.desc())
        else:
            stmt = select(NewsTopic).order_by(NewsTopic.sort_order, NewsTopic.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_topic(self, db: AsyncSession, topic_id=None):
        if topic_id is None:
            return None
        stmt = select(NewsTopic).where(NewsTopic.id == topic_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_topic(self, db: AsyncSession, data):
        topic = NewsTopic(
            title=data.title if hasattr(data, "title") else data.get("title", ""),
            description=data.description if hasattr(data, "description") else data.get("description"),
            cover_image=data.cover_image if hasattr(data, "cover_image") else data.get("cover_image"),
            sort_order=data.sort_order if hasattr(data, "sort_order") else data.get("sort_order", 0),
            is_active=data.is_active if hasattr(data, "is_active") else data.get("is_active", True),
        )
        db.add(topic)
        await db.commit()
        await db.refresh(topic)
        return topic

    async def update_topic(self, db: AsyncSession, topic, data):
        if data:
            for field, value in data:
                if value is not None and hasattr(topic, field):
                    setattr(topic, field, value)
        await db.commit()
        await db.refresh(topic)
        return topic

    async def delete_topic(self, db: AsyncSession, topic_id=None):
        if topic_id is None:
            return
        stmt = sa_delete(NewsTopicItem).where(NewsTopicItem.topic_id == topic_id)
        await db.execute(stmt)
        stmt = sa_delete(NewsTopic).where(NewsTopic.id == topic_id)
        await db.execute(stmt)
        await db.commit()

    async def list_topic_items_brief(self, db: AsyncSession, topic_id=None):
        if topic_id is None:
            return []
        stmt = select(NewsTopicItem).where(NewsTopicItem.topic_id == topic_id).order_by(NewsTopicItem.position, NewsTopicItem.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def add_topic_item(self, db: AsyncSession, topic_id=None, news_id=None):
        if topic_id is None or news_id is None:
            return None
        max_pos_stmt = select(func.coalesce(func.max(NewsTopicItem.position), 0)).where(NewsTopicItem.topic_id == topic_id)
        result = await db.execute(max_pos_stmt)
        max_pos = result.scalar() or 0
        item = NewsTopicItem(topic_id=topic_id, news_id=news_id, position=max_pos + 1)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def add_topic_items_bulk(self, db: AsyncSession, topic_id=None, news_ids=None):
        if topic_id is None or not news_ids:
            return []
        items = []
        max_pos_stmt = select(func.coalesce(func.max(NewsTopicItem.position), 0)).where(NewsTopicItem.topic_id == topic_id)
        result = await db.execute(max_pos_stmt)
        max_pos = result.scalar() or 0
        for i, news_id in enumerate(news_ids):
            item = NewsTopicItem(topic_id=topic_id, news_id=news_id, position=max_pos + i + 1)
            db.add(item)
            items.append(item)
        await db.commit()
        for item in items:
            await db.refresh(item)
        return items

    async def update_topic_item_position(self, db: AsyncSession, topic_id=None, item_id=None, position=None):
        if topic_id is None or item_id is None:
            return None
        stmt = select(NewsTopicItem).where(NewsTopicItem.id == item_id, NewsTopicItem.topic_id == topic_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            return None
        item.position = position if position is not None else item.position
        await db.commit()
        await db.refresh(item)
        return item

    async def remove_topic_item(self, db: AsyncSession, topic_id=None, item_id=None):
        if topic_id is None or item_id is None:
            return
        stmt = sa_delete(NewsTopicItem).where(NewsTopicItem.id == item_id, NewsTopicItem.topic_id == topic_id)
        await db.execute(stmt)
        await db.commit()

    async def remove_topic_items_bulk(self, db: AsyncSession, topic_id=None, item_ids=None):
        if topic_id is None or not item_ids:
            return
        stmt = sa_delete(NewsTopicItem).where(NewsTopicItem.topic_id == topic_id, NewsTopicItem.id.in_(item_ids))
        await db.execute(stmt)
        await db.commit()

    async def reindex_topic_items(self, db: AsyncSession, topic_id=None):
        if topic_id is None:
            return
        stmt = select(NewsTopicItem).where(NewsTopicItem.topic_id == topic_id).order_by(NewsTopicItem.position, NewsTopicItem.created_at)
        result = await db.execute(stmt)
        items = result.scalars().all()
        for i, item in enumerate(items, 1):
            item.position = i
        await db.commit()

    async def reorder_topic_items(self, db: AsyncSession, topic_id=None, item_ids=None):
        if topic_id is None or not item_ids:
            return
        for i, item_id in enumerate(item_ids, 1):
            stmt = select(NewsTopicItem).where(NewsTopicItem.id == item_id, NewsTopicItem.topic_id == topic_id)
            result = await db.execute(stmt)
            item = result.scalar_one_or_none()
            if item:
                item.position = i
        await db.commit()


news_topic_service = NewsTopicService()
