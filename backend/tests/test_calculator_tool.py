"""Calculator Tool 服务测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone


class TestCalculatorTool:
    """CalculatorTool 测试类"""

    @pytest.fixture
    def tool(self):
        """创建测试用的 CalculatorTool 实例"""
        from app.services.mcp.tools.calculator_tool import CalculatorTool
        return CalculatorTool()

    @pytest.fixture
    def mock_context(self):
        """模拟上下文"""
        return {
            "user_id": 123,
            "is_authenticated": True,
            "is_vip": False,
        }

    def test_tool_name(self, tool):
        """测试工具名称"""
        assert tool.name == "calculator"

    def test_tool_description(self, tool):
        """测试工具描述"""
        assert "诉讼费用计算" in tool.description
        assert "诉讼时效计算" in tool.description

    def test_tool_version(self, tool):
        """测试工具版本"""
        assert tool.version == "1.0.0"

    def test_tool_category(self, tool):
        """测试工具类别"""
        from app.services.mcp.base import ToolCategory
        assert tool.category == ToolCategory.CALCULATOR

    def test_tool_permission(self, tool):
        """测试工具权限"""
        from app.services.mcp.base import ToolPermission
        assert tool.permission == ToolPermission.PUBLIC

    def test_tool_tags(self, tool):
        """测试工具标签"""
        assert "计算" in tool.tags
        assert "费用" in tool.tags
        assert "诉讼费" in tool.tags

    def test_parameters_schema(self, tool):
        """测试参数模式"""
        schema = tool._get_parameters_schema()
        assert schema["type"] == "object"
        assert "calculation_type" in schema["properties"]
        assert "amount" in schema["properties"]
        assert "litigation_fee" in schema["properties"]["calculation_type"]["enum"]
        assert "limitation" in schema["properties"]["calculation_type"]["enum"]

    @pytest.mark.asyncio
    async def test_execute_unknown_calculation_type(self, tool, mock_context):
        """测试不支持的计算类型"""
        result = await tool.execute(
            {"calculation_type": "unknown_type"},
            mock_context
        )
        assert result.success is False
        assert "不支持的计算类型" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_exception(self, tool, mock_context):
        """测试执行异常处理"""
        # Mock _calculate_litigation_fee to raise exception
        tool._calculate_litigation_fee = AsyncMock(side_effect=Exception("Test error"))
        
        result = await tool.execute(
            {"calculation_type": "litigation_fee", "amount": 10000},
            mock_context
        )
        assert result.success is False
        assert "计算失败" in result.error


class TestCalculatorToolLitigationFee:
    """CalculatorTool 诉讼费计算测试"""

    @pytest.fixture
    def tool(self):
        from app.services.mcp.tools.calculator_tool import CalculatorTool
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_calculate_litigation_fee_below_10000(self, tool):
        """测试诉讼费计算 - 金额小于1万"""
        result = await tool._calculate_litigation_fee({"amount": 5000})
        assert result.success is True
        assert result.data["fee"] == 50

    @pytest.mark.asyncio
    async def test_calculate_litigation_fee_10000_to_100000(self, tool):
        """测试诉讼费计算 - 金额1万到10万"""
        result = await tool._calculate_litigation_fee({"amount": 50000})
        assert result.success is True
        # 50 + (50000 - 10000) * 0.025 = 50 + 1000 = 1050
        expected_fee = 50 + (50000 - 10000) * 0.025
        assert result.data["fee"] == round(expected_fee, 2)

    @pytest.mark.asyncio
    async def test_calculate_litigation_fee_100000_to_200000(self, tool):
        """测试诉讼费计算 - 金额10万到20万"""
        result = await tool._calculate_litigation_fee({"amount": 150000})
        assert result.success is True
        # 50 + 90000 * 0.025 + (150000 - 100000) * 0.02 = 50 + 2250 + 1000 = 3300
        expected_fee = 50 + 90000 * 0.025 + (150000 - 100000) * 0.02
        assert result.data["fee"] == round(expected_fee, 2)

    @pytest.mark.asyncio
    async def test_calculate_litigation_fee_500000_to_1000000(self, tool):
        """测试诉讼费计算 - 金额50万到100万"""
        result = await tool._calculate_litigation_fee({"amount": 800000})
        assert result.success is True
        expected_fee = 50 + 90000 * 0.025 + 100000 * 0.02 + 300000 * 0.015 + (800000 - 500000) * 0.01
        assert result.data["fee"] == round(expected_fee, 2)

    @pytest.mark.asyncio
    async def test_calculate_litigation_fee_above_1000000(self, tool):
        """测试诉讼费计算 - 金额超过100万"""
        result = await tool._calculate_litigation_fee({"amount": 2000000})
        assert result.success is True
        expected_fee = 50 + 90000 * 0.025 + 100000 * 0.02 + 300000 * 0.015 + 500000 * 0.01 + (2000000 - 1000000) * 0.005
        assert result.data["fee"] == round(expected_fee, 2)

    @pytest.mark.asyncio
    async def test_calculate_litigation_fee_labor_case(self, tool):
        """测试诉讼费计算 - 劳动争议案件"""
        result = await tool._calculate_litigation_fee({"amount": 50000, "case_type": "labor"})
        assert result.success is True
        assert result.data["fee"] == 10

    @pytest.mark.asyncio
    async def test_calculate_litigation_fee_small_amount(self, tool):
        """测试诉讼费计算 - 小金额简化收费"""
        result = await tool._calculate_litigation_fee({"amount": 500})
        assert result.success is True
        assert result.data["fee"] == 30  # min(fee, 30)

    @pytest.mark.asyncio
    async def test_calculate_litigation_fee_zero_amount(self, tool):
        """测试诉讼费计算 - 零金额"""
        result = await tool._calculate_litigation_fee({"amount": 0})
        assert result.success is False
        assert "请输入有效的诉讼标的金额" in result.error

    @pytest.mark.asyncio
    async def test_calculate_litigation_fee_negative_amount(self, tool):
        """测试诉讼费计算 - 负金额"""
        result = await tool._calculate_litigation_fee({"amount": -1000})
        assert result.success is False
        assert "请输入有效的诉讼标的金额" in result.error

    @pytest.mark.asyncio
    async def test_calculate_litigation_fee_no_amount(self, tool):
        """测试诉讼费计算 - 无金额参数"""
        result = await tool._calculate_litigation_fee({})
        assert result.success is False
        assert "请输入有效的诉讼标的金额" in result.error


class TestCalculatorToolLimitation:
    """CalculatorTool 诉讼时效计算测试"""

    @pytest.fixture
    def tool(self):
        from app.services.mcp.tools.calculator_tool import CalculatorTool
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_calculate_limitation_not_expired(self, tool):
        """测试时效计算 - 未过期"""
        # Start date 1 year ago
        start_date = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%d")
        result = await tool._calculate_limitation({"start_date": start_date})
        assert result.success is True
        assert result.data["is_expired"] is False
        assert result.data["days_remaining"] > 0

    @pytest.mark.asyncio
    async def test_calculate_limitation_expired(self, tool):
        """测试时效计算 - 已过期"""
        # Start date 4 years ago
        start_date = (datetime.now(timezone.utc) - timedelta(days=4 * 365)).strftime("%Y-%m-%d")
        result = await tool._calculate_limitation({"start_date": start_date})
        assert result.success is True
        assert result.data["is_expired"] is True
        assert "advice" in result.data

    @pytest.mark.asyncio
    async def test_calculate_limitation_with_end_date(self, tool):
        """测试时效计算 - 指定结束日期"""
        start_date = "2020-01-01"
        end_date = "2023-06-01"
        result = await tool._calculate_limitation({
            "start_date": start_date,
            "end_date": end_date
        })
        assert result.success is True
        assert result.data["dispute_date"] == start_date
        assert result.data["check_date"] == end_date

    @pytest.mark.asyncio
    async def test_calculate_limitation_no_start_date(self, tool):
        """测试时效计算 - 无开始日期"""
        result = await tool._calculate_limitation({})
        assert result.success is False
        assert "请提供纠纷发生日期" in result.error

    @pytest.mark.asyncio
    async def test_calculate_limitation_invalid_date_format(self, tool):
        """测试时效计算 - 错误日期格式"""
        result = await tool._calculate_limitation({"start_date": "2020/01/01"})
        assert result.success is False
        assert "日期格式错误" in result.error


class TestCalculatorToolSeverance:
    """CalculatorTool 经济补偿金计算测试"""

    @pytest.fixture
    def tool(self):
        from app.services.mcp.tools.calculator_tool import CalculatorTool
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_calculate_severance_normal(self, tool):
        """测试经济补偿金计算 - 正常情况"""
        result = await tool._calculate_severance({
            "amount": 10000,
            "work_years": 5
        })
        assert result.success is True
        assert result.data["total_months"] == 5
        assert result.data["total_compensation"] == 50000

    @pytest.mark.asyncio
    async def test_calculate_severance_with_fraction(self, tool):
        """测试经济补偿金计算 - 带小数的工作年限"""
        result = await tool._calculate_severance({
            "amount": 10000,
            "work_years": 3.5
        })
        assert result.success is True
        assert result.data["years_count"] == 3
        assert result.data["months_compensation"] == 0.5
        assert result.data["total_months"] == 3.5

    @pytest.mark.asyncio
    async def test_calculate_severance_more_than_6_months(self, tool):
        """测试经济补偿金计算 - 超过6个月"""
        result = await tool._calculate_severance({
            "amount": 10000,
            "work_years": 2.7
        })
        assert result.success is True
        assert result.data["years_count"] == 3  # rounds up
        assert result.data["months_compensation"] == 0
        assert result.data["total_months"] == 3

    @pytest.mark.asyncio
    async def test_calculate_severance_zero_wage(self, tool):
        """测试经济补偿金计算 - 零工资"""
        result = await tool._calculate_severance({
            "amount": 0,
            "work_years": 5
        })
        assert result.success is False
        assert "请输入月工资数额" in result.error

    @pytest.mark.asyncio
    async def test_calculate_severance_zero_years(self, tool):
        """测试经济补偿金计算 - 零工作年限"""
        result = await tool._calculate_severance({
            "amount": 10000,
            "work_years": 0
        })
        assert result.success is False
        assert "请输入工作年限" in result.error

    @pytest.mark.asyncio
    async def test_calculate_severance_negative_wage(self, tool):
        """测试经济补偿金计算 - 负工资"""
        result = await tool._calculate_severance({
            "amount": -1000,
            "work_years": 5
        })
        assert result.success is False
        assert "请输入月工资数额" in result.error


class TestCalculatorToolMissedWork:
    """CalculatorTool 误工费计算测试"""

    @pytest.fixture
    def tool(self):
        from app.services.mcp.tools.calculator_tool import CalculatorTool
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_calculate_missed_work_normal(self, tool):
        """测试误工费计算 - 正常情况"""
        result = await tool._calculate_missed_work({
            "daily_wage": 500,
            "missed_days": 10
        })
        assert result.success is True
        assert result.data["total_compensation"] == 5000

    @pytest.mark.asyncio
    async def test_calculate_missed_work_fraction_days(self, tool):
        """测试误工费计算 - 带小数的天数"""
        result = await tool._calculate_missed_work({
            "daily_wage": 500,
            "missed_days": 7.5
        })
        assert result.success is True
        assert result.data["total_compensation"] == 3750

    @pytest.mark.asyncio
    async def test_calculate_missed_work_zero_wage(self, tool):
        """测试误工费计算 - 零日工资"""
        result = await tool._calculate_missed_work({
            "daily_wage": 0,
            "missed_days": 10
        })
        assert result.success is False
        assert "请输入日工资数额" in result.error

    @pytest.mark.asyncio
    async def test_calculate_missed_work_zero_days(self, tool):
        """测试误工费计算 - 零误工天数"""
        result = await tool._calculate_missed_work({
            "daily_wage": 500,
            "missed_days": 0
        })
        assert result.success is False
        assert "请输入误工天数" in result.error

    @pytest.mark.asyncio
    async def test_calculate_missed_work_negative_wage(self, tool):
        """测试误工费计算 - 负日工资"""
        result = await tool._calculate_missed_work({
            "daily_wage": -100,
            "missed_days": 10
        })
        assert result.success is False
        assert "请输入日工资数额" in result.error

    @pytest.mark.asyncio
    async def test_calculate_missed_work_negative_days(self, tool):
        """测试误工费计算 - 负误工天数"""
        result = await tool._calculate_missed_work({
            "daily_wage": 500,
            "missed_days": -5
        })
        assert result.success is False
        assert "请输入误工天数" in result.error
