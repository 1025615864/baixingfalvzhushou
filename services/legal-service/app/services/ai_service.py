"""AI 增强服务 - 为法律服务提供 AI 摘要/标签功能"""
import os
import logging
from typing import Optional, List, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class AIServiceClient:
    """AI 服务客户端"""

    def __init__(self):
        self.ai_service_url = os.getenv("AI_SERVICE_URL", "http://localhost:8005")
        self.api_base = f"{self.ai_service_url}/api/v1/ai"
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

    async def summarize_consultation(
        self,
        title: str,
        description: str,
        messages: List[Dict[str, str]],
    ) -> Optional[str]:
        """调用 AI 服务生成咨询摘要"""
        if not self._enabled:
            logger.info("AI service disabled, skipping summarization")
            return None

        try:
            client = await self._get_client()

            conversation = f"标题: {title}\n\n问题: {description}\n\n对话:\n"
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conversation += f"{role}: {content}\n"

            prompt = f"""请为以下法律咨询生成一个简洁的摘要（100字以内）：

{conversation}

摘要："""

            response = await client.post(
                f"{self.api_base}/chat",
                json={
                    "message": prompt,
                    "intent": "legal",
                    "user_id": 0,
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content")
            else:
                logger.warning(f"AI summarization failed: {response.status_code}")
                return None

        except Exception as e:
            logger.warning(f"AI summarization error: {e}")
            return None

    async def suggest_category(
        self,
        title: str,
        description: str,
    ) -> Optional[List[str]]:
        """调用 AI 服务建议分类标签"""
        if not self._enabled:
            return None

        try:
            client = await self._get_client()

            prompt = f"""请为以下法律问题推荐合适的专业领域标签（最多3个）：
问题：{title}
详情：{description}

请从以下标签中选择最合适的：
- 婚姻继承
- 劳动纠纷
- 合同纠纷
- 交通事故
- 房产纠纷
- 刑事辩护
- 债务纠纷
- 知识产权
- 公司法务
- 其他

只返回标签列表，用逗号分隔，不要其他文字。"""

            response = await client.post(
                f"{self.api_base}/chat",
                json={
                    "message": prompt,
                    "intent": "legal",
                    "user_id": 0,
                }
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "")
                categories = [c.strip() for c in content.split(",") if c.strip()]
                return categories[:3]
            else:
                return None

        except Exception as e:
            logger.warning(f"AI category suggestion error: {e}")
            return None

    async def extract_keywords(
        self,
        text: str,
    ) -> Optional[List[str]]:
        """从文本中提取关键词"""
        if not self._enabled:
            return None

        try:
            client = await self._get_client()

            prompt = f"""请从以下法律文本中提取5个关键词：
{text}

只返回关键词列表，用逗号分隔，不要其他文字。"""

            response = await client.post(
                f"{self.api_base}/chat",
                json={
                    "message": prompt,
                    "intent": "legal",
                    "user_id": 0,
                }
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "")
                keywords = [k.strip() for k in content.split(",") if k.strip()]
                return keywords[:5]
            else:
                return None

        except Exception as e:
            logger.warning(f"AI keyword extraction error: {e}")
            return None

    async def suggest_lawyer_match(
        self,
        consultation_category: str,
        consultation_description: str,
        available_lawyers: List[Dict[str, Any]],
    ) -> Optional[List[int]]:
        """为咨询匹配最合适的律师 ID 列表"""
        if not self._enabled or not available_lawyers:
            return None

        try:
            client = await self._get_client()

            lawyers_info = "\n".join([
                f"ID:{l.get('id')} 姓名:{l.get('name')} 专业:{l.get('specialties')} 评分:{l.get('rating')}"
                for l in available_lawyers[:10]
            ])

            prompt = f"""根据以下法律咨询内容，从候选律师中选择最合适的3位：

咨询类型：{consultation_category}
问题详情：{consultation_description}

候选律师：
{lawyers_info}

请根据律师的专业领域和评分，选择最合适的3位，只返回他们的ID，用逗号分隔。"""

            response = await client.post(
                f"{self.api_base}/chat",
                json={
                    "message": prompt,
                    "intent": "legal",
                    "user_id": 0,
                }
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "")
                ids = [int(i.strip()) for i in content.split(",") if i.strip().isdigit()]
                return ids[:3]
            else:
                return None

        except Exception as e:
            logger.warning(f"AI lawyer matching error: {e}")
            return None


ai_service_client = AIServiceClient()