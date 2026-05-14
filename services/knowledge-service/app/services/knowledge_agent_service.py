"""知识库运营助手 Agent 服务 - AI 辅助质量评估/关联推荐/关键词提取/分类建议"""
import logging
import os
import httpx
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8004")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("KNOWLEDGE_LLM_MODEL", "deepseek-chat")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "internal-api-key-change-in-production")

QUALITY_EVALUATION_PROMPT = """你是一位法律知识质量评估专家，负责对法律知识条目进行专业质量评估。
请从以下维度进行评分（每项1-10分）并给出改进建议：

1. 准确性：法律事实、法条引用是否准确无误
2. 完整性：内容是否涵盖该法律主题的关键要点，有无重要遗漏
3. 可读性：语言是否清晰易懂，结构是否合理，普通读者能否理解
4. 整体质量：综合评价该知识条目的整体价值

用JSON格式返回评估结果：
{
  "scores": {
    "准确性": 8,
    "完整性": 7,
    "可读性": 9,
    "整体质量": 8
  },
  "total_score": 32,
  "max_score": 40,
  "level": "优秀/良好/一般/需改进",
  "improvements": [
    {"dimension": "准确性", "suggestion": "具体改进建议"},
    {"dimension": "完整性", "suggestion": "具体改进建议"}
  ],
  "summary": "总体评价"
}"""

RELATED_RECOMMENDATION_PROMPT = """你是一位法律知识关联分析专家，负责发现法律知识条目之间的关联关系。
请根据提供的知识条目标题和内容，分析并推荐可能相关的法律知识领域和主题。

要求：
1. 识别该知识条目涉及的核心法律领域
2. 推荐可能相关的其他法律知识主题
3. 说明关联理由和关联类型

关联类型包括：法条关联、案例关联、概念关联、程序关联、领域关联

用JSON格式返回推荐结果：
{
  "core_areas": ["核心法律领域1", "核心法律领域2"],
  "recommendations": [
    {
      "related_topic": "相关知识主题",
      "relation_type": "关联类型",
      "reason": "关联理由",
      "relevance": 0.9
    }
  ]
}"""

KEYWORD_EXTRACTION_PROMPT = """你是一位法律关键词提取专家，擅长从法律知识内容中提取专业关键词。
请从提供的法律知识条目中提取关键词，要求：

1. 包含法律专业术语（如法条名称、法律概念）
2. 包含案件类型关键词
3. 包含适用场景关键词
4. 关键词应具有检索价值，便于知识库搜索
5. 提取5-10个关键词

用JSON格式返回关键词：
{
  "keywords": [
    {"keyword": "关键词", "category": "法律术语/案件类型/适用场景/法律概念", "weight": 0.9}
  ],
  "keyword_string": "关键词1,关键词2,关键词3"
}"""

CATEGORY_SUGGESTION_PROMPT = """你是一位法律知识分类专家，负责为法律知识条目推荐最合适的分类。
可选分类包括但不限于：
- 民法典（总则、物权、合同、人格权、婚姻家庭、继承、侵权责任）
- 刑法（总则、分则）
- 行政法
- 商法（公司法、证券法、保险法、票据法）
- 知识产权法（著作权、专利、商标）
- 劳动法与社会保障法
- 诉讼法（民事诉讼、刑事诉讼、行政诉讼）
- 环境与资源保护法
- 房产与建设法
- 消费者权益保护法
- 交通事故法
- 其他

请根据知识条目的标题和内容，推荐最合适的分类，用JSON格式返回：
{
  "primary_category": "主分类",
  "sub_category": "子分类",
  "confidence": 0.95,
  "alternative_categories": [
    {"category": "备选分类", "sub_category": "备选子分类", "confidence": 0.8, "reason": "备选理由"}
  ],
  "reason": "分类理由"
}"""


class KnowledgeAgentService:
    """知识库运营助手 Agent"""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def _call_ai_service(self, messages: list, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        client = await self._get_client()
        try:
            resp = await client.post(
                f"{AI_SERVICE_URL}/api/v1/ai/chat",
                json={
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                headers={"X-Internal-API-Key": INTERNAL_API_KEY},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("content", data.get("response", ""))
        except Exception as e:
            logger.warning(f"AI service call failed, falling back to direct LLM: {e}")

        return await self._call_llm_direct(messages, temperature, max_tokens)

    async def _call_llm_direct(self, messages: list, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        if not OPENAI_API_KEY:
            return '{"error": "LLM API key not configured"}'

        client = await self._get_client()
        try:
            resp = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                json={
                    "model": LLM_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            logger.error(f"LLM direct call failed: {resp.status_code} {resp.text}")
            return f'{{"error": "LLM call failed with status {resp.status_code}"}}'
        except Exception as e:
            logger.error(f"LLM direct call exception: {e}")
            return f'{{"error": "{str(e)}"}}'

    async def evaluate_quality(self, title: str, content: str) -> Dict[str, Any]:
        user_msg = f"标题：{title}\n\n内容：\n{content[:4000]}"
        messages = [
            {"role": "system", "content": QUALITY_EVALUATION_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.3, max_tokens=1500)
        return {"evaluation": result}

    async def recommend_related(self, knowledge_id: int, title: str, content: str) -> Dict[str, Any]:
        user_msg = f"知识条目ID：{knowledge_id}\n标题：{title}\n\n内容：\n{content[:3000]}"
        messages = [
            {"role": "system", "content": RELATED_RECOMMENDATION_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.4, max_tokens=1500)
        return {"recommendations": result, "knowledge_id": knowledge_id}

    async def generate_keywords(self, title: str, content: str) -> Dict[str, Any]:
        user_msg = f"标题：{title}\n\n内容：\n{content[:3000]}"
        messages = [
            {"role": "system", "content": KEYWORD_EXTRACTION_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.3, max_tokens=800)
        return {"keywords": result}

    async def suggest_category(self, title: str, content: str) -> Dict[str, Any]:
        user_msg = f"标题：{title}\n\n内容：\n{content[:3000]}"
        messages = [
            {"role": "system", "content": CATEGORY_SUGGESTION_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.3, max_tokens=800)
        return {"suggestion": result}

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


knowledge_agent_service = KnowledgeAgentService()
