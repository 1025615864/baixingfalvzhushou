"""内容审核服务测试"""
from __future__ import annotations

import pytest

from app.services.content_moderation import (
    KeywordFilter,
    ContentModerationService,
    content_moderation_service,
    submit_content_for_moderation,
    ai_review_content,
    get_moderation_stats,
)


class TestKeywordFilter:
    """关键词过滤器测试"""

    def test_add_keyword(self):
        """测试添加关键词"""
        filter = KeywordFilter()
        result = filter.add_keyword(
            keyword="test",
            category="political",
            severity="high",
        )

        assert result["keyword_id"] == "KW-0001"
        assert result["keyword"] == "test"
        assert result["category"] == "political"

    def test_add_keyword_custom_category(self):
        """测试添加关键词（自定义分类）"""
        filter = KeywordFilter()
        result = filter.add_keyword(
            keyword="spam",
            category="advertisement",
            severity="medium",
        )

        assert result["category"] == "advertisement"

    def test_check_content_safe(self):
        """测试检查内容（安全）"""
        filter = KeywordFilter()
        filter.add_keyword("badword", category="violence", severity="high")

        result = filter.check_content("This is safe content")

        assert result["is_safe"] is True
        assert result["risk_score"] == 0
        assert result["matched_count"] == 0

    def test_check_content_unsafe(self):
        """测试检查内容（不安全）"""
        filter = KeywordFilter()
        filter.add_keyword("badword", category="violence", severity="high")

        result = filter.check_content("This contains badword")

        assert result["is_safe"] is False
        assert result["risk_score"] == 30
        assert result["matched_count"] == 1
        assert result["matched_keywords"][0]["keyword"] == "badword"

    def test_check_content_with_category_filter(self):
        """测试检查内容（带分类过滤）"""
        filter = KeywordFilter()
        filter.add_keyword("political", category="political", severity="high")
        filter.add_keyword("spam", category="advertisement", severity="low")

        result = filter.check_content("political spam", categories=["advertisement"])

        assert result["matched_count"] == 1
        assert result["matched_keywords"][0]["keyword"] == "spam"

    def test_get_keywords_by_category(self):
        """测试获取分类关键词"""
        filter = KeywordFilter()
        filter.add_keyword("word1", category="political")
        filter.add_keyword("word2", category="political")
        filter.add_keyword("word3", category="violence")

        keywords = filter.get_keywords_by_category("political")

        assert len(keywords) == 2


class TestContentModerationService:
    """内容审核服务测试"""

    @pytest.mark.asyncio
    async def test_submit_content(self):
        """测试提交内容审核"""
        service = ContentModerationService()
        result = await service.submit_content(
            user_id=1,
            content_type="post",
            content="测试内容",
        )

        assert result["content_id"] == 1
        assert result["status"] == "pending"
        assert "risk_score" in result

    @pytest.mark.asyncio
    async def test_ai_review_safe(self):
        """测试AI审核（安全）"""
        service = ContentModerationService()
        await service.submit_content(
            user_id=1,
            content_type="post",
            content="这是一条正常的内容",
        )

        result = await service.ai_review(1)

        assert result["success"] is True
        assert result["is_safe"] is True
        assert result["confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_ai_review_unsafe_fraud(self):
        """测试AI审核（诈骗）"""
        service = ContentModerationService()
        await service.submit_content(
            user_id=1,
            content_type="post",
            content="这是一个诈骗信息",
        )

        result = await service.ai_review(1)

        assert result["success"] is True
        assert result["is_safe"] is False
        assert "potential_fraud" in result["flags"]

    @pytest.mark.asyncio
    async def test_ai_review_unsafe_gambling(self):
        """测试AI审核（赌博）"""
        service = ContentModerationService()
        await service.submit_content(
            user_id=1,
            content_type="post",
            content="赌博网站链接",
        )

        result = await service.ai_review(1)

        assert result["success"] is True
        assert result["is_safe"] is False
        assert "gambling" in result["flags"]

    @pytest.mark.asyncio
    async def test_ai_review_unsafe_pornographic(self):
        """测试AI审核（色情）"""
        service = ContentModerationService()
        await service.submit_content(
            user_id=1,
            content_type="post",
            content="色情内容",
        )

        result = await service.ai_review(1)

        assert result["success"] is True
        assert result["is_safe"] is False
        assert "pornographic" in result["flags"]

    @pytest.mark.asyncio
    async def test_ai_review_not_found(self):
        """测试AI审核（内容不存在）"""
        service = ContentModerationService()
        result = await service.ai_review(999)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_make_decision_auto_approved(self):
        """测试自动决策（通过）"""
        service = ContentModerationService()
        await service.submit_content(
            user_id=1,
            content_type="post",
            content="安全内容",
        )
        await service.ai_review(1)

        result = await service.make_decision(1, decision="auto")

        assert result["success"] is True
        assert result["decision"] == "approved"

    @pytest.mark.asyncio
    async def test_make_decision_manual(self):
        """测试手动决策"""
        service = ContentModerationService()
        await service.submit_content(
            user_id=1,
            content_type="post",
            content="测试内容",
        )

        result = await service.make_decision(1, decision="rejected")

        assert result["success"] is True
        assert result["decision"] == "rejected"

    @pytest.mark.asyncio
    async def test_make_decision_not_found(self):
        """测试决策（内容不存在）"""
        service = ContentModerationService()
        result = await service.make_decision(999, decision="approved")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_moderation_stats(self):
        """测试获取审核统计"""
        service = ContentModerationService()
        await service.submit_content(user_id=1, content_type="post", content="内容1")
        await service.submit_content(user_id=2, content_type="post", content="内容2")
        await service.ai_review(1)
        await service.make_decision(1, decision="approved")

        stats = await service.get_moderation_stats()

        assert stats["total_content"] == 2
        assert stats["approved"] == 1
        assert "approval_rate" in stats

    @pytest.mark.asyncio
    async def test_report_content(self):
        """测试举报内容"""
        service = ContentModerationService()
        await service.submit_content(user_id=1, content_type="post", content="内容")

        result = await service.report_content(
            reporter_id=2,
            content_id=1,
            reason="违规内容",
        )

        assert result["report_id"] == 1
        assert result["status"] == "pending"

    def test_get_total_checks(self):
        """测试获取总检查数"""
        service = ContentModerationService()
        service._contents[1] = {"id": 1}
        service._contents[2] = {"id": 2}

        count = service.get_total_checks()
        assert count == 2

    def test_get_blocked_count(self):
        """测试获取拦截数"""
        service = ContentModerationService()
        service._contents[1] = {"final_decision": "rejected"}
        service._contents[2] = {"final_decision": "approved"}

        count = service.get_blocked_count()
        assert count == 1

    def test_get_warning_count(self):
        """测试获取警告数"""
        service = ContentModerationService()
        service._contents[1] = {"check_result": {"risk_level": "high"}}
        service._contents[2] = {"check_result": {"risk_level": "low"}}

        count = service.get_warning_count()
        assert count == 1

    def test_get_passed_count(self):
        """测试获取通过数"""
        service = ContentModerationService()
        service._contents[1] = {"final_decision": "approved"}
        service._contents[2] = {"final_decision": "rejected"}

        count = service.get_passed_count()
        assert count == 1

    def test_get_block_rate(self):
        """测试获取拦截率"""
        service = ContentModerationService()
        service._contents[1] = {"final_decision": "rejected"}
        service._contents[2] = {"final_decision": "rejected"}
        service._contents[3] = {"final_decision": "approved"}

        rate = service.get_block_rate()
        assert rate == 66.67

    def test_get_block_rate_empty(self):
        """测试获取拦截率（空）"""
        service = ContentModerationService()
        rate = service.get_block_rate()
        assert rate == 0.0

    def test_get_category_count(self):
        """测试获取分类计数"""
        service = ContentModerationService()
        service._contents[1] = {"content_type": "post"}
        service._contents[2] = {"content_type": "post"}
        service._contents[3] = {"content_type": "comment"}

        count = service.get_category_count("post")
        assert count == 2


class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_submit_content_for_moderation(self):
        """测试提交内容审核便捷函数"""
        result = await submit_content_for_moderation(
            user_id=1,
            content_type="post",
            content="测试内容",
        )

        assert result["content_id"] == 1
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_ai_review_content(self):
        """测试AI审核内容便捷函数"""
        await submit_content_for_moderation(
            user_id=1,
            content_type="post",
            content="测试内容",
        )

        result = await ai_review_content(1)

        assert result["success"] is True
        assert "is_safe" in result

    @pytest.mark.asyncio
    async def test_get_moderation_stats_function(self):
        """测试获取审核统计便捷函数"""
        service = ContentModerationService()
        await service.submit_content(user_id=1, content_type="post", content="内容1")
        await service.submit_content(user_id=2, content_type="post", content="内容2")

        stats = await service.get_moderation_stats()

        assert stats["total_content"] == 2


class TestSingletonService:
    """单例服务测试"""

    def test_content_moderation_service_singleton(self):
        """测试内容审核服务单例"""
        assert content_moderation_service is not None
        assert isinstance(content_moderation_service, ContentModerationService)
