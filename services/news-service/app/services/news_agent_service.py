"""新闻运营助手 Agent 服务 - AI 辅助写作/审核/运营"""
import logging
import os
import httpx
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8004")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("NEWS_LLM_MODEL", "deepseek-chat")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "internal-api-key-change-in-production")

TITLE_SYSTEM_PROMPT = """你是一位专业的法律新闻编辑，擅长撰写吸引人的新闻标题。
要求：
1. 标题简洁有力，20字以内最佳
2. 突出法律要点和社会影响
3. 避免标题党和夸张表述
4. 符合法律新闻的专业性
请根据新闻内容生成3个备选标题，用JSON数组格式返回。"""

SUMMARY_SYSTEM_PROMPT = """你是一位专业的法律新闻摘要编辑。
要求：
1. 摘要100-200字，提炼核心信息
2. 包含关键法律事实、涉及法条、社会影响
3. 语言客观准确，避免主观评价
4. 适合作为新闻列表页的预览文字
请直接输出摘要文本。"""

CATEGORY_SYSTEM_PROMPT = """你是一位法律新闻分类专家。
可选分类：民事纠纷、刑事犯罪、行政法律、知识产权、劳动争议、合同纠纷、房产纠纷、婚姻家庭、交通事故、消费维权、公司法务、环境法律、其他
请根据新闻内容推荐最合适的分类，用JSON格式返回：{"category": "分类名", "confidence": 0.95, "reason": "推荐理由"}"""

TAG_SYSTEM_PROMPT = """你是一位法律新闻标签专家。
请根据新闻内容推荐3-5个标签，标签应涵盖：
- 涉及的法律领域
- 案件类型
- 关键法律概念
- 社会关注点
用JSON数组格式返回：[{"tag": "标签名", "relevance": 0.9}]"""

REVIEW_SYSTEM_PROMPT = """你是一位法律新闻审核专家，负责审核新闻内容质量。
请从以下维度审核并打分(1-10)：
1. 内容准确性：法律事实是否准确
2. 专业性：法律术语使用是否规范
3. 客观性：是否存在主观偏见
4. 可读性：普通读者是否容易理解
5. 合规性：是否涉及敏感信息或不当表述
6. 完整性：信息是否完整，有无遗漏关键点

用JSON格式返回审核结果：
{
  "scores": {"准确性": 8, "专业性": 9, ...},
  "total_score": 45,
  "max_score": 60,
  "passed": true,
  "issues": ["问题描述1", "问题描述2"],
  "suggestions": ["改进建议1", "改进建议2"],
  "summary": "总体评价"
}"""

WRITING_ASSIST_PROMPT = """你是一位法律新闻写作助手。
根据用户提供的信息，帮助撰写法律新闻稿件。
要求：
1. 结构清晰：标题→导语→正文→结语
2. 法律事实准确，引用法条规范
3. 语言客观中立，避免主观判断
4. 适合普通读者阅读理解
请直接输出完整的新闻稿件。"""

OPERATIONS_SUGGESTION_PROMPT = """你是一位新闻运营策略专家。
根据提供的新闻数据和运营指标，给出运营建议。
请分析：
1. 内容策略建议
2. 发布时间建议
3. 标题优化建议
4. 标签和分类优化
5. 推广策略建议
用JSON格式返回建议列表。"""


class NewsAgentService:
    """新闻运营助手 Agent"""

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

    async def generate_titles(self, content: str, original_title: Optional[str] = None) -> Dict[str, Any]:
        user_msg = f"新闻内容：\n{content[:3000]}"
        if original_title:
            user_msg = f"原标题：{original_title}\n\n新闻内容：\n{content[:3000]}"

        messages = [
            {"role": "system", "content": TITLE_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.8, max_tokens=500)
        return {"suggestions": result, "original_title": original_title}

    async def generate_summary(self, content: str, title: Optional[str] = None) -> Dict[str, Any]:
        user_msg = ""
        if title:
            user_msg = f"标题：{title}\n\n"
        user_msg += f"新闻内容：\n{content[:4000]}"

        messages = [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.5, max_tokens=500)
        return {"summary": result}

    async def recommend_category(self, content: str, title: Optional[str] = None) -> Dict[str, Any]:
        user_msg = ""
        if title:
            user_msg = f"标题：{title}\n\n"
        user_msg += f"新闻内容：\n{content[:3000]}"

        messages = [
            {"role": "system", "content": CATEGORY_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.3, max_tokens=300)
        return {"recommendation": result}

    async def recommend_tags(self, content: str, title: Optional[str] = None) -> Dict[str, Any]:
        user_msg = ""
        if title:
            user_msg = f"标题：{title}\n\n"
        user_msg += f"新闻内容：\n{content[:3000]}"

        messages = [
            {"role": "system", "content": TAG_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.4, max_tokens=500)
        return {"tags": result}

    async def review_content(self, content: str, title: Optional[str] = None) -> Dict[str, Any]:
        user_msg = ""
        if title:
            user_msg = f"标题：{title}\n\n"
        user_msg += f"新闻内容：\n{content[:4000]}"

        messages = [
            {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.3, max_tokens=1000)
        return {"review": result}

    async def assist_writing(
        self,
        topic: str,
        key_points: Optional[List[str]] = None,
        style: Optional[str] = None,
        reference_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        user_msg = f"主题：{topic}\n"
        if key_points:
            user_msg += f"要点：{'、'.join(key_points)}\n"
        if style:
            user_msg += f"风格要求：{style}\n"
        if reference_content:
            user_msg += f"参考内容：\n{reference_content[:2000]}\n"

        messages = [
            {"role": "system", "content": WRITING_ASSIST_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.7, max_tokens=3000)
        return {"draft": result}

    async def operations_suggestions(self, stats_data: Dict[str, Any]) -> Dict[str, Any]:
        import json
        user_msg = f"运营数据：\n{json.dumps(stats_data, ensure_ascii=False, indent=2)}"

        messages = [
            {"role": "system", "content": OPERATIONS_SUGGESTION_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.6, max_tokens=1500)
        return {"suggestions": result}

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


news_agent_service = NewsAgentService()
