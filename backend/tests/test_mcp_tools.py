"""MCP Tools 测试 - 补充AI模块的工具测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestDocumentGenerationTool:
    """文档生成工具测试"""

    @pytest.fixture
    def tool(self):
        """创建文档生成工具实例"""
        from app.services.mcp.tools.document_tool import DocumentGenerationTool
        return DocumentGenerationTool()

    def test_tool_name(self, tool):
        """测试工具名称"""
        assert tool.name == "document_generation"

    def test_tool_description(self, tool):
        """测试工具描述"""
        assert "起诉状" in tool.description
        assert "答辩状" in tool.description

    def test_tool_category(self, tool):
        """测试工具分类"""
        from app.services.mcp import ToolCategory
        assert tool.category == ToolCategory.DOCUMENT

    def test_parameters_schema(self, tool):
        """测试参数模式"""
        schema = tool._get_parameters_schema()
        assert schema["type"] == "object"
        assert "document_type" in schema["properties"]
        assert "case_type" in schema["properties"]
        assert "plaintiff_name" in schema["properties"]
        assert "defendant_name" in schema["properties"]

    def test_parameters_schema_required_fields(self, tool):
        """测试必需参数"""
        schema = tool._get_parameters_schema()
        required = schema.get("required", [])
        assert "document_type" in required
        assert "case_type" in required
        assert "plaintiff_name" in required
        assert "defendant_name" in required

    @pytest.mark.asyncio
    async def test_execute_missing_required_params(self, tool):
        """测试参数验证"""
        from app.services.mcp import ToolResult

        result = await tool.execute({}, {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_complaint_generation(self, tool):
        """测试起诉状生成"""
        from app.services.mcp import ToolResult

        with patch.object(tool, '_generate_document', return_value="起诉状内容") as mock_gen:
            result = await tool.execute({
                "document_type": "complaint",
                "case_type": "labor_dispute",
                "plaintiff_name": "张三",
                "defendant_name": "某公司",
                "facts": "2024年1月入职，2024年6月被违法解除",
                "claims": "要求支付违法解除赔偿金"
            }, {})

            assert result.success is True
            assert "document_type" in result.data

    @pytest.mark.asyncio
    async def test_execute_defense_generation(self, tool):
        """测试答辩状生成"""

class TestKnowledgeSearchTool:
    """知识库搜索工具测试"""

    @pytest.fixture
    def tool(self):
        """创建知识搜索工具实例"""
        from app.services.mcp.tools.knowledge_tool import KnowledgeSearchTool
        return KnowledgeSearchTool()

    def test_tool_name(self, tool):
        """测试工具名称"""
        assert tool.name == "knowledge_search"

    def test_tool_description(self, tool):
        """测试工具描述"""
        assert "法条" in tool.description
        assert "案例" in tool.description

    def test_tool_category(self, tool):
        """测试工具分类"""
        from app.services.mcp import ToolCategory
        assert tool.category == ToolCategory.KNOWLEDGE

    def test_parameters_schema(self, tool):
        """测试参数模式"""
        schema = tool._get_parameters_schema()
        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "law_type" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_empty_query(self, tool):
        """测试空查询"""
        from app.services.mcp import ToolResult

        result = await tool.execute({"query": ""}, {})
        assert result.success is False
        assert "请提供搜索关键词" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_query(self, tool):
        """测试有效查询"""
        from app.services.mcp.base import ToolResult

        with patch.object(tool, '_search_knowledge', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [{"title": "劳动合同法", "content": "第X条"}]
            result = await tool.execute({"query": "劳动合同"}, {})

            assert result.success is True
            assert result.data["query"] == "劳动合同"

    @pytest.mark.asyncio
    async def test_execute_with_limit(self, tool):
        """测试带限制的查询"""
        from app.services.mcp.base import ToolResult

        with patch.object(tool, '_search_knowledge', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            result = await tool.execute({"query": "测试", "limit": 3}, {})

            assert result.success is True
            assert "limit" in str(result.data) or result.data.get("total") == 0


class TestLawfirmSearchTool:
    """律所搜索工具测试"""

    @pytest.fixture
    def tool(self):
        """创建律所搜索工具实例"""
        from app.services.mcp.tools.lawfirm_tool import LawfirmSearchTool
        return LawfirmSearchTool()

    def test_tool_name(self, tool):
        """测试工具名称"""
        assert tool.name == "lawfirm_search"

    def test_tool_category(self, tool):
        """测试工具分类"""
        from app.services.mcp import ToolCategory
        assert tool.category == ToolCategory.LAWFIRM

    def test_parameters_schema(self, tool):
        """测试参数模式"""
        schema = tool._get_parameters_schema()
        assert schema["type"] == "object"
        assert "action" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_search_firms(self, tool):
        """测试搜索律所"""
        from app.services.mcp import ToolResult

        with patch.object(tool, '_search_firms', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = ToolResult(success=True, data={"firms": []}, error=None)
            result = await tool.execute({"action": "search_firms", "city": "北京"}, {})

            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_search_lawyers(self, tool):
        """测试搜索律师"""
        from app.services.mcp import ToolResult

        with patch.object(tool, '_search_lawyers', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = ToolResult(success=True, data={"lawyers": []}, error=None)
            result = await tool.execute({"action": "search_lawyers", "specialty": "刑事"}, {})

            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_recommend(self, tool):
        """测试推荐律师"""
        from app.services.mcp import ToolResult

        with patch.object(tool, '_recommend_lawyers', new_callable=AsyncMock) as mock_recommend:
            mock_recommend.return_value = ToolResult(success=True, data={"recommendations": []}, error=None)
            result = await tool.execute({"action": "recommend", "case_type": "劳动纠纷"}, {})

            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_invalid_action(self, tool):
        """测试无效操作"""
        from app.services.mcp import ToolResult

        result = await tool.execute({"action": "invalid_action"}, {})
        assert result.success is False


class TestCalculatorTool:
    """计算器工具测试"""

    @pytest.fixture
    def tool(self):
        """创建计算器工具实例"""
        from app.services.mcp.tools.calculator_tool import CalculatorTool
        return CalculatorTool()

    def test_tool_name(self, tool):
        """测试工具名称"""
        assert tool.name == "calculator"

    def test_tool_category(self, tool):
        """测试工具分类"""
        from app.services.mcp import ToolCategory
        assert tool.category == ToolCategory.CALCULATOR

    def test_parameters_schema(self, tool):
        """测试参数模式"""
        schema = tool._get_parameters_schema()
        assert schema["type"] == "object"
        assert "calculation_type" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_litigation_fee(self, tool):
        """测试诉讼费计算"""
        from app.services.mcp import ToolResult

        with patch.object(tool, '_calculate_litigation_fee', new_callable=AsyncMock) as mock_calc:
            mock_calc.return_value = ToolResult(success=True, data={"fee": 50}, error=None)
            result = await tool.execute({
                "calculation_type": "litigation_fee",
                "amount": 10000
            }, {})

            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_limitation(self, tool):
        """测试诉讼时效计算"""
        from app.services.mcp import ToolResult

        with patch.object(tool, '_calculate_limitation', new_callable=AsyncMock) as mock_calc:
            mock_calc.return_value = ToolResult(success=True, data={"expired": False}, error=None)
            result = await tool.execute({
                "calculation_type": "limitation",
                "start_date": "2020-01-01",
                "end_date": "2024-01-01"
            }, {})

            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_severance(self, tool):
        """测试经济补偿金计算"""
        from app.services.mcp import ToolResult

        with patch.object(tool, '_calculate_severance', new_callable=AsyncMock) as mock_calc:
            mock_calc.return_value = ToolResult(success=True, data={"amount": 10000}, error=None)
            result = await tool.execute({
                "calculation_type": "severance",
                "amount": 10000,
                "work_years": 3
            }, {})

            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_missed_work(self, tool):
        """测试误工费计算"""
        from app.services.mcp import ToolResult

        with patch.object(tool, '_calculate_missed_work', new_callable=AsyncMock) as mock_calc:
            mock_calc.return_value = ToolResult(success=True, data={"amount": 3000}, error=None)
            result = await tool.execute({
                "calculation_type": "missed_work",
                "daily_wage": 300,
                "missed_days": 10
            }, {})

            assert result.success is True


class TestCalendarTool:
    """日历工具测试"""

    @pytest.fixture
    def tool(self):
        """创建日历工具实例"""
        from app.services.mcp.tools.calendar_tool import CalendarTool
        return CalendarTool()

    def test_tool_name(self, tool):
        """测试工具名称"""
        assert tool.name == "calendar"

    def test_tool_category(self, tool):
        """测试工具分类"""
        from app.services.mcp import ToolCategory
        assert tool.category == ToolCategory.UTILITY

    @pytest.mark.asyncio
    async def test_execute_check_availability(self, tool):
        """测试检查可用性"""
        from app.services.mcp import ToolResult

        with patch.object(tool, '_check_availability', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = ToolResult(success=True, data={"available": True}, error=None)
            result = await tool.execute({"action": "check_availability"}, {})

            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_book_appointment(self, tool):
        """测试预约"""
        from app.services.mcp import ToolResult

        with patch.object(tool, '_create_appointment', new_callable=AsyncMock) as mock_book:
            mock_book.return_value = ToolResult(success=True, data={"appointment_id": 123}, error=None)
            result = await tool.execute({
                "action": "create_appointment",
                "lawyer_id": 1,
                "date": "2024-06-01",
                "time_slot": "10:00-11:00"
            }, {"user_id": 1})

            assert result.success is True
