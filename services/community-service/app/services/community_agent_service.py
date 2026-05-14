"""社区运营助手 Agent 服务 - AI 辅助内容审核/热点发现/用户画像/摘要生成"""
import logging
import os
import httpx
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8004")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("COMMUNITY_LLM_MODEL", "deepseek-chat")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "internal-api-key-change-in-production")

MODERATE_SYSTEM_PROMPT = """你是一位专业的社区内容审核专家，负责对社区帖子进行智能审核。
请从以下维度检测违规内容：
1. 涉黄：色情、低俗、暗示性内容
2. 涉暴：暴力、恐怖、血腥内容
3. 涉政：敏感政治话题、不当政治言论
4. 广告：垃圾广告、营销推广、引流信息
5. 辱骂：人身攻击、侮辱性语言、歧视言论
6. 诈骗：虚假信息、诈骗内容、误导性信息
7. 侵权：侵犯他人隐私、泄露个人信息
8. 其他违规：违反社区规范的其他内容

用JSON格式返回审核结果：
{
  "is_violation": true/false,
  "violation_types": ["违规类型1", "违规类型2"],
  "confidence": 0.95,
  "details": [
    {"type": "违规类型", "description": "具体描述", "severity": "high/medium/low", "location": "违规内容位置"}
  ],
  "risk_level": "high/medium/low",
  "summary": "审核总结"
}"""

TRENDING_SYSTEM_PROMPT = """你是一位社区运营数据分析专家，擅长从社区互动数据中发现热点话题。
请根据提供的帖子互动数据，分析并识别热点话题：
1. 识别互动量异常高的帖子及其共同主题
2. 发现新兴话题趋势
3. 分析用户关注焦点
4. 评估话题热度和传播潜力

用JSON格式返回热点发现结果：
{
  "trending_topics": [
    {
      "topic": "话题名称",
      "heat_score": 95,
      "post_count": 10,
      "total_interactions": 5000,
      "trend": "rising/stable/declining",
      "keywords": ["关键词1", "关键词2"],
      "summary": "话题概述"
    }
  ],
  "emerging_topics": [
    {
      "topic": "新兴话题",
      "potential_score": 80,
      "reason": "潜力原因"
    }
  ],
  "overall_analysis": "整体社区热点趋势分析"
}"""

USER_PROFILE_SYSTEM_PROMPT = """你是一位社区用户行为分析专家，擅长构建用户画像。
请根据用户的行为数据，进行深度画像分析：
1. 活跃度分析：发帖频率、评论频率、互动频率
2. 兴趣领域：关注的法律领域和话题偏好
3. 内容偏好：偏好的内容类型和风格
4. 社交特征：互动模式、影响力
5. 价值评估：对社区的贡献度

用JSON格式返回用户画像：
{
  "activity_level": "high/medium/low",
  "activity_score": 85,
  "interests": [
    {"domain": "法律领域", "weight": 0.9, "evidence": "依据"}
  ],
  "content_preference": {
    "preferred_types": ["提问", "分享"],
    "preferred_length": "long/medium/short",
    "writing_style": "专业/通俗"
  },
  "social_profile": {
    "influence_score": 75,
    "interaction_pattern": "主动型/被动型",
    "community_role": "意见领袖/活跃用户/潜水者"
  },
  "contribution": {
    "quality_score": 80,
    "helpfulness": 85,
    "expertise_areas": ["劳动法", "合同纠纷"]
  },
  "recommended_tags": ["标签1", "标签2", "标签3"],
  "summary": "用户画像总结"
}"""

SUMMARY_SYSTEM_PROMPT = """你是一位社区内容摘要专家，擅长为长篇帖子生成精炼摘要。
要求：
1. 摘要150-300字，提炼核心观点和关键信息
2. 保留法律要点和关键事实
3. 语言简洁客观，便于快速浏览
4. 如果帖子包含问题，摘要中应体现核心问题
5. 如果帖子包含解答，摘要中应体现关键建议

请直接输出摘要文本。"""

MODERATION_ACTION_SYSTEM_PROMPT = """你是一位社区审核处理专家，根据违规类型和严重程度建议审核操作。
可选操作：
- 通过：内容无违规，正常展示
- 警告：轻微违规，提醒作者修改
- 编辑：自动替换敏感词或删除违规片段
- 隐藏：中等违规，内容不公开展示
- 删除：严重违规，删除内容
- 封禁用户：极端违规，临时或永久封禁账号

请根据违规类型和上下文，给出处理建议：

用JSON格式返回建议：
{
  "action": "推荐操作",
  "action_level": "none/warning/edit/hide/delete/ban",
  "reason": "处理原因",
  "duration": "封禁时长（如适用）",
  "notification_template": "通知用户的消息模板",
  "appeal_suggestion": "申诉建议",
  "alternative_actions": [
    {"action": "备选操作", "reason": "适用场景"}
  ]
}"""


class CommunityAgentService:
    """社区运营助手 Agent"""

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

    async def moderate_content(self, content: str, title: Optional[str] = None) -> Dict[str, Any]:
        user_msg = ""
        if title:
            user_msg = f"标题：{title}\n\n"
        user_msg += f"帖子内容：\n{content[:4000]}"

        messages = [
            {"role": "system", "content": MODERATE_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.2, max_tokens=1500)
        return {"moderation": result}

    async def discover_trending(self, posts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        import json
        user_msg = f"社区帖子互动数据：\n{json.dumps(posts_data, ensure_ascii=False, indent=2)[:8000]}"

        messages = [
            {"role": "system", "content": TRENDING_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.5, max_tokens=2000)
        return {"trending": result}

    async def analyze_user_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        import json
        user_msg = f"用户行为数据：\n{json.dumps(user_data, ensure_ascii=False, indent=2)[:6000]}"

        messages = [
            {"role": "system", "content": USER_PROFILE_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.4, max_tokens=2000)
        return {"profile": result}

    async def generate_summary(self, content: str, title: Optional[str] = None) -> Dict[str, Any]:
        user_msg = ""
        if title:
            user_msg = f"标题：{title}\n\n"
        user_msg += f"帖子内容：\n{content[:4000]}"

        messages = [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.5, max_tokens=500)
        return {"summary": result}

    async def suggest_moderation_action(self, content: str, violation_type: str) -> Dict[str, Any]:
        user_msg = f"违规类型：{violation_type}\n\n帖子内容：\n{content[:3000]}"

        messages = [
            {"role": "system", "content": MODERATION_ACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.3, max_tokens=1000)
        return {"suggestion": result}

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


community_agent_service = CommunityAgentService()
