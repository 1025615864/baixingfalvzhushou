import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config.settings import settings
from app.services.search_service import SearchItem

logger = logging.getLogger(__name__)


class MicroserviceClient:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._timeout = 10.0

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                follow_redirects=True,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _fetch(
        self,
        base_url: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict]:
        client = await self._get_client()
        try:
            response = await client.get(f"{base_url}{path}", params=params or {})
            if response.status_code == 200:
                return response.json()
            logger.warning(
                f"Service at {base_url}{path} returned status {response.status_code}"
            )
            return None
        except httpx.TimeoutException:
            logger.warning(f"Timeout calling {base_url}{path}")
            return None
        except httpx.ConnectError:
            logger.warning(f"Connection error calling {base_url}{path}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling {base_url}{path}: {e}")
            return None

    async def search_posts(
        self, query: str, limit: int = 10
    ) -> List[SearchItem]:
        data = await self._fetch(
            settings.COMMUNITY_SERVICE_URL,
            "/api/v1/posts/search",
            {"query": query, "limit": limit},
        )
        if not data:
            return []
        return self._parse_items(data, "post", "/forum")

    async def search_lawyers(
        self, query: str, limit: int = 10
    ) -> List[SearchItem]:
        data = await self._fetch(
            settings.LEGAL_SERVICE_URL,
            "/api/v1/lawyers/search",
            {"query": query, "limit": limit},
        )
        if not data:
            return []
        return self._parse_items(data, "lawyer", "/lawyer")

    async def search_news(
        self, query: str, limit: int = 10
    ) -> List[SearchItem]:
        data = await self._fetch(
            settings.NEWS_SERVICE_URL,
            "/api/v1/news/search",
            {"query": query, "limit": limit},
        )
        if not data:
            return []
        return self._parse_items(data, "news", "/news")

    async def search_knowledge(
        self, query: str, limit: int = 10
    ) -> List[SearchItem]:
        data = await self._fetch(
            settings.KNOWLEDGE_SERVICE_URL,
            "/api/v1/knowledge/search",
            {"query": query, "limit": limit},
        )
        if not data:
            return []
        return self._parse_items(data, "knowledge", "/knowledge")

    def _parse_items(
        self,
        data: Dict,
        item_type: str,
        url_prefix: str,
    ) -> List[SearchItem]:
        items: List[SearchItem] = []
        results = data.get("items", data.get("data", []))
        if isinstance(results, list):
            for item in results[:20]:
                if isinstance(item, dict):
                    items.append(
                        SearchItem(
                            id=item.get("id", 0),
                            type=item_type,
                            title=item.get("title", ""),
                            description=item.get("description", item.get("content", ""))[:200],
                            url=item.get("url", f"{url_prefix}/{item.get('id', 0)}"),
                            score=item.get("score", 0.8),
                        )
                    )
        return items


client_service = MicroserviceClient()
