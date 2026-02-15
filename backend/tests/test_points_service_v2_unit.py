import pytest
from unittest.mock import AsyncMock, Mock
from app.services.points.points_service_v2 import (
    PointsRuleManager,
    PointsChainValidator,
    PointsAnalytics,
    EnhancedPointsService,
)

class TestPointsRuleManager:
    def test_add_remove_custom_rule(self):
        manager = PointsRuleManager()
        # Add custom rule
        success = manager.add_custom_rule(
            action="custom_action",
            points=100,
            description="Test Custom Rule"
        )
        assert success is True
        
        rule = manager.get_rule("custom_action")
        assert rule is not None
        assert rule["points"] == 100
        assert rule["is_custom"] is True

        # Remove custom rule
        success = manager.remove_custom_rule("custom_action")
        assert success is True
        assert manager.get_rule("custom_action") is None

    def test_validate_rule(self):
        manager = PointsRuleManager()
        manager.add_custom_rule("test", 10, max_daily=5)
        
        # Valid points
        valid, msg = manager.validate_rule("test", 5)
        assert valid is True
        
        # Exceeds max daily
        valid, msg = manager.validate_rule("test", 10)
        assert valid is False
        assert "上限" in msg

        # Invalid points
        valid, msg = manager.validate_rule("test", -1)
        assert valid is False
        assert "大于 0" in msg


class TestPointsChainValidator:
    def test_chain_validation(self):
        validator = PointsChainValidator()
        chain_name = "test_chain"
        required = ["step1", "step2"]
        
        validator.add_chain_config(
            chain_name=chain_name,
            actions=["step1", "step2", "step3"],
            required_actions=required,
            bonus_points=50
        )

        # Incomplete chain
        result = validator.validate_chain(1, chain_name, ["step1"])
        assert result["valid"] is False
        assert "step2" in result["missing"]

        # Complete chain
        result = validator.validate_chain(1, chain_name, ["step1", "step2"])
        assert result["valid"] is True
        assert result["bonus_points"] == 50


@pytest.mark.asyncio
class TestPointsAnalytics:
    async def test_record_stats(self):
        analytics = PointsAnalytics()
        
        await analytics.record_earn(1, "action1", 100)
        await analytics.record_spend(1, 50)
        
        stats = analytics.get_daily_stats()
        assert stats["total_earned"] == 100
        assert stats["total_spent"] == 50
        
        action_stats = analytics.get_action_stats()
        assert action_stats["action_counts"]["action1"] == 1


@pytest.mark.asyncio
class TestEnhancedPointsService:
    async def test_award_points(self):
        service = EnhancedPointsService()
        # Mock base service
        service._base_service = AsyncMock()
        service._base_service.award_points.return_value = (10, None)
        
        result = await service.award_points(1, "test_action")
        
        assert result["success"] is True
        assert result["points"] == 10
        # Verify analytics recorded
        action_stats = service.analytics.get_action_stats()
        assert action_stats["total_actions"] == 1

    async def test_redeem_points(self):
        service = EnhancedPointsService()
        # Mock base service
        service._base_service = AsyncMock()
        service._base_service.redeem_points.return_value = (True, None)
        
        result = await service.redeem_points(1, 100, "prod_1", "desc")
        
        assert result["success"] is True
        # Verify analytics recorded
        stats = service.analytics.get_daily_stats()
        assert stats["total_spent"] == 100
