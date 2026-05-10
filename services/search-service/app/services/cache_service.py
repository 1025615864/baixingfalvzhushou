import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from app.config.settings import settings

logger = logging.getLogger(__name__)


class RedisCacheService:
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._available = False

    async def _get_client(self) -> Optional[redis.Redis]:
        if self._client is not None:
            return self._client
        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
            await self._client.ping()
            self._available = True
            logger.info("Redis cache connected")
        except Exception as e:
            self._available = False
            self._client = None
            logger.warning(f"Redis unavailable, caching disabled: {e}")
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
            self._available = False

    async def get(self, key: str) -> Optional[str]:
        client = await self._get_client()
        if client is None:
            return None
        try:
            return await client.get(key)
        except Exception as e:
            logger.warning(f"Cache get error for key '{key}': {e}")
            return None

    async def set(self, key: str, value: str, ttl: int = 60) -> bool:
        client = await self._get_client()
        if client is None:
            return False
        try:
            await client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        client = await self._get_client()
        if client is None:
            return False
        try:
            await client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key '{key}': {e}")
            return False

    async def get_json(self, key: str) -> Optional[Any]:
        data = await self.get(key)
        if data is None:
            return None
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return None

    async def set_json(self, key: str, value: Any, ttl: int = 60) -> bool:
        try:
            return await self.set(key, json.dumps(value, default=str), ttl)
        except (TypeError, ValueError) as e:
            logger.warning(f"Cache set_json error for key '{key}': {e}")
            return False

    @property
    def is_available(self) -> bool:
        return self._available


cache_service = RedisCacheService()
