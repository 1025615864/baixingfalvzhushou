import pytest
from datetime import datetime, timezone
from app.services.ugc_incentive import (
    ContentContributionTracker,
    IncentiveConfigurator,
    UGCIncentiveService,
    reset_ugc_incentive_service,
)


class TestContentContributionTracker:
    """测试内容贡献追踪器"""

    def setup_method(self):
        """每个测试前初始化"""
        # 重置全局单例状态，确保测试隔离
        reset_ugc_incentive_service()
        self.tracker = ContentContributionTracker()

    def test_record_contribution_new_user(self):
        """测试新用户贡献记录"""
        result = self.tracker.record_contribution(
            user_id=1,
            content_type="article",
            content_id="art-001",
            quality_score=0.8,
        )

        assert result["user_id"] == 1
        assert result["content_type"] == "article"
        assert result["total_contributions"] == 1
        assert result["average_quality"] == 0.8

    def test_record_contribution_existing_user(self):
        """测试现有用户贡献记录"""
        self.tracker.record_contribution(
            user_id=1, content_type="article", content_id="art-001"
        )
        self.tracker.record_contribution(
            user_id=1, content_type="comment", content_id="com-001", quality_score=0.6
        )

        result = self.tracker.record_contribution(
            user_id=1, content_type="article", content_id="art-002", quality_score=0.9
        )

        assert result["total_contributions"] == 3
        assert result["average_quality"] == 0.67  # (0.5 + 0.6 + 0.9) / 3 = 0.666...

    def test_get_user_contributions_no_contributions(self):
        """测试获取无贡献用户数据"""
        result = self.tracker.get_user_contributions(user_id=999)

        assert result["user_id"] == 999
        assert result["total_contributions"] == 0
        assert result["content_types"] == {}
        assert result["average_quality"] == 0

    def test_get_user_contributions_with_data(self):
        """测试获取有贡献用户数据"""
        self.tracker.record_contribution(
            user_id=1, content_type="article", content_id="art-001", quality_score=0.8
        )
        self.tracker.record_contribution(
            user_id=1, content_type="comment", content_id="com-001", quality_score=0.7
        )

        result = self.tracker.get_user_contributions(user_id=1)

        assert result["total_contributions"] == 2
        assert "article" in result["content_types"]
        assert "comment" in result["content_types"]
        assert result["content_types"]["article"]["count"] == 1
        assert result["content_types"]["comment"]["count"] == 1

    def test_get_leaderboard_empty(self):
        """测试空排行榜"""
        result = self.tracker.get_leaderboard()
        assert result == []

    def test_get_leaderboard_with_data(self):
        """测试排行榜排序"""
        self.tracker.record_contribution(
            user_id=1, content_type="article", content_id="art-001"
        )
        self.tracker.record_contribution(
            user_id=2, content_type="article", content_id="art-002"
        )
        self.tracker.record_contribution(
            user_id=2, content_type="comment", content_id="com-001"
        )

        result = self.tracker.get_leaderboard(limit=10)

        assert len(result) == 2
        assert result[0]["rank"] == 1
        assert result[0]["user_id"] == 2  # 2条贡献 > 1条贡献
        assert result[1]["rank"] == 2
        assert result[1]["user_id"] == 1

    def test_get_leaderboard_limit(self):
        """测试排行榜数量限制"""
        for i in range(15):
            self.tracker.record_contribution(
                user_id=i, content_type="article", content_id=f"art-{i}"
            )

        result = self.tracker.get_leaderboard(limit=5)
        assert len(result) == 5


class TestIncentiveConfigurator:
    """测试激励配置器"""

    def setup_method(self):
        """每个测试前初始化"""
        # 重置全局单例状态，确保测试隔离
        reset_ugc_incentive_service()
        self.configurator = IncentiveConfigurator()

    def test_configure_incentive_basic(self):
        """测试基础激励配置"""
        result = self.configurator.configure_incentive(
            incentive_type="article", points_per_unit=20
        )

        assert result["type"] == "article"
        assert result["points_per_unit"] == 20
        assert result["configured"] is True

    def test_configure_incentive_with_bonus(self):
        """测试带奖励的激励配置"""
        result = self.configurator.configure_incentive(
            incentive_type="comment",
            points_per_unit=5,
            bonus_threshold=10,
            bonus_multiplier=1.5,
        )

        rules = self.configurator.get_incentive_rules()
        assert rules["comment"]["bonus_threshold"] == 10
        assert rules["comment"]["bonus_multiplier"] == 1.5

    def test_calculate_rewards_basic(self):
        """测试基础奖励计算"""
        self.configurator.configure_incentive(
            incentive_type="article", points_per_unit=20
        )

        result = self.configurator.calculate_rewards(
            user_id=1, contributions={"article": 3}
        )

        assert result["user_id"] == 1
        assert result["total_points"] == 60  # 3 * 20
        assert "article" in result["breakdown"]
        assert result["breakdown"]["article"]["count"] == 3
        assert result["breakdown"]["article"]["base_points"] == 60
        assert result["breakdown"]["article"]["bonus_points"] == 0

    def test_calculate_rewards_with_bonus(self):
        """测试带奖励阈值的奖励计算"""
        self.configurator.configure_incentive(
            incentive_type="comment",
            points_per_unit=5,
            bonus_threshold=10,
            bonus_multiplier=1.5,
        )

        result = self.configurator.calculate_rewards(
            user_id=1, contributions={"comment": 12}
        )

        # 12 * 5 = 60, 达到阈值(10)，触发1.5倍奖励
        # 60 * 1.5 = 90
        assert result["total_points"] == 90
        assert result["breakdown"]["comment"]["bonus_points"] == 30  # 90 - 60

    def test_calculate_rewards_default_points(self):
        """测试默认积分计算"""
        result = self.configurator.calculate_rewards(
            user_id=1, contributions={"unknown_type": 5}
        )

        # 未配置的类型使用默认10积分
        assert result["total_points"] == 50

    def test_get_incentive_rules(self):
        """测试获取激励规则"""
        self.configurator.configure_incentive(
            incentive_type="article", points_per_unit=20
        )
        self.configurator.configure_incentive(
            incentive_type="comment", points_per_unit=5
        )

        rules = self.configurator.get_incentive_rules()
        assert len(rules) == 2
        assert "article" in rules
        assert "comment" in rules


class TestUGCIncentiveService:
    """测试UGC激励服务"""

    def setup_method(self):
        """每个测试前初始化"""
        # 重置全局单例状态，确保测试隔离
        reset_ugc_incentive_service()
        self.service = UGCIncentiveService()

    @pytest.mark.asyncio
    async def test_record_content(self):
        """测试记录内容"""
        result = await self.service.record_content(
            user_id=1, content_type="article", content_id="art-001", quality_score=0.8
        )

        assert result["user_id"] == 1
        assert result["content_type"] == "article"
        assert result["total_contributions"] == 1
        assert result["rewards"]["total_points"] > 0

    @pytest.mark.asyncio
    async def test_get_user_stats(self):
        """测试获取用户统计"""
        await self.service.record_content(
            user_id=1, content_type="article", content_id="art-001"
        )
        await self.service.record_content(
            user_id=1, content_type="comment", content_id="com-001"
        )

        result = await self.service.get_user_stats(user_id=1)

        assert result["user_id"] == 1
        assert result["contributions"]["total_contributions"] == 2
        assert result["total_points"] > 0
        assert "incentive_rules" in result

    @pytest.mark.asyncio
    async def test_get_leaderboard(self):
        """测试获取排行榜"""
        await self.service.record_content(
            user_id=1, content_type="article", content_id="art-001"
        )
        await self.service.record_content(
            user_id=2, content_type="article", content_id="art-002"
        )
        await self.service.record_content(
            user_id=2, content_type="comment", content_id="com-001"
        )

        result = await self.service.get_leaderboard(limit=10)

        assert len(result) == 2
        assert result[0]["user_id"] == 2  # 更多贡献

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取服务统计"""
        await self.service.record_content(
            user_id=1, content_type="article", content_id="art-001"
        )
        await self.service.record_content(
            user_id=2, content_type="article", content_id="art-002"
        )

        result = await self.service.get_stats()

        assert result["total_users"] == 2
        assert result["total_contributions"] == 2
        assert result["incentive_rules_count"] > 0
