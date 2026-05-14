"""法律运营助手 Agent 服务 - AI 辅助律师匹配/咨询分析/风险识别/回复建议/推荐优化"""
import logging
import os
import httpx
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8004")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LEGAL_LLM_MODEL", "deepseek-chat")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "internal-api-key-change-in-production")

MATCH_LAWYER_PROMPT = """你是一位专业的法律咨询智能匹配专家，擅长根据咨询内容推荐最合适的律师。
请分析用户的咨询内容，结合咨询类别，推荐最匹配的律师专业方向和律师应具备的特质。

要求：
1. 准确识别咨询涉及的法律领域和细分方向
2. 分析案件复杂程度，推荐对应资历的律师
3. 考虑地域因素（如咨询者所在城市）
4. 给出匹配理由和专业建议

用JSON格式返回：
{
  "legal_fields": ["涉及的法律领域1", "法律领域2"],
  "complexity": "简单/一般/复杂/重大",
  "required_specialties": ["律师应具备的专业方向1", "专业方向2"],
  "required_experience": "建议律师资历（如：3年以上/资深律师）",
  "preferred_city": "建议律师所在城市（如有）",
  "match_reason": "匹配理由说明",
  "suggested_lawyer_traits": ["律师应具备的特质1", "特质2"],
  "urgency": "低/中/高/紧急",
  "estimated_sessions": "预计需要咨询次数"
}"""

CONSULTATION_SUMMARY_PROMPT = """你是一位专业的法律咨询分析师，擅长从咨询内容中提取关键法律信息和事实要点。
请对用户的法律咨询内容进行结构化摘要，提取关键法律点和核心事实。

要求：
1. 提取核心法律事实，去除冗余信息
2. 识别涉及的法律关系和主体
3. 标注关键时间节点和证据线索
4. 提炼核心法律争议点
5. 语言客观准确，使用规范法律术语

用JSON格式返回：
{
  "core_facts": ["核心事实1", "核心事实2"],
  "legal_relationships": ["法律关系1", "法律关系2"],
  "key_parties": [{"role": "角色", "description": "描述"}],
  "timeline": [{"time": "时间节点", "event": "事件"}],
  "legal_issues": ["法律争议点1", "法律争议点2"],
  "evidence_hints": ["证据线索1", "证据线索2"],
  "summary": "100字以内的整体摘要"
}"""

LEGAL_RISK_PROMPT = """你是一位资深的法律风险评估专家，擅长识别法律咨询中的潜在风险点。
请对用户的法律咨询内容进行全面的风险分析，识别各类潜在法律风险。

要求：
1. 识别诉讼风险、时效风险、证据风险等
2. 评估各风险的发生概率和影响程度
3. 提供风险规避或降低的建议
4. 提醒可能的法律后果
5. 按风险等级排序

用JSON格式返回：
{
  "risks": [
    {
      "type": "风险类型（诉讼/时效/证据/程序/合规/执行）",
      "description": "风险描述",
      "probability": "低/中/高",
      "impact": "轻微/一般/严重/重大",
      "level": "低/中/高/极高",
      "suggestion": "风险规避建议"
    }
  ],
  "overall_risk_level": "低/中/高/极高",
  "key_warnings": ["重要警示1", "重要警示2"],
  "statute_of_limitations": "时效提醒（如适用）",
  "immediate_actions": ["建议立即采取的行动1", "行动2"]
}"""

SUGGEST_RESPONSE_PROMPT = """你是一位经验丰富的法律回复顾问，擅长为律师撰写专业的咨询回复提供建议。
请根据用户的咨询内容和类别，为律师提供回复建议框架和要点。

要求：
1. 回复应专业、准确、有温度
2. 先安抚情绪，再分析法律问题
3. 明确告知法律权利和救济途径
4. 提供可操作的法律建议
5. 提醒重要注意事项和风险
6. 建议后续步骤和时间安排

用JSON格式返回：
{
  "opening": "开场白建议（安抚+共情）",
  "legal_analysis": ["法律分析要点1", "要点2"],
  "rights_and_remedies": ["可主张的权利1", "救济途径2"],
  "actionable_advice": ["具体操作建议1", "建议2"],
  "risk_warnings": ["风险提醒1", "提醒2"],
  "next_steps": ["后续步骤1", "步骤2"],
  "closing": "结语建议",
  "estimated_cost": "预估费用范围（如适用）",
  "recommended_documents": ["建议准备的材料1", "材料2"]
}"""

OPTIMIZE_RECOMMENDATION_PROMPT = """你是一位法律服务平台运营策略专家，擅长基于历史匹配数据优化律师推荐策略。
请分析提供的历史匹配数据，给出推荐策略优化建议。

要求：
1. 分析匹配成功率和用户满意度趋势
2. 识别匹配效率低下的领域和原因
3. 提出推荐算法优化方向
4. 建议律师资源调配策略
5. 给出可量化的优化目标

用JSON格式返回：
{
  "analysis": {
    "success_rate_trend": "成功率趋势分析",
    "satisfaction_trend": "满意度趋势分析",
    "bottleneck_areas": ["瓶颈领域1", "瓶颈领域2"]
  },
  "optimization_suggestions": [
    {
      "area": "优化方向",
      "suggestion": "具体建议",
      "expected_improvement": "预期提升",
      "priority": "高/中/低"
    }
  ],
  "resource_allocation": {
    "undersupplied_fields": ["律师不足的领域1", "领域2"],
    "oversupplied_fields": ["律师过剩的领域1", "领域2"],
    "suggested_reallocation": "调配建议"
  },
  "quantitative_targets": [
    {"metric": "指标名", "current": "当前值", "target": "目标值", "timeframe": "达成时间"}
  ]
}"""


class LegalAgentService:
    """法律运营助手 Agent"""

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

    async def match_lawyer(self, consultation_content: str, category: str) -> Dict[str, Any]:
        user_msg = f"咨询类别：{category}\n\n咨询内容：\n{consultation_content[:3000]}"
        messages = [
            {"role": "system", "content": MATCH_LAWYER_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.4, max_tokens=1500)
        return {"match_analysis": result, "category": category}

    async def generate_consultation_summary(self, content: str) -> Dict[str, Any]:
        user_msg = f"咨询内容：\n{content[:4000]}"
        messages = [
            {"role": "system", "content": CONSULTATION_SUMMARY_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.3, max_tokens=2000)
        return {"summary": result}

    async def analyze_legal_risk(self, content: str) -> Dict[str, Any]:
        user_msg = f"咨询内容：\n{content[:4000]}"
        messages = [
            {"role": "system", "content": LEGAL_RISK_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.3, max_tokens=2000)
        return {"risk_analysis": result}

    async def suggest_response(self, consultation_content: str, category: str) -> Dict[str, Any]:
        user_msg = f"咨询类别：{category}\n\n咨询内容：\n{consultation_content[:3000]}"
        messages = [
            {"role": "system", "content": SUGGEST_RESPONSE_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.5, max_tokens=2000)
        return {"response_suggestion": result, "category": category}

    async def optimize_recommendation(self, history_data: Dict[str, Any]) -> Dict[str, Any]:
        import json
        user_msg = f"历史匹配数据：\n{json.dumps(history_data, ensure_ascii=False, indent=2)}"
        messages = [
            {"role": "system", "content": OPTIMIZE_RECOMMENDATION_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        result = await self._call_ai_service(messages, temperature=0.5, max_tokens=2000)
        return {"optimization": result}

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


legal_agent_service = LegalAgentService()
