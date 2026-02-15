"""金额精度模块测试

测试金额计算和精度处理功能。
"""
import pytest
from decimal import Decimal


class TestMoney:
    """测试Money类"""

    def test_money_creation_from_float(self):
        """测试从浮点数创建Money对象"""
        from app.core.money import Money

        price = Money(99.99)
        assert price.amount == Decimal("99.99")

    def test_money_creation_from_string(self):
        """测试从字符串创建Money对象"""
        from app.core.money import Money

        price = Money("99.99")
        assert price.amount == Decimal("99.99")

    def test_money_precision(self):
        """测试精度控制"""
        from app.core.money import Money

        price = Money(99.999)
        assert price.amount == Decimal("100.00")

    def test_money_to_cents(self):
        """测试转换为分"""
        from app.core.money import Money

        price = Money(99.99)
        assert price.to_cents() == 9999

    def test_money_addition(self):
        """测试加法"""
        from app.core.money import Money

        result = Money("0.1") + Money("0.2")
        assert result.amount == Decimal("0.30")

    def test_money_subtraction(self):
        """测试减法"""
        from app.core.money import Money

        result = Money("1.00") - Money("0.30")
        assert result.amount == Decimal("0.70")

    def test_money_multiplication(self):
        """测试乘法"""
        from app.core.money import Money

        result = Money("0.10") * 2
        assert result.amount == Decimal("0.20")


class TestAmountConversion:
    """测试金额转换函数"""

    def test_quantize_amount(self):
        """测试金额舍入"""
        from app.core.money import quantize_amount

        result = quantize_amount(99.999)
        assert result == Decimal("100.00")

    def test_amount_to_cents(self):
        """测试金额转分"""
        from app.core.money import amount_to_cents

        result = amount_to_cents(99.99)
        assert result == 9999

    def test_cents_to_amount(self):
        """测试分转金额"""
        from app.core.money import cents_to_amount

        result = cents_to_amount(9999)
        assert result == Decimal("99.99")

    def test_format_money(self):
        """测试金额格式化"""
        from app.core.money import format_money

        result = format_money(99.99)
        assert result == "¥99.99"


class TestSafeCalculation:
    """测试安全计算函数"""

    def test_safe_add(self):
        """测试安全加法"""
        from app.core.money import safe_add

        result = safe_add("0.1", "0.2", "0.3")
        assert result == Decimal("0.60")

    def test_safe_subtract(self):
        """测试安全减法"""
        from app.core.money import safe_subtract

        result = safe_subtract(1, 0.3)
        assert result == Decimal("0.70")

    def test_safe_multiply(self):
        """测试安全乘法"""
        from app.core.money import safe_multiply

        result = safe_multiply(0.1, 3)
        assert result == Decimal("0.30")

    def test_validate_amount_range(self):
        """测试金额范围验证"""
        from app.core.money import validate_amount_range

        valid, _ = validate_amount_range(100, 1, 10000)
        assert valid is True

        valid, error = validate_amount_range(0.001, 0.01, 10000)
        assert valid is False
        assert "不能小于" in error


class TestMoneyCalculator:
    """测试金额计算器"""

    def test_calculator_chain(self):
        """测试链式计算"""
        from app.core.money import MoneyCalculator

        calc = MoneyCalculator(100)
        calc.add(50).subtract(30).multiply(2)
        assert calc.result() == Decimal("240.00")

    def test_calculator_percentage(self):
        """测试百分比计算"""
        from app.core.money import MoneyCalculator

        calc = MoneyCalculator(100)
        calc.percentage(20)
        assert calc.result() == Decimal("20.00")

    def test_calculator_to_cents(self):
        """测试转换为分"""
        from app.core.money import MoneyCalculator

        calc = MoneyCalculator(99.99)
        assert calc.to_cents() == 9999
