"""帖子缓存"""
import json
import os
from typing import Optional, List
import redis.asyncio as redis


class PostCache:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client: Optional[redis.Redis] = None
        self.detail_ttl = 600
        self.list_ttl = 300

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    async def get_post_detail(self, post_id: int) -> Optional[dict]:
        key = f"post:detail:{post_id}"
        client = await self._get_client()
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_post_detail(self, post_id: int, post_data: dict):
        key = f"post:detail:{post_id}"
        client = await self._get_client()
        await client.setex(key, self.detail_ttl, json.dumps(post_data, default=str))

    async def invalidate_post(self, post_id: int):
        key = f"post:detail:{post_id}"
        client = await self._get_client()
        await client.delete(key)

    async def get_post_list(
        self,
        category: str = None,
        page: int = 1,
        sort_by: str = "latest"
    ) -> Optional[dict]:
        key = f"post:list:{category or 'all'}:{sort_by}:{page}"
        client = await self._get_client()
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_post_list(
        self,
        posts_data: dict,
        category: str = None,
        page: int = 1,
        sort_by: str = "latest"
    ):
        key = f"post:list:{category or 'all'}:{sort_by}:{page}"
        client = await self._get_client()
        await client.setex(key, self.list_ttl, json.dumps(posts_data, default=str))

    async def invalidate_post_list(self, category: str = None):
        client = await self._get_client()
        if category:
            pattern = f"post:list:{category}:*"
            pattern_all = f"post:list:*:{category}:*"
            keys = []
            keys.extend(await client.keys(pattern))
            keys.extend(await client.keys(pattern_all))
            if keys:
                await client.delete(*keys)
        else:
            keys = await client.keys("post:list:*")
            if keys:
                await client.delete(*keys)

    async def invalidate_user_posts(self, user_id: int):
        client = await self._get_client()
        pattern = f"post:list:*"
        keys = await client.keys(pattern)
        if keys:
            await client.delete(*keys)

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
        await client.setex(key, self.list_ttl, json.dumps(posts, default=str))

    async def invalidate_hot_posts(self, category: str = None):
        key = f"hot:posts:{category or 'all'}"
        client = await self._get_client()
        await client.delete(key)

    async def incr_like_count(self, post_id: int) -> int:
        key = f"post:like_count:{post_id}"
        client = await self._get_client()
        count = await client.incr(key)
        await client.expire(key, 1800)
        return count

    async def decr_like_count(self, post_id: int) -> int:
        key = f"post:like_count:{post_id}"
        client = await self._get_client()
        count = await client.decr(key)
        if count < 0:
            await client.set(key, 0)
            count = 0
        await client.expire(key, 1800)
        return count

    async def get_like_count(self, post_id: int) -> Optional[int]:
        key = f"post:like_count:{post_id}"
        client = await self._get_client()
        count = await client.get(key)
        return int(count) if count else None

    async def set_like_count(self, post_id: int, count: int):
        key = f"post:like_count:{post_id}"
        client = await self._get_client()
        await client.set(key, count)
        await client.expire(key, 1800)


post_cache = PostCache()
