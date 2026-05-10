import logging
from typing import List, Dict, Optional

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class MicroserviceClient:
    def __init__(self):
        settings = get_settings()
        self._legal_url = settings.legal_service_url
        self._news_url = settings.news_service_url
        self._community_url = settings.community_service_url
        self._timeout = settings.http_timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def fetch_lawyers(self, user_id: int, limit: int = 10) -> List[Dict]:
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self._legal_url}/api/v1/lawyers/recommend",
                params={"user_id": user_id, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Failed to fetch lawyers from legal service: {e}")
            return []

    async def fetch_news(self, user_id: int, limit: int = 10) -> List[Dict]:
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self._news_url}/api/v1/news/recommend",
                params={"user_id": user_id, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Failed to fetch news from news service: {e}")
            return []

    async def fetch_posts(self, user_id: int, limit: int = 10) -> List[Dict]:
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self._community_url}/api/v1/posts/recommend",
                params={"user_id": user_id, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Failed to fetch posts from community service: {e}")
            return []

    async def fetch_knowledge(self, user_id: int, limit: int = 10) -> List[Dict]:
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self._legal_url}/api/v1/knowledge/recommend",
                params={"user_id": user_id, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Failed to fetch knowledge from legal service: {e}")
            return []


microservice_client = MicroserviceClient()
