"""AI 服务客户端 - 内容审核"""
import os
import logging
from typing import Optional
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


@dataclass
class AIAnalysisResult:
    confidence: float
    reason: str
    category: str = "general"


class AIClient:
    def __init__(self):
        self.base_url = os.getenv("AI_SERVICE_URL", "http://localhost:8005")
        self.timeout = 5.0

    async def analyze_content(self, content: str) -> AIAnalysisResult:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(
                    "/api/v1/ai/analyze",
                    json={"content": content}
                )
                if response.status_code == 200:
                    data = response.json()
                    return AIAnalysisResult(
                        confidence=data.get("confidence", 0.0),
                        reason=data.get("reason", ""),
                        category=data.get("category", "general")
                    )
                else:
                    logger.warning(f"AI service returned {response.status_code}")
                    return AIAnalysisResult(confidence=0.0, reason="AI服务不可用")
        except Exception as e:
            logger.error(f"Failed to call AI service: {e}")
            return AIAnalysisResult(confidence=0.0, reason="AI服务调用失败")

    async def check_legal_advice(self, content: str) -> dict:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(
                    "/api/v1/ai/check-legal-advice",
                    json={"content": content}
                )
                if response.status_code == 200:
                    return response.json()
                return {"is_legal": True, "warnings": []}
        except Exception as e:
            logger.error(f"Failed to check legal advice: {e}")
            return {"is_legal": True, "warnings": ["AI服务不可用"]}


ai_client = AIClient()
