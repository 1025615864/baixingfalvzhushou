"""Backend RAG 客户端 - 从 backend 知识库检索"""
import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class BackendRAGClient:
    """Backend 知识库 RAG 客户端"""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.getenv("BACKEND_API_URL", "http://localhost:8080")
        self.api_key = api_key or os.getenv("BACKEND_API_KEY", "")
        self.timeout = 30.0

    async def query(self, question: str, top_k: int = 5) -> dict:
        """查询 backend 知识库

        Args:
            question: 查询问题
            top_k: 返回数量

        Returns:
            检索结果 {
                "question": str,
                "context": str,
                "retrieved_documents": int,
                "sources": list[dict]
            }
        """
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/knowledge/rag/query",
                    params={"question": question, "top_k": top_k},
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError:
            logger.warning(f"无法连接到 backend: {self.base_url}")
            return {"context": "", "retrieved_documents": 0, "sources": []}
        except httpx.TimeoutException:
            logger.warning("Backend RAG 查询超时")
            return {"context": "", "retrieved_documents": 0, "sources": []}
        except Exception as e:
            logger.error(f"Backend RAG 查询失败: {e}")
            return {"context": "", "retrieved_documents": 0, "sources": []}

    async def health_check(self) -> bool:
        """检查 backend 是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/health"
                )
                return response.status_code == 200
        except Exception:
            logger.error("Failed to check backend RAG health")
            return False


backend_rag_client = BackendRAGClient()


async def query_backend_knowledge(question: str, top_k: int = 5) -> dict:
    """便捷函数：查询 backend 知识库"""
    return await backend_rag_client.query(question=question, top_k=top_k)