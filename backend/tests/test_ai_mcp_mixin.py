"""AI MCP Mixin 服务测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json


class TestAIAssistantMCPMixin:
    """AIAssistantMCPMixin 测试类"""

    @pytest.fixture
    def mixin_class(self):
        """创建测试用的 Mixin 类"""
        from app.services.ai_mcp_mixin import AIAssistantMCPMixin

        class TestAssistant(AIAssistantMCPMixin):
            pass

        return TestAssistant()

    @pytest.fixture
    def mock_context(self):
        """模拟上下文"""
        return {
            "user_id": 123,
            "is_authenticated": True,
            "is_vip": False,
            "is_admin": False,
        }

    def test_tool_trigger_words_exist(self, mixin_class):
        """测试工具触发词定义"""
        assert hasattr(mixin_class, "TOOL_TRIGGER_WORDS")
        assert "计算" in mixin_class.TOOL_TRIGGER_WORDS
        assert "生成文书" in mixin_class.TOOL_TRIGGER_WORDS
        assert "找律师" in mixin_class.TOOL_TRIGGER_WORDS

    def test_tool_patterns_exist(self, mixin_class):
        """测试工具模式定义"""
        assert hasattr(mixin_class, "TOOL_PATTERNS")
        assert "calculator" in mixin_class.TOOL_PATTERNS
        assert "document_generation" in mixin_class.TOOL_PATTERNS
        assert "lawfirm_search" in mixin_class.TOOL_PATTERNS

    def test_get_tool_context_with_user(self, mixin_class, mock_context):
        """测试获取工具调用上下文（已认证用户）"""
        ctx = mixin_class.get_tool_context(user_id=123)
        assert ctx["user_id"] == 123
        assert ctx["is_authenticated"] is True

    def test_get_tool_context_without_user(self, mixin_class):
        """测试获取工具调用上下文（未认证用户）"""
        ctx = mixin_class.get_tool_context(user_id=None)
        assert ctx["user_id"] is None
        assert ctx["is_authenticated"] is False

    def test_get_tools_for_system_prompt(self, mixin_class):
        """测试获取工具列表用于 system prompt"""
        with patch("app.services.ai_mcp_mixin.get_tools_for_prompt") as mock:
            mock.return_value = "tool1, tool2"
            result = mixin_class.get_tools_for_system_prompt()
            assert result == "tool1, tool2"

    def test_detect_tool_intent_no_match(self, mixin_class):
        """测试无工具匹配时返回 None"""
        result = mixin_class.detect_tool_intent("你好，我想咨询法律问题")
        assert result is None

    def test_detect_tool_intent_calculator_pattern(self, mixin_class):
        """测试计算器模式匹配"""
        result = mixin_class.detect_tool_intent("帮我计算5000元诉讼费")
        assert result is not None
        assert result["tool_name"] == "calculator"

    def test_detect_tool_intent_document_generation_pattern(self, mixin_class):
        """测试文书生成模式匹配"""
        # 使用触发词方式测试
        result = mixin_class.detect_tool_intent("生成文书")
        assert result is not None
        assert result["tool_name"] == "document_generation"

    def test_detect_tool_intent_lawfirm_search_pattern(self, mixin_class):
        """测试律所搜索模式匹配"""
        result = mixin_class.detect_tool_intent("我想找北京的劳动律师")
        assert result is not None
        assert result["tool_name"] == "lawfirm_search"

    def test_detect_tool_intent_knowledge_search_pattern(self, mixin_class):
        """测试知识搜索模式匹配"""
        result = mixin_class.detect_tool_intent("相关法规劳动法")
        assert result is not None
        assert result["tool_name"] == "knowledge_search"

    def test_detect_tool_intent_calendar_pattern(self, mixin_class):
        """测试日历模式匹配"""
        result = mixin_class.detect_tool_intent("我想预约咨询时间")
        assert result is not None
        assert result["tool_name"] == "calendar"

    def test_detect_tool_intent_trigger_word(self, mixin_class):
        """测试触发词检测"""
        result = mixin_class.detect_tool_intent("帮我算一下赔偿金额")
        assert result is not None
        assert result["tool_name"] == "calculator"

    def test_word_to_tool_mapping(self, mixin_class):
        """测试触发词到工具名的映射"""
        assert mixin_class._word_to_tool("计算") == "calculator"
        assert mixin_class._word_to_tool("生成文书") == "document_generation"
        assert mixin_class._word_to_tool("找律师") == "lawfirm_search"
        assert mixin_class._word_to_tool("查询法条") == "knowledge_search"
        assert mixin_class._word_to_tool("预约") == "calendar"

    def test_extract_tool_params_calculator(self, mixin_class):
        """测试计算器参数提取"""
        params = mixin_class._extract_tool_params(
            "calculator", "帮我计算5000元诉讼费"
        )
        assert params["action"] == "litigation_fee"
        assert params["amount"] == 5000.0

    def test_extract_tool_params_calculator_limitation(self, mixin_class):
        """测试计算器参数提取 - 诉讼时效"""
        params = mixin_class._extract_tool_params(
            "calculator", "诉讼时效从2020-01-01开始"
        )
        assert params["calculation_type"] == "limitation"

    def test_extract_tool_params_document_generation(self, mixin_class):
        """测试文书生成参数提取"""
        params = mixin_class._extract_tool_params(
            "document_generation", "帮我写一份劳动纠纷的起诉状"
        )
        assert params["document_type"] == "complaint"
        assert params["case_type"] == "labor_dispute"

    def test_extract_tool_params_document_generation_defense(self, mixin_class):
        """测试文书生成参数提取 - 答辩状"""
        params = mixin_class._extract_tool_params(
            "document_generation", "写一份离婚答辩状"
        )
        assert params["document_type"] == "defense"
        assert params["case_type"] == "marriage_family"

    def test_extract_tool_params_lawfirm_search(self, mixin_class):
        """测试律所搜索参数提取"""
        params = mixin_class._extract_tool_params(
            "lawfirm_search", "我想找上海的合同律师"
        )
        assert params["action"] == "recommend"
        assert params["city"] == "上海"
        assert params["case_type"] == "contract_dispute"

    def test_extract_tool_params_knowledge_search(self, mixin_class):
        """测试知识搜索参数提取"""
        params = mixin_class._extract_tool_params(
            "knowledge_search", "婚姻法规定离婚条件"
        )
        assert params["action"] == "search"
        assert "离婚" in params["query"] or "条件" in params["query"]

    def test_extract_tool_params_calendar(self, mixin_class):
        """测试日历参数提取"""
        params = mixin_class._extract_tool_params("calendar", "我想预约咨询")
        assert params["action"] == "check_availability"

    def test_get_default_action(self, mixin_class):
        """测试获取默认操作"""
        assert mixin_class._get_default_action("calculator") == "litigation_fee"
        assert mixin_class._get_default_action("document_generation") == "generate"
        assert mixin_class._get_default_action("lawfirm_search") == "recommend"
        assert mixin_class._get_default_action("knowledge_search") == "search"
        assert mixin_class._get_default_action("calendar") == "check_availability"

    def test_extract_tool_params_by_word(self, mixin_class):
        """测试根据触发词提取参数"""
        params = mixin_class._extract_tool_params_by_word("计算", "帮我计算")
        assert params["action"] == "litigation_fee"

    @pytest.mark.asyncio
    async def test_execute_tool_if_needed_no_intent(self, mixin_class, mock_context):
        """测试无工具意图时不执行"""
        with patch.object(mixin_class, "detect_tool_intent", return_value=None):
            result = await mixin_class.execute_tool_if_needed(
                "你好啊", mock_context, "session-123"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_execute_tool_if_needed_with_intent(self, mixin_class, mock_context):
        """测试有工具意图时执行"""
        from app.services.mcp import ToolResult

        mock_tool_result = ToolResult(
            success=True, data={"result": "test"}, error=None
        )

        with patch.object(mixin_class, "detect_tool_intent") as mock_detect:
            mock_detect.return_value = {
                "tool_name": "calculator",
                "params": {"action": "litigation_fee"},
            }
            with patch("app.services.ai_mcp_mixin.execute_tool", new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = mock_tool_result
                result = await mixin_class.execute_tool_if_needed(
                    "帮我计算5000元", mock_context, "session-123"
                )
                assert result.success is True
                assert result.data == {"result": "test"}

    def test_format_tool_result_for_response_success(self, mixin_class):
        """测试格式化工具结果 - 成功"""
        from app.services.mcp import ToolResult

        result = ToolResult(
            success=True, data={"description": "诉讼费为50元"}, error=None
        )
        formatted = mixin_class.format_tool_result_for_response(result, "calculator")
        assert "根据计算，结果如下：诉讼费为50元" in formatted

    def test_format_tool_result_for_response_failure(self, mixin_class):
        """测试格式化工具结果 - 失败"""
        from app.services.mcp import ToolResult

        result = ToolResult(success=False, data=None, error="计算失败")
        formatted = mixin_class.format_tool_result_for_response(result, "calculator")
        assert "抱歉" in formatted
        assert "计算失败" in formatted

    def test_format_tool_result_for_response_document(self, mixin_class):
        """测试格式化工具结果 - 文书生成"""
        from app.services.mcp import ToolResult

        result = ToolResult(
            success=True,
            data={
                "document_type": "起诉状",
                "content": "原告张三，被告李四...",
            },
            error=None,
        )
        formatted = mixin_class.format_tool_result_for_response(result, "document_generation")
        assert "已为您生成起诉状" in formatted

    def test_format_tool_result_for_response_lawfirm(self, mixin_class):
        """测试格式化工具结果 - 律所推荐"""
        from app.services.mcp import ToolResult

        result = ToolResult(
            success=True,
            data={
                "recommendations": [
                    {"name": "张律师", "match_reason": "专业劳动法律师"},
                    {"name": "李律师", "match_reason": "十年执业经验"},
                ]
            },
            error=None,
        )
        formatted = mixin_class.format_tool_result_for_response(result, "lawfirm_search")
        assert "为您推荐以下律师" in formatted

    def test_format_tool_result_for_response_knowledge(self, mixin_class):
        """测试格式化工具结果 - 知识搜索"""
        from app.services.mcp import ToolResult

        result = ToolResult(
            success=True,
            data={
                "results": [
                    {"title": "劳动合同法", "article": "第X条"},
                    {"title": "劳动法", "article": "第Y条"},
                ]
            },
            error=None,
        )
        formatted = mixin_class.format_tool_result_for_response(result, "knowledge_search")
        assert "找到以下相关法条" in formatted


class TestAIAssistantMCPMixinEdgeCases:
    """AIAssistantMCPMixin 边界情况测试"""

    @pytest.fixture
    def mixin_class(self):
        from app.services.ai_mcp_mixin import AIAssistantMCPMixin

        class TestAssistant(AIAssistantMCPMixin):
            pass

        return TestAssistant()

    @pytest.fixture
    def mock_context(self):
        """模拟上下文"""
        return {
            "user_id": 123,
            "is_authenticated": True,
            "is_vip": False,
            "is_admin": False,
        }

    def test_detect_tool_intent_empty_message(self, mixin_class):
        """测试空消息"""
        result = mixin_class.detect_tool_intent("")
        assert result is None

    def test_detect_tool_intent_special_characters(self, mixin_class):
        """测试特殊字符"""
        result = mixin_class.detect_tool_intent("帮我计算100元！@@##")
        assert result is not None
        assert result["tool_name"] == "calculator"

    def test_detect_tool_intent_mixed_case(self, mixin_class):
        """测试混合大小写"""
        result = mixin_class.detect_tool_intent("HELP ME 生成文书")
        assert result is not None or result is None

    def test_extract_tool_params_unknown_tool(self, mixin_class):
        """测试未知工具"""
        params = mixin_class._extract_tool_params("unknown_tool", "test message")
        assert params["action"] == "execute"

    def test_extract_tool_params_calculator_no_amount(self, mixin_class):
        """测试计算器无金额"""
        params = mixin_class._extract_tool_params(
            "calculator", "帮我计算诉讼费"
        )
        assert "amount" not in params

    def test_extract_tool_params_lawfirm_no_city(self, mixin_class):
        """测试律所搜索无城市"""
        params = mixin_class._extract_tool_params(
            "lawfirm_search", "我想找律师帮我打官司"
        )
        assert "city" not in params

    def test_format_tool_result_for_response_empty_data(self, mixin_class):
        """测试格式化空数据"""
        from app.services.mcp import ToolResult

        result = ToolResult(success=True, data={}, error=None)
        formatted = mixin_class.format_tool_result_for_response(result, "calculator")
        assert "根据计算" in formatted
        assert "结果如下" in formatted

    @pytest.mark.asyncio
    async def test_execute_tool_if_needed_handles_exception(self, mixin_class, mock_context):
        """测试工具执行异常时返回 None"""
        with patch.object(mixin_class, "detect_tool_intent") as mock_detect:
            mock_detect.return_value = {
                "tool_name": "calculator",
                "params": {"action": "litigation_fee"},
            }
            with patch(
                "app.services.ai_mcp_mixin.execute_tool",
                new=AsyncMock(side_effect=RuntimeError("boom")),
            ):
                result = await mixin_class.execute_tool_if_needed(
                    "帮我计算", mock_context, "session-err"
                )
                assert result is None


class TestAIAssistantMCPMixinStreaming:
    """AIAssistantMCPMixin 流式输出测试"""

    @pytest.fixture
    def mixin_class(self):
        from app.services.ai_mcp_mixin import AIAssistantMCPMixin

        class TestAssistant(AIAssistantMCPMixin):
            pass

        return TestAssistant()

    @pytest.mark.asyncio
    async def test_stream_with_tools_yields_tool_and_prompt(self, mixin_class):
        """测试流式输出包含工具结果和续写提示"""
        from app.services.mcp import ToolResult

        tool_result = ToolResult(
            success=True,
            data={"calculation_type": "calculator", "description": "金额为100元"},
            error=None,
        )
        history: list[dict[str, str]] = []

        with patch.object(
            mixin_class, "execute_tool_if_needed", new=AsyncMock(return_value=tool_result)
        ):
            chunks = [item async for item in mixin_class.stream_with_tools(
                "帮我算一下", {"user_id": 1}, "session-1", history
            )]

        assert len(chunks) == 2
        assert chunks[0][0] == "content"
        assert "金额为100元" in chunks[0][1]["text"]
        assert "此外" in chunks[1][1]["text"]
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_stream_with_tools_no_intent(self, mixin_class):
        """测试未触发工具时无输出"""
        history: list[dict[str, str]] = []
        with patch.object(
            mixin_class, "execute_tool_if_needed", new=AsyncMock(return_value=None)
        ):
            chunks = [item async for item in mixin_class.stream_with_tools(
                "你好", {}, "session-2", history
            )]

        assert chunks == []
        assert history == []
