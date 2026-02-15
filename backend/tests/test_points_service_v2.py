"""积分体系 2.0 增强服务测试

覆盖 points_service_v2.py 的所有功能，目标覆盖率 100%
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone, timedelta

from app.services.points.points_service_v2 import (
    PointsRuleManager,
    PointsChainValidator,
    PointsAnalytics,
    EnhancedPointsService,
    enhanced_points_service,
    award_points_v2,
    redeem_points_v2,
    get_points_balance_v2,
    get_points_rules_v2,
    get_points_analytics_v2,
)


class TestPointsRuleManager:
    """积分规则管理器测试"""

    def test_init(self):
        """测试初始化"""
        manager = PointsRuleManager()
        assert manager._rules is not None
        assert manager._custom_rules == {}

    def test_add_custom_rule_new(self):
        """测试添加新规则"""
        manager = PointsRuleManager()
        success = manager.add_custom_rule(
            action="new_action",
            points=100,
            max_daily=5,
            description="New rule",
            vip_multiplier=1.5,
            requires_auth=True,
        )
        assert success is True
        assert "new_action" in manager._custom_rules
        assert manager._custom_rules["new_action"]["points"] == 100

    def test_add_custom_rule_existing(self):
        """测试更新已存在的规则"""
        manager = PointsRuleManager()
        manager.add_custom_rule("existing", 50)
        # 添加同名规则应该更新
        success = manager.add_custom_rule("existing", 100)
        assert success is True
        assert manager._custom_rules["existing"]["points"] == 100

    def test_add_custom_rule_existing_builtin(self):
        """测试添加与内置规则同名的自定义规则"""
        manager = PointsRuleManager()
        # 添加一个与内置规则同名的自定义规则
        # 这会触发第48行的 logger.warning
        # 使用 daily_signin 因为它确实存在于内置规则中
        success = manager.add_custom_rule("daily_signin", 200)
        assert success is True
        assert manager._custom_rules["daily_signin"]["points"] == 200

    def test_remove_custom_rule_success(self):
        """测试成功移除自定义规则"""
        manager = PointsRuleManager()
        manager.add_custom_rule("to_remove", 100)
        success = manager.remove_custom_rule("to_remove")
        assert success is True
        assert "to_remove" not in manager._custom_rules

    def test_remove_custom_rule_not_found(self):
        """测试移除不存在的规则"""
        manager = PointsRuleManager()
        success = manager.remove_custom_rule("non_existent")
        assert success is False

    def test_get_all_rules(self):
        """测试获取所有规则"""
        manager = PointsRuleManager()
        manager.add_custom_rule("custom1", 100)
        manager.add_custom_rule("custom2", 200)

        rules = manager.get_all_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0

        # 检查自定义规则标记
        custom_rules = [r for r in rules if r["action"] in ["custom1", "custom2"]]
        assert all(r["is_custom"] for r in custom_rules)

    def test_get_rule_found(self):
        """测试获取存在的规则"""
        manager = PointsRuleManager()
        manager.add_custom_rule("test_rule", 150)

        rule = manager.get_rule("test_rule")
        assert rule is not None
        assert rule["action"] == "test_rule"
        assert rule["points"] == 150
        assert rule["is_custom"] is True

    def test_get_rule_builtin(self):
        """测试获取内置规则（非自定义）"""
        manager = PointsRuleManager()
        # 获取内置规则
        rule = manager.get_rule("daily_signin")
        assert rule is not None
        assert rule["action"] == "daily_signin"
        assert rule["is_custom"] is False

    def test_get_rule_not_found(self):
        """测试获取不存在的规则"""
        manager = PointsRuleManager()
        rule = manager.get_rule("non_existent")
        assert rule is None

    def test_validate_rule_valid(self):
        """测试验证有效规则"""
        manager = PointsRuleManager()
        manager.add_custom_rule("valid_rule", 100, max_daily=50)

        valid, msg = manager.validate_rule("valid_rule", 30)
        assert valid is True
        assert msg == ""

    def test_validate_rule_builtin_valid(self):
        """测试验证内置规则（非自定义）"""
        manager = PointsRuleManager()
        # 验证内置规则
        valid, msg = manager.validate_rule("daily_signin", 1)
        assert valid is True
        assert msg == ""

    def test_validate_rule_builtin_exceeds_max(self):
        """测试验证内置规则超过上限"""
        manager = PointsRuleManager()
        # 验证内置规则超过上限
        valid, msg = manager.validate_rule("daily_signin", 100)
        assert valid is False
        assert "超过每日上限" in msg

    def test_validate_rule_builtin_zero_points(self):
        """测试验证内置规则零积分"""
        manager = PointsRuleManager()
        # 验证内置规则零积分，这会覆盖第159行
        valid, msg = manager.validate_rule("daily_signin", 0)
        assert valid is False
        assert "大于 0" in msg

    def test_validate_rule_builtin_negative_points(self):
        """测试验证内置规则负积分"""
        manager = PointsRuleManager()
        # 验证内置规则负积分
        valid, msg = manager.validate_rule("daily_signin", -10)
        assert valid is False
        assert "大于 0" in msg

    def test_validate_rule_unknown_action(self):
        """测试验证未知动作"""
        manager = PointsRuleManager()
        valid, msg = manager.validate_rule("unknown", 10)
        assert valid is False
        assert "未知的积分动作" in msg

    def test_validate_rule_exceeds_max_daily(self):
        """测试验证超过每日上限"""
        manager = PointsRuleManager()
        manager.add_custom_rule("limit_rule", 100, max_daily=10)

        valid, msg = manager.validate_rule("limit_rule", 20)
        assert valid is False
        assert "超过每日上限" in msg

    def test_validate_rule_zero_points(self):
        """测试验证零积分"""
        manager = PointsRuleManager()
        manager.add_custom_rule("zero_rule", 100)

        valid, msg = manager.validate_rule("zero_rule", 0)
        assert valid is False
        assert "大于 0" in msg

    def test_validate_rule_negative_points(self):
        """测试验证负积分"""
        manager = PointsRuleManager()
        manager.add_custom_rule("negative_rule", 100)

        valid, msg = manager.validate_rule("negative_rule", -10)
        assert valid is False
        assert "大于 0" in msg


class TestPointsChainValidator:
    """积分链路验证器测试"""

    def test_init(self):
        """测试初始化"""
        validator = PointsChainValidator()
        assert validator._chain_configs == {}
        assert validator._chain_results == {}

    def test_add_chain_config(self):
        """测试添加链路配置"""
        validator = PointsChainValidator()
        validator.add_chain_config(
            chain_name="test_chain",
            actions=["step1", "step2", "step3"],
            required_actions=["step1", "step2"],
            bonus_points=50,
        )
        assert "test_chain" in validator._chain_configs
        config = validator._chain_configs["test_chain"]
        assert config["bonus_points"] == 50

    def test_validate_chain_unknown(self):
        """测试验证未知链路"""
        validator = PointsChainValidator()
        result = validator.validate_chain(1, "unknown", [])
        assert result["valid"] is False
        assert "未知的链路" in result["error"]

    def test_validate_chain_incomplete(self):
        """测试验证不完整链路"""
        validator = PointsChainValidator()
        validator.add_chain_config(
            chain_name="incomplete_chain",
            actions=["step1", "step2", "step3"],
            required_actions=["step1", "step2"],
            bonus_points=50,
        )

        result = validator.validate_chain(1, "incomplete_chain", ["step1"])
        assert result["valid"] is False
        assert "step2" in result["missing"]
        assert result["progress"] == "1/2"

    def test_validate_chain_complete_with_bonus(self):
        """测试验证完整链路（有奖励）"""
        validator = PointsChainValidator()
        validator.add_chain_config(
            chain_name="bonus_chain",
            actions=["step1", "step2"],
            required_actions=["step1", "step2"],
            bonus_points=100,
        )

        result = validator.validate_chain(1, "bonus_chain", ["step1", "step2"])
        assert result["valid"] is True
        assert result["bonus_points"] == 100
        assert "恭喜完成" in result["message"]

    def test_validate_chain_complete_no_bonus(self):
        """测试验证完整链路（无奖励）"""
        validator = PointsChainValidator()
        validator.add_chain_config(
            chain_name="no_bonus_chain",
            actions=["step1", "step2"],
            required_actions=["step1", "step2"],
            bonus_points=0,
        )

        result = validator.validate_chain(1, "no_bonus_chain", ["step1", "step2"])
        assert result["valid"] is True
        assert result["bonus_points"] == 0
        assert "恭喜完成" in result["message"]

    def test_get_chain_status_found(self):
        """测试获取存在的链路状态"""
        validator = PointsChainValidator()
        validator.add_chain_config(
            chain_name="status_chain",
            actions=["step1", "step2"],
            required_actions=["step1"],
            bonus_points=30,
        )

        status = validator.get_chain_status(1, "status_chain")
        assert status["chain_name"] == "status_chain"
        assert status["required_actions"] == ["step1"]
        assert status["bonus_points"] == 30

    def test_get_chain_status_not_found(self):
        """测试获取不存在的链路状态"""
        validator = PointsChainValidator()
        status = validator.get_chain_status(1, "unknown_chain")
        assert "error" in status
        assert "未知的链路" in status["error"]


class TestPointsAnalytics:
    """积分数据分析测试"""

    def test_init(self):
        """测试初始化"""
        analytics = PointsAnalytics()
        assert analytics._stats == {
            "total_earned": {},
            "total_spent": {},
            "action_counts": {},
        }

    @pytest.mark.asyncio
    async def test_record_earn(self):
        """测试记录积分获取"""
        analytics = PointsAnalytics()
        await analytics.record_earn(1, "action1", 100)
        await analytics.record_earn(1, "action1", 50)
        await analytics.record_earn(1, "action2", 200)

        assert analytics._stats["action_counts"]["action1"] == 2
        assert analytics._stats["action_counts"]["action2"] == 1

    @pytest.mark.asyncio
    async def test_record_spend(self):
        """测试记录积分消耗"""
        analytics = PointsAnalytics()
        await analytics.record_spend(1, 100)
        await analytics.record_spend(1, 50)

        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert analytics._stats["total_spent"][date] == 150

    @pytest.mark.asyncio
    async def test_get_daily_stats(self):
        """测试获取每日统计"""
        analytics = PointsAnalytics()
        await analytics.record_earn(1, "action1", 100)
        await analytics.record_spend(1, 50)

        stats = analytics.get_daily_stats(days=7)
        assert stats["period_days"] == 7
        assert stats["total_earned"] == 100
        assert stats["total_spent"] == 50
        assert len(stats["daily_data"]) == 8  # 7 days + 1 for today

    @pytest.mark.asyncio
    async def test_get_daily_stats_net(self):
        """测试每日统计的净积分"""
        analytics = PointsAnalytics()
        await analytics.record_earn(1, "action1", 200)
        await analytics.record_spend(1, 50)

        stats = analytics.get_daily_stats(days=1)
        today_data = stats["daily_data"][-1]
        assert today_data["net"] == 150

    @pytest.mark.asyncio
    async def test_get_action_stats(self):
        """测试获取动作统计"""
        analytics = PointsAnalytics()
        await analytics.record_earn(1, "action1", 100)
        await analytics.record_earn(1, "action1", 100)
        await analytics.record_earn(1, "action2", 50)

        stats = analytics.get_action_stats()
        assert stats["total_actions"] == 3
        assert stats["action_counts"]["action1"] == 2
        assert stats["action_counts"]["action2"] == 1

    @pytest.mark.asyncio
    async def test_get_action_stats_sorted(self):
        """测试动作统计按次数排序"""
        analytics = PointsAnalytics()
        await analytics.record_earn(1, "action3", 10)
        await analytics.record_earn(1, "action1", 10)
        await analytics.record_earn(1, "action1", 10)
        await analytics.record_earn(1, "action2", 10)
        await analytics.record_earn(1, "action2", 10)
        await analytics.record_earn(1, "action2", 10)

        stats = analytics.get_action_stats()
        counts = list(stats["action_counts"].values())
        assert counts == [3, 2, 1]  # 降序排列


class TestEnhancedPointsService:
    """增强积分服务测试"""

    def test_init(self):
        """测试初始化"""
        service = EnhancedPointsService()
        assert service.rule_manager is not None
        assert service.chain_validator is not None
        assert service.analytics is not None
        assert service._base_service is not None

    @pytest.mark.asyncio
    async def test_award_points_success(self):
        """测试成功奖励积分"""
        service = EnhancedPointsService()
        service._base_service = AsyncMock()
        service._base_service.award_points.return_value = (10, None)

        result = await service.award_points(1, "test_action", "Test description")

        assert result["success"] is True
        assert result["points"] == 10
        assert result["error"] is None
        service._base_service.award_points.assert_called_once()

    @pytest.mark.asyncio
    async def test_award_points_error(self):
        """测试奖励积分失败"""
        service = EnhancedPointsService()
        service._base_service = AsyncMock()
        service._base_service.award_points.return_value = (0, "Error occurred")

        result = await service.award_points(1, "test_action")

        assert result["success"] is False
        assert result["points"] == 0
        assert result["error"] == "Error occurred"

    @pytest.mark.asyncio
    async def test_award_points_with_metadata(self):
        """测试带元数据奖励积分"""
        service = EnhancedPointsService()
        service._base_service = AsyncMock()
        service._base_service.award_points.return_value = (20, None)

        metadata = {"source": "test", "extra": "data"}
        result = await service.award_points(
            1, "test_action", "Test", metadata
        )

        assert result["success"] is True
        assert result["points"] == 20

    @pytest.mark.asyncio
    async def test_redeem_points_success(self):
        """测试成功消耗积分"""
        service = EnhancedPointsService()
        service._base_service = AsyncMock()
        service._base_service.redeem_points.return_value = (True, None)

        result = await service.redeem_points(1, 100, "prod_1", "Test product")

        assert result["success"] is True
        assert result["error"] is None
        service._base_service.redeem_points.assert_called_once()

    @pytest.mark.asyncio
    async def test_redeem_points_failure(self):
        """测试消耗积分失败"""
        service = EnhancedPointsService()
        service._base_service = AsyncMock()
        service._base_service.redeem_points.return_value = (False, "Insufficient points")

        result = await service.redeem_points(1, 100, "prod_1", "Test product")

        assert result["success"] is False
        assert result["error"] == "Insufficient points"

    def test_get_balance(self):
        """测试获取积分余额"""
        service = EnhancedPointsService()
        service._base_service = Mock()
        service._base_service.get_balance.return_value = 500
        service._base_service.get_continuous_days.return_value = 7

        result = service.get_balance(1)

        assert result["user_id"] == 1
        assert result["balance"] == 500
        assert result["continuous_days"] == 7

    def test_get_rules(self):
        """测试获取积分规则"""
        service = EnhancedPointsService()
        rules = service.get_rules()

        assert isinstance(rules, list)
        assert len(rules) > 0

    def test_get_analytics(self):
        """测试获取分析数据"""
        service = EnhancedPointsService()
        analytics = service.get_analytics(days=7)

        assert "daily_stats" in analytics
        assert "action_stats" in analytics
        assert analytics["daily_stats"]["period_days"] == 7


class TestSingleton:
    """单例测试"""

    def test_enhanced_points_service_singleton(self):
        """测试增强积分服务单例"""
        assert enhanced_points_service is not None
        assert isinstance(enhanced_points_service, EnhancedPointsService)


class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_award_points_v2(self):
        """测试 award_points_v2 便捷函数"""
        with patch.object(
            enhanced_points_service, "award_points", new_callable=AsyncMock
        ) as mock_award:
            mock_award.return_value = {"success": True, "points": 10, "error": None}

            result = await award_points_v2(1, "test_action", "Test", {"key": "value"})

            assert result["success"] is True
            mock_award.assert_called_once_with(
                user_id=1,
                action="test_action",
                description="Test",
                metadata={"key": "value"},
            )

    @pytest.mark.asyncio
    async def test_redeem_points_v2(self):
        """测试 redeem_points_v2 便捷函数"""
        with patch.object(
            enhanced_points_service, "redeem_points", new_callable=AsyncMock
        ) as mock_redeem:
            mock_redeem.return_value = {"success": True, "error": None}

            result = await redeem_points_v2(1, 100, "prod_1", "Test product")

            assert result["success"] is True
            mock_redeem.assert_called_once_with(
                user_id=1, points=100, product_id="prod_1", description="Test product"
            )

    def test_get_points_balance_v2(self):
        """测试 get_points_balance_v2 便捷函数"""
        with patch.object(
            enhanced_points_service, "get_balance", return_value={"balance": 500}
        ) as mock_get:
            result = get_points_balance_v2(1)

            assert result["balance"] == 500
            mock_get.assert_called_once_with(1)

    def test_get_points_rules_v2(self):
        """测试 get_points_rules_v2 便捷函数"""
        with patch.object(
            enhanced_points_service, "get_rules", return_value=[{"action": "test"}]
        ) as mock_get:
            result = get_points_rules_v2()

            assert len(result) == 1
            mock_get.assert_called_once()

    def test_get_points_analytics_v2(self):
        """测试 get_points_analytics_v2 便捷函数"""
        with patch.object(
            enhanced_points_service,
            "get_analytics",
            return_value={"daily_stats": {}, "action_stats": {}},
        ) as mock_get:
            result = get_points_analytics_v2(days=14)

            assert "daily_stats" in result
            mock_get.assert_called_once_with(14)
