"""分享统计服务"""
import hashlib
import logging
import os
from typing import Optional
from datetime import datetime, timezone

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class ShareService:
    def __init__(self):
        self.redis_url = "redis://localhost:6379"
        self._client = None
        self.base_url = os.getenv("SHARE_BASE_URL", "https://baixing.com/post")

    def _get_client(self):
        if self._client is None and redis:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    def generate_short_code(self, post_id: int) -> str:
        hash_input = f"baixing-share-{post_id}-{datetime.now(timezone.utc).date()}"
        return hashlib.urlsafe_base64_encode(
            hashlib.sha256(hash_input.encode()).digest()
        )[:8].decode()

    def generate_share_url(self, post_id: int) -> str:
        short_code = self.generate_short_code(post_id)
        return f"{self.base_url}/s/{short_code}"

    async def track_share(self, post_id: int, platform: str = "unknown") -> bool:
        try:
            client = self._get_client()
            if not client:
                return False

            short_code = self.generate_short_code(post_id)
            key = f"share:post:{short_code}"
            await client.hincrby(key, f"total", 1)
            await client.hincrby(key, f"platform:{platform}", 1)
            await client.expire(key, 86400 * 30)
            return True
        except Exception as e:
            logger.error(f"Failed to track share: {e}")
            return False

    async def get_share_stats(self, post_id: int) -> dict:
        try:
            client = self._get_client()
            if not client:
                return {"total": 0, "platforms": {}}

            short_code = self.generate_short_code(post_id)
            key = f"share:post:{short_code}"
            data = await client.hgetall(key)

            total = int(data.get("total", 0))
            platforms = {
                k.replace("platform:", ""): int(v)
                for k, v in data.items()
                if k.startswith("platform:")
            }

            return {"total": total, "platforms": platforms}
        except Exception as e:
            logger.error(f"Failed to get share stats: {e}")
            return {"total": 0, "platforms": {}}

    async def get_top_shared_posts(self, limit: int = 10) -> list:
        try:
            client = self._get_client()
            if not client:
                return []

            keys = await client.keys("share:post:*")
            if not keys:
                return []

            scores = []
            for key in keys:
                total = await client.hget(key, "total")
                if total:
                    scores.append((key, int(total)))

            scores.sort(key=lambda x: x[1], reverse=True)
            return [{"short_code": s[0].replace("share:post:", ""), "shares": s[1]} for s in scores[:limit]]
        except Exception as e:
            logger.error(f"Failed to get top shared posts: {e}")
            return []


share_service = ShareService()
