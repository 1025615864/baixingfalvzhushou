"""热门缓存"""
import json
import os
from typing import Optional, List
import redis.asyncio as redis


class HotCache:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client: Optional[redis.Redis] = None
        self.ttl = 300

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    async def get_hot_posts(self, category: str = None) -> Optional[List[dict]]:
        key = f"hot:posts:{category or 'all'}"
        client = await self._get_client()
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_hot_posts(self, posts: List[dict], category: str = None):
        key = f"hot:posts:{category or 'all'}"
        client = await self._get_client()
        await client.setex(key, self.ttl, json.dumps(posts))

    async def invalidate(self, category: str = None):
        key = f"hot:posts:{category or 'all'}"
        client = await self._get_client()
        await client.delete(key)


hot_cache = HotCache()
