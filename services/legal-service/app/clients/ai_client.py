"""AI 服务客户端 - 调用外部 AI Service API"""
import os
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class AIServiceClient:
    """AI 服务 HTTP 客户端"""

    def __init__(self):
        self.ai_service_url = os.getenv("AI_SERVICE_URL", "http://localhost:8005")
        self.api_base = f"{self.ai_service_url}/api/v1"
        self._client: Optional[httpx.AsyncClient] = None
        self._enabled = os.getenv("AI_SERVICE_ENABLED", "false").lower() in {"1", "true", "yes"}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def analyze_consultation(
        self,
        consultation_id: int,
        category: str,
        title: str,
        description: str,
        user_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """分析咨询内容，提取关键信息和建议"""
        if not self._enabled:
            logger.info("AI service disabled, skipping consultation analysis")
            return None

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.api_base}/analyze/consultation",
                json={
                    "consultation_id": consultation_id,
                    "category": category,
                    "title": title,
                    "description": description,
                    "user_id": user_id,
                },
            )
            if response.status_code == 200:
                return response.json()
            logger.warning(f"AI service returned status {response.status_code}: {response.text}")
            return None
        except Exception as e:
            logger.error(f"Failed to analyze consultation: {e}")
            return None


ai_service_client = AIServiceClient()