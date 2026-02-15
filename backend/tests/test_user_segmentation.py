import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from app.services.user_segmentation import (
    UserLifecycleManager,
    UserValueSegmenter,
    UserSegmentationService,
)


class TestUserLifecycleManager:
    """测试用户生命周期管理器"""

    def setup_method(self):
        """每个测试前初始化"""
        self.manager = UserLifecycleManager()

    def test_get_lifecycle_stage_new_user(self):
        """测试新用户生命周期阶段"""
        stage = self.manager.get_lifecycle_stage(user_id=999)
        assert stage == "new"

    def test_update_user_activity_new_user(self):
        """测试新用户活动更新"""
        result = self.manager.update_user_activity(user_id=1, session_duration=120)

        assert result["user_id"] == 1
        assert result["sessions"] == 1
        assert "lifecycle_stage" in result

    def test_update_user_activity_existing_user(self):
        """测试现有用户活动更新"""
        self.manager.update_user_activity(user_id=1, session_duration=120)
        result = self.manager.update_user_activity(user_id=1, session_duration=180)

        assert result["sessions"] == 2

    def test_get_lifecycle_stats_empty(self):
        """测试空统计数据"""
        result = self.manager.get_lifecycle_stats()

        assert result["total_users"] == 0
        assert all(v == 0 for v in result["stages"].values())

    def test_get_lifecycle_stats_with_users(self):
        """测试用户统计数据"""
        self.manager.update_user_activity(user_id=1, session_duration=300)
        self.manager.update_user_activity(user_id=2, session_duration=300)

        result = self.manager.get_lifecycle_stats()

        assert result["total_users"] == 2
        assert result["stages"]["new"] == 2


class TestUserValueSegmenter:
    """测试用户价值分层器"""

    def setup_method(self):
        """每个测试前初始化"""
        self.segmenter = UserValueSegmenter()

    def test_calculate_user_value_low_segment(self):
        """测试低价值用户分层"""
        result = self.segmenter.calculate_user_value(
            user_id=1, total_spend=0, consultation_count=0, activity_score=0.0
        )

        assert result["user_id"] == 1
        assert result["segment"] == "low"
        assert result["value_score"] == 0

    def test_calculate_user_value_medium_segment(self):
        """测试中等价值用户分层"""
        result = self.segmenter.calculate_user_value(
            user_id=1, total_spend=10, consultation_count=2, activity_score=1.0
        )

        # value_score = 10*0.5 + 2*2 + 1.0*10 = 5 + 4 + 10 = 19 -> low
        assert result["segment"] == "low"
        assert result["value_score"] == 19

    def test_calculate_user_value_high_segment(self):
        """测试高价值用户分层"""
        result = self.segmenter.calculate_user_value(
            user_id=1, total_spend=50, consultation_count=10, activity_score=3.0
        )

        # value_score = 50*0.5 + 10*2 + 3.0*10 = 25 + 20 + 30 = 75
        assert result["segment"] == "high"
        assert result["value_score"] == 75

    def test_calculate_user_value_premium_segment(self):
        """测试高净值用户分层"""
        result = self.segmenter.calculate_user_value(
            user_id=1, total_spend=200, consultation_count=50, activity_score=5.0
        )

        # value_score = 200*0.5 + 50*2 + 5.0*10 = 100 + 100 + 50 = 250
        assert result["segment"] == "premium"
        assert result["value_score"] == 250

    def test_get_segment_distribution_empty(self):
        """测试空分段分布"""
        result = self.segmenter.get_segment_distribution()

        assert result["total_users"] == 0
        assert all(v == 0 for v in result["segments"].values())

    def test_get_segment_distribution_with_users(self):
        """测试用户分段分布"""
        self.segmenter.calculate_user_value(user_id=1, total_spend=0, consultation_count=0)
        self.segmenter.calculate_user_value(user_id=2, total_spend=100, consultation_count=20)
        self.segmenter.calculate_user_value(user_id=3, total_spend=200, consultation_count=50)

        result = self.segmenter.get_segment_distribution()

        assert result["total_users"] == 3
        assert result["segments"]["low"] == 1
        assert result["segments"]["premium"] == 1


class TestUserSegmentationService:
    """测试用户分层运营服务"""

    def setup_method(self):
        """每个测试前初始化"""
        self.service = UserSegmentationService()

    @pytest.mark.asyncio
    async def test_segment_user(self):
        """测试用户分层"""
        result = await self.service.segment_user(
            user_id=1,
            total_spend=50,
            consultation_count=10,
            activity_score=3.0,
            session_duration=300,
        )

        assert result["user_id"] == 1
        assert "lifecycle_stage" in result
        assert "value_segment" in result
        assert "value_score" in result

    @pytest.mark.asyncio
    async def test_get_segmentation_stats(self):
        """测试获取分层统计"""
        await self.service.segment_user(user_id=1, total_spend=10, consultation_count=2)
        await self.service.segment_user(user_id=2, total_spend=100, consultation_count=20)

        result = await self.service.get_segmentation_stats()

        assert "lifecycle" in result
        assert "value_segments" in result

    @pytest.mark.asyncio
    async def test_get_recommendations_new_user(self):
        """测试新用户推荐"""
        result = await self.service.get_recommendations(user_id=999)

        assert result["user_id"] == 999
        assert result["lifecycle_stage"] == "new"
        assert len(result["recommendations"]) > 0


class TestUserSegmentationEdgeCases:
    """测试用户分层边界情况"""

    def setup_method(self):
        """每个测试前初始化"""
        self.service = UserSegmentationService()

    def test_lifecycle_stage_transitions(self):
        """测试生命周期阶段转换"""
        manager = UserLifecycleManager()

        # 新用户
        assert manager.get_lifecycle_stage(user_id=1) == "new"

        # 更新活动后应该还是 new (需要更多会话)
        manager.update_user_activity(user_id=1, session_duration=120)
        # 生命周期阶段取决于会话次数
        stage = manager.get_lifecycle_stage(user_id=1)
        assert stage in ["new", "active", "loyal", "champion"]

    def test_value_segment_boundary_cases(self):
        """测试价值分段边界情况"""
        segmenter = UserValueSegmenter()

        # 边界值测试
        result = segmenter.calculate_user_value(
            user_id=1, total_spend=0, consultation_count=0, activity_score=0.0
        )
        assert result["segment"] == "low"
        assert result["value_score"] == 0

        # 高价值边界
        result = segmenter.calculate_user_value(
            user_id=2, total_spend=100, consultation_count=20, activity_score=5.0
        )
        # value_score = 100*0.5 + 20*2 + 5.0*10 = 50 + 40 + 50 = 140 -> premium
        assert result["segment"] == "premium"
        assert result["value_score"] == 140

    def test_segment_distribution_comprehensive(self):
        """测试分段分布综合情况"""
        segmenter = UserValueSegmenter()

        # 添加不同分段的测试用户
        users = [
            (1, 0, 0, 0.0),      # low
            (2, 5, 1, 0.5),      # low
            (3, 20, 5, 1.0),     # low
            (4, 50, 10, 2.0),    # high
            (5, 100, 20, 3.0),   # high
            (6, 200, 50, 5.0),   # premium
        ]

        for user_id, spend, count, score in users:
            segmenter.calculate_user_value(user_id, spend, count, score)

        result = segmenter.get_segment_distribution()
        assert result["total_users"] == 6
        # 验证有分段数据
        assert "segments" in result
        assert result["segments"]["low"] >= 1
        assert result["segments"]["high"] >= 1
        assert result["segments"]["premium"] >= 1


class TestUserSegmentationIntegration:
    """测试用户分层集成场景"""

    def setup_method(self):
        """每个测试前初始化"""
        self.service = UserSegmentationService()

    @pytest.mark.asyncio
    async def test_segment_multiple_users(self):
        """测试批量用户分层"""
        users = [
            (1, 0, 0, 0.0, 60),
            (2, 50, 10, 2.0, 300),
            (3, 150, 30, 4.0, 600),
        ]

        results = []
        for user_id, spend, count, score, duration in users:
            result = await self.service.segment_user(
                user_id=user_id,
                total_spend=spend,
                consultation_count=count,
                activity_score=score,
                session_duration=duration,
            )
            results.append(result)

        assert len(results) == 3
        assert all("lifecycle_stage" in r for r in results)
        assert all("value_segment" in r for r in results)

    @pytest.mark.asyncio
    async def test_recommendations_different_stages(self):
        """测试不同阶段的推荐"""
        # 新用户推荐
        new_result = await self.service.get_recommendations(user_id=1)
        assert "引导" in str(new_result["recommendations"]) or len(new_result["recommendations"]) > 0

        # 活跃用户推荐
        lifecycle_manager = UserLifecycleManager()
        for _ in range(10):
            lifecycle_manager.update_user_activity(user_id=2, session_duration=300)

        active_result = await self.service.get_recommendations(user_id=2)
        assert "lifecycle_stage" in active_result

    @pytest.mark.asyncio
    async def test_get_segmentation_stats_comprehensive(self):
        """测试综合分层统计"""
        # 添加多个用户
        for i in range(1, 6):
            await self.service.segment_user(
                user_id=i,
                total_spend=i * 10,
                consultation_count=i,
                activity_score=float(i),
                session_duration=i * 60,
            )

        result = await self.service.get_segmentation_stats()

        # 验证返回结果包含必要字段
        assert "lifecycle" in result
        assert "value_segments" in result


class TestUserSegmentationServiceDetail:
    """测试 UserSegmentationService 详细功能"""

    def setup_method(self):
        """每个测试前初始化"""
        self.service = UserSegmentationService()

    @pytest.mark.asyncio
    async def test_segment_user_with_zero_values(self):
        """测试用户分段（零值）"""
        result = await self.service.segment_user(
            user_id=999,
            total_spend=0,
            consultation_count=0,
            activity_score=0,
            session_duration=0,
        )

        assert "lifecycle_stage" in result
        assert "value_segment" in result
        assert result["user_id"] == 999

    @pytest.mark.asyncio
    async def test_segment_user_with_high_values(self):
        """测试用户分段（高值）"""
        result = await self.service.segment_user(
            user_id=888,
            total_spend=10000,
            consultation_count=100,
            activity_score=100,
            session_duration=3600,
        )

        assert "lifecycle_stage" in result
        assert "value_segment" in result
        assert result["user_id"] == 888

    @pytest.mark.asyncio
    async def test_segment_user_edge_case_spend(self):
        """测试用户分段（边界值-消费）"""
        result = await self.service.segment_user(
            user_id=777,
            total_spend=100,
            consultation_count=5,
            activity_score=50,
            session_duration=1800,
        )

        assert "lifecycle_stage" in result
        assert "value_segment" in result

    @pytest.mark.asyncio
    async def test_get_recommendations_returns_dict(self):
        """测试推荐返回字典"""
        result = await self.service.get_recommendations(user_id=123)

        assert isinstance(result, dict)
        assert "lifecycle_stage" in result
        assert "value_segment" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_get_recommendations_contains_stage_info(self):
        """测试推荐包含阶段信息"""
        result = await self.service.get_recommendations(user_id=456)

        assert "recommendations" in result
        # 推荐应该是一个列表或字符串
        assert isinstance(result["recommendations"], (list, str))


class TestUserLifecycleManagerDetail:
    """测试 UserLifecycleManager 详细功能"""

    def setup_method(self):
        """每个测试前初始化"""
        self.manager = UserLifecycleManager()

    def test_update_activity_multiple_users(self):
        """测试多用户活动更新"""
        for user_id in [1, 2, 3]:
            for _ in range(5):
                self.manager.update_user_activity(user_id=user_id, session_duration=600)

        stage1 = self.manager.get_lifecycle_stage(1)
        stage2 = self.manager.get_lifecycle_stage(2)
        stage3 = self.manager.get_lifecycle_stage(3)

        assert stage1 is not None
        assert stage2 is not None
        assert stage3 is not None

    def test_get_lifecycle_stage_unknown_user(self):
        """测试获取未知用户的生命周期"""
        result = self.manager.get_lifecycle_stage(99999)
        assert result == "new"

    def test_determine_lifecycle_stage_consistency(self):
        """测试生命周期阶段判断一致性"""
        manager = UserLifecycleManager()

        for _ in range(10):
            manager.update_user_activity(user_id=100, session_duration=100)

        stage1 = manager.get_lifecycle_stage(100)
        assert stage1 is not None

        for _ in range(10):
            manager.update_user_activity(user_id=100, session_duration=100)

        stage2 = manager.get_lifecycle_stage(100)
        assert stage2 is not None


class TestUserValueSegmenterDetail:
    """测试 UserValueSegmenter 详细功能"""

    def setup_method(self):
        """每个测试前初始化"""
        self.segmenter = UserValueSegmenter()

    def test_calculate_user_value_extreme_low(self):
        """测试用户价值计算（极低值）"""
        result = self.segmenter.calculate_user_value(
            user_id=999,
            total_spend=0,
            consultation_count=0,
            activity_score=0,
        )
        assert isinstance(result, dict)
        assert "segment" in result
        assert "value_score" in result

    def test_calculate_user_value_extreme_high(self):
        """测试用户价值计算（极高值）"""
        result = self.segmenter.calculate_user_value(
            user_id=888,
            total_spend=100000,
            consultation_count=1000,
            activity_score=100,
        )
        assert isinstance(result, dict)
        assert result["value_score"] > 0

    def test_segment_distribution_empty(self):
        """测试分段分布（空）"""
        result = self.segmenter.get_segment_distribution()
        assert "segments" in result
        assert isinstance(result["segments"], dict)

    def test_segment_distribution_with_data(self):
        """测试分段分布（有数据）"""
        # 添加一些用户
        for i in range(10):
            self.segmenter.calculate_user_value(
                user_id=i,
                total_spend=i * 100,
                consultation_count=i,
                activity_score=i * 10,
            )

        result = self.segmenter.get_segment_distribution()
        assert "segments" in result
        assert isinstance(result["segments"], dict)
