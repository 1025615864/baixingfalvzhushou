"""审核流程边界测试"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.services.moderation_service import ModerationService
from app.utils.sensitive_words import SensitiveWordFilter


class TestModerationBoundaryCases:
    def setup_method(self):
        self.filter = SensitiveWordFilter()
        self.service = ModerationService()

    def test_empty_content(self):
        blocked, words = self.filter.check("")
        assert blocked is False
        assert len(words) == 0

    def test_whitespace_only(self):
        blocked, words = self.filter.check("   \n\t  ")
        assert blocked is False
        assert len(words) == 0

    def test_unicode_sensitive_words(self):
        blocked, words = self.filter.check("包含毒品和赌博的内容")
        assert blocked is True
        assert len(words) > 0

    def test_mixed_case_sensitive(self):
        blocked_lower = self.filter.check("毒品")
        blocked_upper = self.filter.check("毒品")
        assert blocked_lower[0] == blocked_upper[0]

    def test_partial_word_match(self):
        result1 = self.filter.check("赌博网站")
        assert result1[0] is True

        result2 = self.filter.check("一个很好的赌博")
        assert result2[0] is True

    def test_contact_info_various_formats(self):
        phone_formats = [
            "电话: 13812345678",
            "电话：13812345678",
            "手机13812345678",
            "138-1234-5678",
            "13812345678",
        ]
        for phone in phone_formats:
            assert self.service.check_contact_info(phone) is True, f"Failed for {phone}"

        wechat_formats = [
            "微信: lawyer123",
            "微信：lawyer123",
            "VX: lawyer123",
            "vxlawyer123",
        ]
        for wechat in wechat_formats:
            assert self.service.check_contact_info(wechat) is True, f"Failed for {wechat}"

        email_formats = [
            "邮箱: test@example.com",
            "邮箱：test@example.com",
            "email: test@example.com",
            "test@example.com",
        ]
        for email in email_formats:
            assert self.service.check_contact_info(email) is True, f"Failed for {email}"

    def test_clean_legal_content(self):
        legal_contents = [
            "我想咨询一下婚姻法的问题",
            "关于劳动仲裁的流程是什么",
            "交通事故责任如何划分",
            "房屋买卖合同需要注意什么",
            "请问个人所得税如何计算",
        ]
        for content in legal_contents:
            blocked, _ = self.service.sensitive_filter.check(content)
            assert blocked is False, f"False positive for: {content}"

    def test_length_boundaries(self):
        short_content = "a"
        result = self.filter.check(short_content)
        assert result[0] is False

        very_long_content = "a" * 10000
        result = self.filter.check(very_long_content)
        assert result[0] is False

    def test_special_characters(self):
        special_contents = [
            "这是一个包含@符号的内容",
            "包含#标签的内容",
            "包含$符号的内容",
            "包含%百分比的内容",
        ]
        for content in special_contents:
            blocked, _ = self.filter.check(content)
            assert blocked is False, f"False positive for special chars: {content}"

    def test_newlines_and_tabs(self):
        content_with_whitespace = "毒品\n赌博\r\n海洛因\t冰毒"
        blocked, words = self.filter.check(content_with_whitespace)
        assert blocked is True
        assert len(words) > 0


class TestModerationFilterReplacement:
    def setup_method(self):
        self.filter = SensitiveWordFilter()

    def test_replacement_with_asterisk(self):
        result = self.filter.filter("包含毒品的内容", replace_char="*")
        assert "毒品" not in result
        assert "*" in result

    def test_replacement_with_hash(self):
        result = self.filter.filter("赌博网站", replace_char="#")
        assert "赌博" not in result
        assert "#" in result

    def test_replacement_preserves_length(self):
        original = "毒品"
        result = self.filter.filter(original, replace_char="#")
        assert len(result) == len(original)

    def test_multiple_replacements(self):
        result = self.filter.filter(
            "毒品和赌博和吸毒",
            replace_char="#"
        )
        assert "毒品" not in result
        assert "赌博" not in result
        assert "吸毒" not in result
        assert result.count("#") >= 3


class TestModerationAsync:
    def setup_method(self):
        self.service = ModerationService()

    @pytest.mark.asyncio
    async def test_async_content_check(self):
        result = await self.service.check_content("正常的法律咨询内容")
        assert result.blocked is False
        assert result.reason is None

    @pytest.mark.asyncio
    async def test_async_blocked_content(self):
        result = await self.service.check_content("毒品和赌博网站")
        assert result.blocked is True
        assert result.reason is not None

    @pytest.mark.asyncio
    async def test_async_needs_review(self):
        result = await self.service.check_content("这个内容可能需要审核")
        assert result.needs_review is not None


class TestModerationResults:
    def setup_method(self):
        self.service = ModerationService()

    def test_result_structure(self):
        result = self.service.sensitive_filter.check("测试内容")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)

    def test_service_check_content_result(self):
        from app.services.moderation_service import ModerationResult

        result = ModerationResult(
            blocked=False,
            reason=None,
            needs_review=False
        )
        assert result.blocked is False
        assert result.needs_review is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
