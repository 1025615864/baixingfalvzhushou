import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class RedisCacheService:
    def __init__(self):
        settings = get_settings()
        self._url = settings.redis_url
        self._ttl = settings.cache_ttl
        self._client: Optional[aioredis.Redis] = None

    async def _get_client(self) -> Optional[aioredis.Redis]:
        if self._client is None:
            try:
                self._client = aioredis.from_url(
                    self._url,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                )
                await self._client.ping()
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._client = None
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, key: str) -> Optional[Any]:
        try:
            client = await self._get_client()
            if client is None:
                return None
            data = await client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logger.error(f"Cache get failed for key '{key}': {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            client = await self._get_client()
            if client is None:
                return False
            serialized = json.dumps(value, ensure_ascii=False)
            effective_ttl = ttl if ttl is not None else self._ttl
            await client.setex(key, effective_ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set failed for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            client = await self._get_client()
            if client is None:
                return False
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete failed for key '{key}': {e}")
            return False

    async def delete_pattern(self, pattern: str) -> bool:
        try:
            client = await self._get_client()
            if client is None:
                return False
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache delete_pattern failed for pattern '{pattern}': {e}")
            return False


redis_cache_service = RedisCacheService()
