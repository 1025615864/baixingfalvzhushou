from __future__ import annotations

from datetime import datetime


class NewsTopicService:
    async def list_topics(self, db, active_only=True):
        raise NotImplementedError

    async def get_topic(self, db, topic_id=None):
        raise NotImplementedError

    async def create_topic(self, db, data):
        raise NotImplementedError

    async def update_topic(self, db, topic, data):
        raise NotImplementedError

    async def delete_topic(self, db, topic_id=None):
        raise NotImplementedError

    async def list_topic_items_brief(self, db, topic_id=None):
        raise NotImplementedError

    async def add_topic_item(self, db, topic_id=None, news_id=None):
        raise NotImplementedError

    async def add_topic_items_bulk(self, db, topic_id=None, news_ids=None):
        raise NotImplementedError

    async def update_topic_item_position(self, db, topic_id=None, item_id=None, position=None):
        raise NotImplementedError

    async def remove_topic_item(self, db, topic_id=None, item_id=None):
        raise NotImplementedError

    async def remove_topic_items_bulk(self, db, topic_id=None, item_ids=None):
        raise NotImplementedError

    async def reindex_topic_items(self, db, topic_id=None):
        raise NotImplementedError

    async def reorder_topic_items(self, db, topic_id=None, item_ids=None):
        raise NotImplementedError
