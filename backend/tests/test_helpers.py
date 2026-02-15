import pytest
from datetime import datetime
from unittest.mock import patch
from app.utils.helpers import (
    _get_int_env,
    _coerce_int,
    _truncate,
    _parse_dt_param,
)


class TestGetIntEnv:
    """测试环境变量整数获取"""

    def test_with_valid_value(self):
        """测试获取有效整数值"""
        with patch.dict("os.environ", {"TEST_PORT": "8080"}):
            result = _get_int_env("TEST_PORT", 8000)
            assert result == 8080

    def test_with_invalid_value(self):
        """测试获取无效整数值时返回默认值"""
        with patch.dict("os.environ", {"TEST_PORT": "invalid"}):
            result = _get_int_env("TEST_PORT", 8000)
            assert result == 8000

    def test_with_empty_value(self):
        """测试获取空值时返回默认值"""
        with patch.dict("os.environ", {"TEST_PORT": ""}):
            result = _get_int_env("TEST_PORT", 8000)
            assert result == 8000

    def test_with_missing_key(self):
        """测试获取不存在的键时返回默认值"""
        with patch.dict("os.environ", {}, clear=True):
            result = _get_int_env("NONEXISTENT_PORT", 8000)
            assert result == 8000

    def test_with_negative_value(self):
        """测试获取负数值"""
        with patch.dict("os.environ", {"TEST_PORT": "-100"}):
            result = _get_int_env("TEST_PORT", 8000)
            assert result == -100


class TestCoerceInt:
    """测试整数强制转换"""

    def test_with_none(self):
        """测试 None 转换"""
        result = _coerce_int(None, 10)
        assert result == 10

    def test_with_int(self):
        """测试整数转换"""
        result = _coerce_int(42, 10)
        assert result == 42

    def test_with_float(self):
        """测试浮点数转换"""
        result = _coerce_int(3.14, 10)
        assert result == 3

    def test_with_string_number(self):
        """测试数字字符串转换"""
        result = _coerce_int("42", 10)
        assert result == 42

    def test_with_float_string(self):
        """测试浮点数字符串转换"""
        result = _coerce_int("3.14", 10)
        assert result == 3

    def test_with_empty_string(self):
        """测试空字符串转换"""
        result = _coerce_int("", 10)
        assert result == 10

    def test_with_whitespace_string(self):
        """测试空白字符串转换"""
        result = _coerce_int("   ", 10)
        assert result == 10

    def test_with_invalid_string(self):
        """测试无效字符串转换"""
        result = _coerce_int("invalid", 10)
        assert result == 10

    def test_with_bool_true(self):
        """测试 True 转换"""
        result = _coerce_int(True, 10)
        assert result == 10

    def test_with_bool_false(self):
        """测试 False 转换"""
        result = _coerce_int(False, 10)
        assert result == 10

    def test_with_default_zero(self):
        """测试默认值为0"""
        result = _coerce_int(None, 0)
        assert result == 0


class TestTruncate:
    """测试字符串截断"""

    def test_with_none(self):
        """测试 None 截断"""
        result = _truncate(None, 10)
        assert result is None

    def test_with_empty_string(self):
        """测试空字符串截断"""
        result = _truncate("", 10)
        assert result is None

    def test_with_whitespace_string(self):
        """测试空白字符串截断"""
        result = _truncate("   ", 10)
        assert result is None

    def test_with_short_string(self):
        """测试短字符串截断"""
        result = _truncate("hello", 10)
        assert result == "hello"

    def test_with_long_string(self):
        """测试长字符串截断"""
        result = _truncate("hello world", 5)
        assert result == "hello"

    def test_with_exact_length(self):
        """测试等于最大长度的字符串"""
        result = _truncate("hello", 5)
        assert result == "hello"

    def test_with_unicode(self):
        """测试Unicode字符串截断"""
        result = _truncate("你好世界", 2)
        assert result == "你好"

    def test_with_leading_whitespace(self):
        """测试带前导空白的字符串"""
        result = _truncate("  hello  ", 5)
        assert result == "hello"


class TestParseDtParam:
    """测试日期时间参数解析"""

    def test_with_none(self):
        """测试 None 解析"""
        result = _parse_dt_param(None, field="test")
        assert result is None

    def test_with_empty_string(self):
        """测试空字符串解析"""
        result = _parse_dt_param("", field="test")
        assert result is None

    def test_with_whitespace(self):
        """测试空白字符串解析"""
        result = _parse_dt_param("   ", field="test")
        assert result is None

    def test_with_valid_date(self):
        """测试有效日期解析"""
        result = _parse_dt_param("2024-01-15", field="created_at")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_with_datetime(self):
        """测试完整日期时间解析"""
        result = _parse_dt_param("2024-01-15 10:30:00", field="created_at")
        assert result is not None
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 0

    def test_with_iso_format(self):
        """测试ISO格式解析"""
        result = _parse_dt_param("2024-01-15T10:30:00", field="created_at")
        assert result is not None
        assert result.hour == 10

    def test_with_z_suffix(self):
        """测试Z后缀解析"""
        result = _parse_dt_param("2024-01-15T10:30:00Z", field="created_at")
        assert result is not None

    def test_with_end_of_day(self):
        """测试结束时间调整"""
        result = _parse_dt_param("2024-01-15", field="created_at", end_of_day=True)
        assert result is not None
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59

    def test_with_end_of_day_not_date_only(self):
        """测试结束时间调整（非纯日期）"""
        result = _parse_dt_param("2024-01-15 10:30:00", field="created_at", end_of_day=True)
        assert result is not None
        assert result.hour == 10
        assert result.minute == 30
