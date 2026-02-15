import pytest
import os
import importlib.util
from unittest.mock import Mock, patch

# 使用动态导入解决模块路径问题
points_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'services', 'points.py')
spec = importlib.util.spec_from_file_location('points_module', points_file)
points_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(points_module)

PointsRuleConfig = points_module.PointsRuleConfig
PointsLedger = points_module.PointsLedger
PointsService = points_module.PointsService
earn_points = points_module.earn_points
spend_points = points_module.spend_points
get_points_balance = points_module.get_points_balance


class TestPointsRuleConfig:
    def test_register_earn_rule(self):
        config = PointsRuleConfig()
        result = config.register_earn_rule(
            rule_id="test_rule",
            action="test_action",
            points=10,
            description="Test Rule",
        )
        assert result["registered"] is True
        assert config.get_earn_rule("test_action") is not None

    def test_register_spend_rule(self):
        config = PointsRuleConfig()
        result = config.register_spend_rule(
            rule_id="test_spend",
            action="test_spend_action",
            cost_points=100,
            description="Test Spend",
        )
        assert result["registered"] is True
        assert config.get_spend_rule("test_spend_action") is not None


class TestPointsLedger:
    def test_credit_and_balance(self):
        ledger = PointsLedger()
        user_id = 1
        ledger.credit(user_id, 100, "test_action", "Test Credit")
        balance = ledger.get_balance(user_id)
        assert balance["current_balance"] == 100
        assert balance["total_earned"] == 100

    def test_debit_success(self):
        ledger = PointsLedger()
        user_id = 1
        ledger.credit(user_id, 100, "earn", "Earn")
        result = ledger.debit(user_id, 50, "spend", "Spend")
        assert result["new_balance"] == 50

    def test_debit_insufficient_funds(self):
        ledger = PointsLedger()
        user_id = 1
        ledger.credit(user_id, 10, "earn", "Earn")
        result = ledger.debit(user_id, 100, "spend", "Spend")
        assert "error" in result
        assert result["error"] == "积分不足"


@pytest.mark.asyncio
class TestPointsService:
    async def test_earn_points(self):
        service = PointsService()
        service.register_default_rules()
        
        # Test earning points with a default rule
        result = await service.earn_points(
            user_id=1,
            action="daily_signin"
        )
        assert result["success"] is True
        assert result["points_earned"] == 10

        # Test earning points with invalid action
        result = await service.earn_points(
            user_id=1,
            action="invalid_action"
        )
        assert result["success"] is False

    async def test_spend_points(self):
        service = PointsService()
        service.register_default_rules()
        
        # Earn points first
        await service.earn_points(1, "invite_register") # 50 points
        await service.earn_points(1, "invite_register") # 50 points = 100 total
        
        # Spend points
        result = await service.spend_points(
            user_id=1,
            action="consultation_discount" # costs 100
        )
        assert result["success"] is True
        
        # Verify balance
        balance = await service.get_balance(1)
        assert balance["current_balance"] == 0

    async def test_get_transactions(self):
        service = PointsService()
        service.register_default_rules()
        await service.earn_points(1, "daily_signin")
        
        txs = await service.get_transactions(1)
        assert len(txs) == 1
        assert txs[0]["action"] == "daily_signin"
