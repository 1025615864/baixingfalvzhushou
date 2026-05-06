"""草稿箱服务"""
import json
import logging
from typing import Optional, List
from datetime import datetime, timezone

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class DraftCache:
    def __init__(self):
        self.redis_url = "redis://localhost:6379"
        self._client = None
        self.ttl = 86400

    def _get_client(self):
        if self._client is None and redis:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    def _get_key(self, user_id: int) -> str:
        return f"draft:user:{user_id}"

    async def save_draft(self, user_id: int, draft_data: dict) -> bool:
        try:
            client = self._get_client()
            if not client:
                return False
            key = self._get_key(user_id)
            draft_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            await client.setex(key, self.ttl, json.dumps(draft_data, default=str))
            return True
        except Exception as e:
            logger.error(f"Failed to save draft: {e}")
            return False

    async def get_draft(self, user_id: int) -> Optional[dict]:
        try:
            client = self._get_client()
            if not client:
                return None
            key = self._get_key(user_id)
            data = await client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get draft: {e}")
            return None

    async def delete_draft(self, user_id: int) -> bool:
        try:
            client = self._get_client()
            if not client:
                return False
            key = self._get_key(user_id)
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete draft: {e}")
            return False


draft_cache = DraftCache()
