"""档案库服务HTTP客户端 - AI服务使用"""
import os
import logging
from typing import Optional, List
import httpx

logger = logging.getLogger(__name__)

ARCHIVE_SERVICE_URL = os.getenv("ARCHIVE_SERVICE_URL", "http://localhost:8082")
ARCHIVE_SERVICE_API_KEY = os.getenv("ARCHIVE_SERVICE_API_KEY", "")


class ArchiveServiceClient:
    """档案库服务HTTP客户端 - 用于AI服务的RAG检索"""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or ARCHIVE_SERVICE_URL
        self.api_key = api_key or ARCHIVE_SERVICE_API_KEY
        self.timeout = 30.0

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def search_vector(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        case_type: Optional[str] = None
    ) -> List[dict]:
        """向量搜索档案库

        Returns:
            List[dict]: 检索结果列表，每项包含 id, text, metadata, distance
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/cases/vector/search",
                    json={
                        "query": query,
                        "top_k": top_k,
                        "category": category,
                        "case_type": case_type
                    },
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
        except httpx.ConnectError:
            logger.warning(f"无法连接到档案库服务: {self.base_url}")
            return []
        except httpx.TimeoutException:
            logger.warning("档案库向量搜索超时")
            return []
        except Exception as e:
            logger.error(f"档案库向量搜索失败: {e}")
            return []

    async def search_fulltext(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        status: str = "published"
    ) -> List[dict]:
        """全文搜索档案库"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/search",
                    params={
                        "q": query,
                        "category": category,
                        "page_size": top_k
                    },
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                items = data.get("items", [])
                return [
                    {
                        "id": str(item["id"]),
                        "text": item.get("facts", item.get("content", "")),
                        "metadata": {
                            "title": item.get("title"),
                            "category": item.get("category"),
                            "case_type": item.get("case_type"),
                            "court": item.get("court"),
                            "judgment_result": item.get("judgment_result")
                        },
                        "distance": 0.0
                    }
                    for item in items
                ]
        except httpx.ConnectError:
            logger.warning(f"无法连接到档案库服务: {self.base_url}")
            return []
        except httpx.TimeoutException:
            logger.warning("档案库全文搜索超时")
            return []
        except Exception as e:
            logger.error(f"档案库全文搜索失败: {e}")
            return []

    async def get_recommendations(
        self,
        case_id: int,
        top_k: int = 5
    ) -> List[dict]:
        """获取相关案例推荐"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/recommendations/{case_id}",
                    params={"top_k": top_k},
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json().get("recommendations", [])
        except Exception as e:
            logger.error(f"获取案例推荐失败: {e}")
            return []

    async def health_check(self) -> bool:
        """检查档案库服务是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False

    async def get_stats(self) -> dict:
        """获取档案库统计信息"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/stats/summary",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"获取档案库统计失败: {e}")
            return {}


_archive_client: Optional[ArchiveServiceClient] = None


def get_archive_client() -> ArchiveServiceClient:
    global _archive_client
    if _archive_client is None:
        _archive_client = ArchiveServiceClient()
    return _archive_client


async def search_archive_vector(query: str, top_k: int = 5) -> List[dict]:
    """便捷函数：搜索档案库向量"""
    return await get_archive_client().search_vector(query=query, top_k=top_k)


async def search_archive_fulltext(query: str, top_k: int = 5) -> List[dict]:
    """便捷函数：全文搜索档案库"""
    return await get_archive_client().search_fulltext(query=query, top_k=top_k)
