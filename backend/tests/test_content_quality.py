"""内容质量评分体系服务测试"""
from __future__ import annotations

import pytest

from app.services.content_quality import (
    UserVotingSystem,
    AIQualityEvaluator,
    ContentQualityScoringService,
    content_quality_service,
    rate_content,
    get_quality_score,
)


class TestUserVotingSystem:
    """用户投票系统测试"""

    def test_vote_up(self):
        """测试投票（赞成）"""
        voting = UserVotingSystem()
        result = voting.vote(
            content_id="content1",
            user_id=1,
            vote_type="up",
        )

        assert result["content_id"] == "content1"
        assert result["vote_type"] == "up"
        assert result["total_up"] == 1
        assert result["total_down"] == 0

    def test_vote_down(self):
        """测试投票（反对）"""
        voting = UserVotingSystem()
        result = voting.vote(
            content_id="content1",
            user_id=1,
            vote_type="down",
        )

        assert result["content_id"] == "content1"
        assert result["vote_type"] == "down"
        assert result["total_up"] == 0
        assert result["total_down"] == 1

    def test_vote_change(self):
        """测试更改投票"""
        voting = UserVotingSystem()
        voting.vote("content1", 1, "up")
        result = voting.vote("content1", 1, "down")

        assert result["vote_type"] == "down"
        assert result["total_up"] == 0
        assert result["total_down"] == 1

    def test_vote_multiple_users(self):
        """测试多用户投票"""
        voting = UserVotingSystem()
        voting.vote("content1", 1, "up")
        voting.vote("content1", 2, "up")
        voting.vote("content1", 3, "down")

        result = voting.vote("content1", 4, "up")

        assert result["total_up"] == 3
        assert result["total_down"] == 1

    def test_get_vote_stats(self):
        """测试获取投票统计"""
        voting = UserVotingSystem()
        voting.vote("content1", 1, "up")
        voting.vote("content1", 2, "up")
        voting.vote("content1", 3, "down")

        stats = voting.get_vote_stats("content1")

        assert stats["up"] == 2
        assert stats["down"] == 1
        assert stats["score"] == 1

    def test_get_vote_stats_not_found(self):
        """测试获取不存在的投票统计"""
        voting = UserVotingSystem()
        stats = voting.get_vote_stats("nonexistent")

        assert stats["up"] == 0
        assert stats["down"] == 0
        assert stats["score"] == 0


class TestAIQualityEvaluator:
    """AI 质量评估器测试"""

    def test_evaluate_content_short(self):
        """测试评估内容（短文本）"""
        evaluator = AIQualityEvaluator()
        result = evaluator.evaluate_content(
            content_id="content1",
            content_text="短文本",
            category="general",
        )

        assert result["content_id"] == "content1"
        assert result["total_score"] < 70
        assert result["quality_level"] in ["poor", "average"]

    def test_evaluate_content_long(self):
        """测试评估内容（长文本）"""
        evaluator = AIQualityEvaluator()
        long_text = "这是一段很长的文本。" * 100
        result = evaluator.evaluate_content(
            content_id="content1",
            content_text=long_text,
            category="general",
        )

        assert result["content_id"] == "content1"
        assert result["total_score"] >= 90
        assert result["quality_level"] == "excellent"

    def test_evaluate_content_medium(self):
        """测试评估内容（中等长度）"""
        evaluator = AIQualityEvaluator()
        medium_text = "这是一段中等长度的文本。" * 10
        result = evaluator.evaluate_content(
            content_id="content1",
            content_text=medium_text,
            category="general",
        )

        assert result["content_id"] == "content1"
        assert 50 <= result["total_score"] < 90
        assert result["quality_level"] in ["good", "average"]

    def test_get_evaluation(self):
        """测试获取评估结果"""
        evaluator = AIQualityEvaluator()
        evaluator.evaluate_content(
            content_id="content1",
            content_text="测试文本",
            category="general",
        )

        result = evaluator.get_evaluation("content1")

        assert result["content_id"] == "content1"
        assert "total_score" in result
        assert "quality_level" in result

    def test_get_evaluation_not_found(self):
        """测试获取不存在的评估结果"""
        evaluator = AIQualityEvaluator()
        result = evaluator.get_evaluation("nonexistent")

        assert result["content_id"] == "nonexistent"
        assert result["total_score"] == 0
        assert result["quality_level"] == "unknown"


class TestContentQualityScoringService:
    """内容质量评分服务测试"""

    @pytest.mark.asyncio
    async def test_rate_content_with_vote(self):
        """测试评价内容（带投票）"""
        service = ContentQualityScoringService()
        result = await service.rate_content(
            content_id="content1",
            user_id=1,
            content_text="这是一段测试文本。",
            category="general",
            vote_type="up",
        )

        assert result["content_id"] == "content1"
        assert "ai_score" in result
        assert "ai_level" in result
        assert "vote_stats" in result
        assert "combined_score" in result

    @pytest.mark.asyncio
    async def test_rate_content_without_vote(self):
        """测试评价内容（无投票）"""
        service = ContentQualityScoringService()
        result = await service.rate_content(
            content_id="content1",
            user_id=1,
            content_text="这是一段测试文本。",
            category="general",
        )

        assert result["content_id"] == "content1"
        assert result["vote_stats"]["up"] == 0
        assert result["vote_stats"]["down"] == 0

    @pytest.mark.asyncio
    async def test_get_quality_score(self):
        """测试获取质量评分"""
        service = ContentQualityScoringService()
        await service.rate_content(
            content_id="content1",
            user_id=1,
            content_text="测试文本",
            category="general",
            vote_type="up",
        )

        score = await service.get_quality_score("content1")

        assert score["content_id"] == "content1"
        assert "vote_score" in score
        assert "ai_score" in score
        assert "quality_level" in score

    @pytest.mark.asyncio
    async def test_get_top_rated_content(self):
        """测试获取高评分内容"""
        service = ContentQualityScoringService()
        await service.rate_content(
            content_id="content1",
            user_id=1,
            content_text="这是一段很长的文本。" * 100,
            category="general",
            vote_type="up",
        )
        await service.rate_content(
            content_id="content2",
            user_id=2,
            content_text="短文本",
            category="general",
            vote_type="down",
        )

        top_content = await service.get_top_rated_content(limit=10)

        assert len(top_content) == 2
        assert top_content[0]["combined_score"] >= top_content[1]["combined_score"]

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计信息"""
        service = ContentQualityScoringService()
        await service.rate_content(
            content_id="content1",
            user_id=1,
            content_text="这是一段很长的文本。" * 100,
            category="general",
            vote_type="up",
        )
        await service.rate_content(
            content_id="content2",
            user_id=2,
            content_text="短文本",
            category="general",
            vote_type="down",
        )

        stats = await service.get_stats()

        assert stats["total_content"] == 2
        assert "quality_distribution" in stats
        assert "total_votes" in stats


class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_rate_content_function(self):
        """测试评价内容便捷函数"""
        result = await rate_content(
            content_id="content1",
            user_id=1,
            content_text="测试文本",
            category="general",
            vote_type="up",
        )

        assert result["content_id"] == "content1"
        assert "combined_score" in result

    @pytest.mark.asyncio
    async def test_get_quality_score_function(self):
        """测试获取质量评分便捷函数"""
        await rate_content(
            content_id="content1",
            user_id=1,
            content_text="测试文本",
            category="general",
            vote_type="up",
        )

        score = await get_quality_score("content1")

        assert score["content_id"] == "content1"
        assert "vote_score" in score


class TestSingletonService:
    """单例服务测试"""

    def test_content_quality_service_singleton(self):
        """测试内容质量服务单例"""
        assert content_quality_service is not None
        assert isinstance(content_quality_service, ContentQualityScoringService)
