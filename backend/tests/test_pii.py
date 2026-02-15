import re

import pytest

import app.utils.pii as pii
from app.utils.pii import sanitize_pii


def test_sanitize_pii_masks_common_patterns():
    text = "手机号：13800138000 身份证：11010519900101123X 邮箱 test@example.com 银行卡 6222020402040204020"
    out = sanitize_pii(text)
    assert "13800138000" not in out
    assert "11010519900101123X" not in out
    assert "test@example.com" not in out
    assert "6222020402040204020" not in out
    assert "【手机号已脱敏】" in out
    assert "【身份证号已脱敏】" in out
    assert "【邮箱已脱敏】" in out
    assert "【银行卡号已脱敏】" in out


def test_sanitize_pii_empty_returns_empty():
    assert sanitize_pii("") == ""


def test_sanitize_pii_bank_repl_keeps_11_digits_non_phone_and_15_18_when_id_regex_disabled(monkeypatch: pytest.MonkeyPatch):
    out = sanitize_pii("11000000000")
    assert out == "11000000000"

    monkeypatch.setattr(pii, "_ID18_RE", re.compile(r"a^"), raising=True)
    monkeypatch.setattr(pii, "_ID15_RE", re.compile(r"a^"), raising=True)

    d18 = "123456789012345678"
    assert sanitize_pii(d18) == d18

    d15 = "123456789012345"
    assert sanitize_pii(d15) == d15


class TestPIIEdgeCases:
    """测试 PII 脱敏边缘情况"""

    def test_sanitize_pii_phone_only(self):
        """测试完整手机号脱敏"""
        out = sanitize_pii("13800138000")
        assert "【手机号已脱敏】" in out

    def test_sanitize_pii_id_only(self):
        """测试完整身份证号脱敏"""
        out = sanitize_pii("11010519900101123X")
        assert "【身份证号已脱敏】" in out

    def test_sanitize_pii_email_only(self):
        """测试完整邮箱脱敏"""
        out = sanitize_pii("test@example.com")
        assert "【邮箱已脱敏】" in out

    def test_sanitize_pii_bank_only(self):
        """测试完整银行卡号脱敏"""
        out = sanitize_pii("6222020402040204020")
        assert "【银行卡号已脱敏】" in out

    def test_sanitize_pii_multiple_same_type(self):
        """测试多个相同类型脱敏"""
        text = "手机1: 13800138001, 手机2: 13800138002"
        out = sanitize_pii(text)
        assert out.count("【手机号已脱敏】") == 2
        assert "13800138001" not in out
        assert "13800138002" not in out

    def test_sanitize_pii_mixed_content(self):
        """测试混合内容脱敏"""
        text = "张三的手机是13800138000，身份证11010519900101123X"
        out = sanitize_pii(text)
        assert "【手机号已脱敏】" in out
        assert "【身份证号已脱敏】" in out
        # 名字不应被脱敏
        assert "张三" in out

    def test_sanitize_pii_none_input(self):
        """测试 None 输入"""
        result = sanitize_pii(None)
        assert result == ""

    def test_sanitize_pii_unicode_content(self):
        """测试Unicode内容脱敏"""
        text = "中文手机号13800138000测试"
        out = sanitize_pii(text)
        assert "【手机号已脱敏】" in out
        assert "中文" in out
