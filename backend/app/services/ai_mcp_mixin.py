"""AI 助手 MCP 工具集成 Mixin"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, AsyncGenerator

from ..services.mcp import (
    get_mcp_manager,
    get_tools_for_prompt,
    execute_tool,
    ToolResult,
)
from .ai_response_strategy import ResponseStrategy

logger = logging.getLogger(__name__)


class AIAssistantMCPMixin:
    """AI 助手 MCP 工具集成 Mixin

    使用方法:
    class AILegalAssistant(AIAssistantMCPMixin, ...):
        ...
    """

    # 工具调用触发词
    TOOL_TRIGGER_WORDS = [
        "计算", "算一下", "帮我算",
        "生成文书", "写起诉状", "写答辩状",
        "找律师", "律所", "律师推荐",
        "查询法条", "搜索法律", "相关法规",
        "预约", "日程", "咨询时间",
    ]

    # 工具调用模式（正则）
    TOOL_PATTERNS = {
        "calculator": [
            r"计算\s*(\d+[\s,]*\d*)\s*元?",  # 计算金额
            r"诉讼时效",  # 时效查询
            r"经济补偿金",  # 补偿计算
            r"误工费",  # 误工费计算
        ],
        "document_generation": [
            r"生成\s*(起诉状|答辩状|和解协议|律师函)",
            r"写\s*(起诉状|答辩状|和解协议|律师函)",
            r"帮我写\s*(文书|法律文书)",
        ],
        "lawfirm_search": [
            r"找\s*(.*)律师",
            r"(.*)律所",
            r"律师推荐",
            r"咨询\s*(.*)律师",
        ],
        "knowledge_search": [
            r"(.*)法条",
            r"(.*)法律规定",
            r"搜索\s*(.*)法律",
            r"相关\s*(.*)法规",
        ],
        "calendar": [
            r"预约\s*(.*)",
            r"咨询\s*(.*)时间",
            r"日程",
        ],
    }

    def get_tool_context(
            self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """获取工具调用上下文"""
        return {
            "user_id": user_id,
            "is_authenticated": user_id is not None,
            "is_vip": getattr(self, "_is_vip", False),
            "is_admin": getattr(self, "_is_admin", False),
        }

    def get_tools_for_system_prompt(self) -> str:
        """获取工具列表用于 system prompt"""
        return get_tools_for_prompt()

    def detect_tool_intent(self, message: str) -> Optional[Dict[str, Any]]:
        """检测是否需要调用工具

        Returns:
            如果需要调用工具，返回 {'tool_name': str, 'params': dict}
            否则返回 None
        """
        message_lower = message.lower()

        # 检查各工具模式
        for tool_name, patterns in self.TOOL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    params = self._extract_tool_params(tool_name, message)
                    return {
                        "tool_name": tool_name,
                        "params": params,
                        "reason": f"匹配到工具触发模式: {pattern}",
                    }

        # 检查触发词
        for word in self.TOOL_TRIGGER_WORDS:
            if word in message:
                params = self._extract_tool_params_by_word(word, message)
                if params:
                    return {
                        "tool_name": self._word_to_tool(word),
                        "params": params,
                        "reason": f"包含触发词: {word}",
                    }

        return None

    def _word_to_tool(self, word: str) -> str:
        """将触发词映射到工具名"""
        mapping = {
            "计算": "calculator",
            "算一下": "calculator",
            "帮我算": "calculator",
            "生成文书": "document_generation",
            "写起诉状": "document_generation",
            "写答辩状": "document_generation",
            "找律师": "lawfirm_search",
            "律所": "lawfirm_search",
            "律师推荐": "lawfirm_search",
            "查询法条": "knowledge_search",
            "搜索法律": "knowledge_search",
            "相关法规": "knowledge_search",
            "预约": "calendar",
            "日程": "calendar",
            "咨询时间": "calendar",
        }
        return mapping.get(word, "calculator")

    def _extract_tool_params(self, tool_name: str,
                             message: str) -> Dict[str, Any]:
        """从消息中提取工具参数"""
        params: Dict[str, Any] = {
            "action": self._get_default_action(tool_name)}

        if tool_name == "calculator":
            # 尝试提取金额
            money_match = re.search(r"(\d+[\s,]*\d*)\s*元", message)
            if money_match:
                amount_str = money_match.group(
                    1).replace(",", "").replace(" ", "")
                try:
                    params["amount"] = float(amount_str)
                except ValueError:
                    pass

            # 确定计算类型
            if "诉讼时效" in message:
                params["calculation_type"] = "limitation"
                date_match = re.search(
                    r"(\d{4}[-年]\d{1,2}[-月]\d{1,2})", message)
                if date_match:
                    params["start_date"] = date_match.group(1).replace(
                        "年", "-").replace("月", "-").replace("日", "")
            elif "经济补偿金" in message:
                params["calculation_type"] = "severance"
            elif "误工费" in message:
                params["calculation_type"] = "missed_work"
            else:
                params["calculation_type"] = "litigation_fee"

        elif tool_name == "document_generation":
            # 提取文书类型
            if "起诉状" in message:
                params["document_type"] = "complaint"
            elif "答辩状" in message:
                params["document_type"] = "defense"
            elif "和解协议" in message:
                params["document_type"] = "agreement"
            elif "律师函" in message:
                params["document_type"] = "letter"
            else:
                params["document_type"] = "complaint"  # 默认

            # 提取案件类型
            case_type_map = {
                "劳动": "labor_dispute",
                "合同": "contract_dispute",
                "婚姻": "marriage_family",
                "离婚": "marriage_family",
                "房产": "property_dispute",
                "消费": "consumer_rights",
                "交通": "traffic_accident",
                "借贷": "loan_dispute",
            }
            for key, value in case_type_map.items():
                if key in message:
                    params["case_type"] = value
                    break

        elif tool_name == "lawfirm_search":
            params["action"] = "recommend"
            # 提取城市
            city_match = re.search(
                r"(北京|上海|广州|深圳|杭州|南京|成都|武汉|西安)\s*(.*?)(律师|律所)", message)
            if city_match:
                params["city"] = city_match.group(1)

            # 提取案件类型用于推荐
            case_type_map = {
                "劳动": "labor_dispute",
                "合同": "contract_dispute",
                "婚姻": "marriage_family",
                "房产": "property_dispute",
                "消费": "consumer_rights",
                "交通": "traffic_accident",
                "借贷": "loan_dispute",
            }
            for key, value in case_type_map.items():
                if key in message:
                    params["case_type"] = value
                    break

        elif tool_name == "knowledge_search":
            # 提取搜索关键词
            keywords = ["法条", "规定", "法律", "法规"]
            for keyword in keywords:
                if keyword in message:
                    parts = message.split(keyword)
                    if len(parts) > 1:
                        query = parts[1].strip()
                        if query:
                            params["query"] = query
                            break
            if "query" not in params:
                params["query"] = message[:50]

        elif tool_name == "calendar":
            if "预约" in message:
                params["action"] = "check_availability"
            elif "日程" in message:
                params["action"] = "list_appointments"

        return params

    def _extract_tool_params_by_word(
            self, word: str, message: str) -> Optional[Dict[str, Any]]:
        """根据触发词提取参数"""
        params = {"action": self._get_default_action(self._word_to_tool(word))}
        return params

    def _get_default_action(self, tool_name: str) -> str:
        """获取工具默认操作"""
        actions = {
            "calculator": "litigation_fee",
            "document_generation": "generate",
            "lawfirm_search": "recommend",
            "knowledge_search": "search",
            "calendar": "check_availability",
        }
        return actions.get(tool_name, "execute")

    async def execute_tool_if_needed(
        self,
        message: str,
        context: Dict[str, Any],
        session_id: str,
    ) -> Optional[ToolResult]:
        """如果检测到工具调用意图，执行工具

        Returns:
            ToolResult 如果执行了工具，否则 None
        """
        tool_intent = self.detect_tool_intent(message)
        if not tool_intent:
            return None

        tool_name = tool_intent["tool_name"]
        params = tool_intent["params"]

        logger.info(f"检测到工具调用意图: {tool_name}, params: {params}")

        try:
            user_id = context.get("user_id")
            result = await execute_tool(
                tool_name=tool_name,
                params=params,
                context=self.get_tool_context(user_id),
                user_id=user_id,
                conversation_id=session_id,
            )

            if result.success:
                logger.info(f"工具执行成功: {tool_name}")
            else:
                logger.warning(f"工具执行失败: {tool_name}, error: {result.error}")

            return result

        except Exception as e:
            logger.exception(f"工具执行异常: {tool_name}")
            return None

    def format_tool_result_for_response(
            self, result: ToolResult, tool_name: str) -> str:
        """格式化工具结果用于 AI 回答"""
        if not result.success:
            return f"抱歉，调用工具「{tool_name}」时出现错误：{result.error}"

        data = result.data
        if isinstance(data, dict):
            if tool_name == "calculator":
                return f"根据计算，结果如下：{data.get('description', '')}"
            elif tool_name == "document_generation":
                doc_type = data.get("document_type", "文书")
                content = str(data.get("content", ""))
                return (
                    f"已为您生成{doc_type}，内容如下：\n\n"
                    f"{content[:500]}..."
                )
            elif tool_name == "lawfirm_search":
                recommendations = data.get("recommendations", [])
                if recommendations:
                    lines = ["为您推荐以下律师："]
                    for rec in recommendations[:3]:
                        lines.append(
                            f"- {rec['name']} ({rec['match_reason']})")
                    return "\n".join(lines)
                return "未找到匹配的律师"
            elif tool_name == "knowledge_search":
                results = data.get("results", [])
                if results:
                    lines = ["找到以下相关法条："]
                    for r in results[:3]:
                        lines.append(
                            f"- {r.get('title', '')} {r.get('article', '')}")
                    return "\n".join(lines)
                return "未找到相关法条"
            elif tool_name == "calendar":
                return f"日程信息：{json.dumps(data, ensure_ascii=False, indent=2)}"

        result_text = json.dumps(data, ensure_ascii=False, indent=2)
        return f"工具执行成功，结果：{result_text[:200]}"

    async def stream_with_tools(
        self,
        message: str,
        context: Dict[str, Any],
        session_id: str,
        history: List[Dict[str, str]],
    ) -> AsyncGenerator[tuple[str, Dict], None]:
        """流式生成回答，支持工具调用

        如果检测到工具调用，会先输出工具结果，再继续生成回答
        """
        # 检测是否需要调用工具
        tool_result = await self.execute_tool_if_needed(message, context, session_id)

        if tool_result and tool_result.success:
            # 先输出工具结果
            tool_response = self.format_tool_result_for_response(
                tool_result, (tool_result.data or {}).get("calculation_type") or "tool")

            yield ("content", {"text": tool_response})

            # 更新历史
            history.append({"role": "assistant", "content": tool_response})

            # 在工具结果后追加继续回答的前缀
            continue_prompt = "\n\n此外，关于您的问题，我还可以提供以下信息："
            yield ("content", {"text": continue_prompt})

            history.append({"role": "assistant", "content": continue_prompt})
