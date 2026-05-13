"""知识库服务HTTP客户端 - AI服务使用"""
import os
import logging
from typing import Optional, List
import httpx

logger = logging.getLogger(__name__)

KNOWLEDGE_SERVICE_URL = os.getenv("KNOWLEDGE_SERVICE_URL", "http://localhost:8081")
KNOWLEDGE_SERVICE_API_KEY = os.getenv("KNOWLEDGE_SERVICE_API_KEY", "")


class KnowledgeServiceClient:
    """知识库服务HTTP客户端 - 用于AI服务的RAG检索"""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or KNOWLEDGE_SERVICE_URL
        self.api_key = api_key or KNOWLEDGE_SERVICE_API_KEY
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
        knowledge_type: Optional[str] = None
    ) -> List[dict]:
        """向量搜索知识库

        Returns:
            List[dict]: 检索结果列表，每项包含 id, text, metadata, distance
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/knowledge/vector/search",
                    json={
                        "query": query,
                        "top_k": top_k,
                        "category": category,
                        "knowledge_type": knowledge_type
                    },
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
        except httpx.ConnectError:
            logger.warning(f"无法连接到知识库服务: {self.base_url}")
            return []
        except httpx.TimeoutException:
            logger.warning("知识库向量搜索超时")
            return []
        except Exception as e:
            logger.error(f"知识库向量搜索失败: {e}")
            return []

    async def search_fulltext(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        status: str = "published"
    ) -> List[dict]:
        """全文搜索知识库"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/knowledge/search",
                    params={
                        "q": query,
                        "category": category,
                        "status": status,
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
                        "text": item["content"],
                        "metadata": {
                            "title": item["title"],
                            "category": item.get("category"),
                            "keywords": item.get("keywords"),
                            "source": item.get("source")
                        },
                        "distance": 0.0
                    }
                    for item in items
                ]
        except httpx.ConnectError:
            logger.warning(f"无法连接到知识库服务: {self.base_url}")
            return []
        except httpx.TimeoutException:
            logger.warning("知识库全文搜索超时")
            return []
        except Exception as e:
            logger.error(f"知识库全文搜索失败: {e}")
            return []

    async def health_check(self) -> bool:
        """检查知识库服务是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            logger.error("Failed to check knowledge service health")
            return False

    async def get_stats(self) -> dict:
        """获取知识库统计信息"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/stats/summary",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"获取知识库统计失败: {e}")
            return {}


_knowledge_client: Optional[KnowledgeServiceClient] = None


def get_knowledge_client() -> KnowledgeServiceClient:
    global _knowledge_client
    if _knowledge_client is None:
        _knowledge_client = KnowledgeServiceClient()
    return _knowledge_client


async def search_knowledge_vector(query: str, top_k: int = 5) -> List[dict]:
    """便捷函数：搜索知识库向量"""
    return await get_knowledge_client().search_vector(query=query, top_k=top_k)


async def search_knowledge_fulltext(query: str, top_k: int = 5) -> List[dict]:
    """便捷函数：全文搜索知识库"""
    return await get_knowledge_client().search_fulltext(query=query, top_k=top_k)
