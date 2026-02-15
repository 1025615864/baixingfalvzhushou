"""Tests for points service base."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.points.points_service_base import (
    PointsAction,
    PointsRule,
    POINTS_RULES,
    get_vip_multiplier,
    get_points_rule,
)


class TestPointsAction:
    """Test PointsAction enum."""

    def test_all_actions_defined(self) -> None:
        """Test that all expected actions are defined."""
        assert hasattr(PointsAction, 'DAILY_SIGNIN')
        assert hasattr(PointsAction, 'AI_CONSULTATION')
        assert hasattr(PointsAction, 'POST_CREATED')
        assert hasattr(PointsAction, 'COMMENT_CREATED')
        assert hasattr(PointsAction, 'SHARE_CONTENT')
        assert hasattr(PointsAction, 'DOCUMENT_GENERATED')
        assert hasattr(PointsAction, 'LAWYER_BOOKING')
        assert hasattr(PointsAction, 'INVITE_FRIEND')
        assert hasattr(PointsAction, 'FAVORITE_POST')
        assert hasattr(PointsAction, 'COMPLETE_PROFILE')
        assert hasattr(PointsAction, 'FIRST_QUESTION')

    def test_action_values_are_strings(self) -> None:
        """Test that action values are strings."""
        assert isinstance(PointsAction.DAILY_SIGNIN.value, str)
        assert PointsAction.DAILY_SIGNIN.value == "daily_signin"

    def test_action_is_string_enum(self) -> None:
        """Test that PointsAction is a string enum."""
        action = PointsAction.AI_CONSULTATION
        assert action == "ai_consultation"
        assert str(action) == "PointsAction.AI_CONSULTATION"


class TestPointsRule:
    """Test PointsRule dataclass."""

    def test_points_rule_creation(self) -> None:
        """Test creating PointsRule."""
        rule = PointsRule(
            action=PointsAction.DAILY_SIGNIN,
            points=5,
            max_daily=1,
            description="Daily signin"
        )
        assert rule.action == PointsAction.DAILY_SIGNIN
        assert rule.points == 5
        assert rule.max_daily == 1
        assert rule.description == "Daily signin"

    def test_points_rule_defaults(self) -> None:
        """Test PointsRule default values."""
        rule = PointsRule(
            action=PointsAction.POST_CREATED,
            points=10
        )
        assert rule.max_daily == 1
        assert rule.description == ""
        assert rule.continuous_bonus is None
        assert rule.requires_auth is False
        assert rule.vip_multiplier == 1.0

    def test_points_rule_with_continuous_bonus(self) -> None:
        """Test PointsRule with continuous bonus."""
        bonus = {
            "7_days": {"bonus": 10, "description": "7 day bonus"}
        }
        rule = PointsRule(
            action=PointsAction.DAILY_SIGNIN,
            points=5,
            continuous_bonus=bonus
        )
        assert rule.continuous_bonus == bonus
        if rule.continuous_bonus:
            assert rule.continuous_bonus["7_days"]["bonus"] == 10


class TestPointsRules:
    """Test POINTS_RULES dictionary."""

    def test_points_rules_exists(self) -> None:
        """Test that POINTS_RULES exists."""
        assert POINTS_RULES is not None
        assert isinstance(POINTS_RULES, dict)

    def test_daily_signin_rule(self) -> None:
        """Test daily signin rule."""
        rule = POINTS_RULES["daily_signin"]
        assert rule.action == PointsAction.DAILY_SIGNIN
        assert rule.points == 5
        assert rule.max_daily == 1
        assert rule.continuous_bonus is not None

    def test_ai_consultation_rule(self) -> None:
        """Test AI consultation rule."""
        rule = POINTS_RULES["ai_consultation"]
        assert rule.action == PointsAction.AI_CONSULTATION
        assert rule.points == 2
        assert rule.max_daily == 10
        assert rule.requires_auth is True
        assert rule.vip_multiplier == 1.5

    def test_post_created_rule(self) -> None:
        """Test post created rule."""
        rule = POINTS_RULES["post_created"]
        assert rule.action == PointsAction.POST_CREATED
        assert rule.points == 10
        assert rule.max_daily == 5
        assert rule.requires_auth is True

    def test_invite_friend_high_points(self) -> None:
        """Test invite friend has highest points."""
        rule = POINTS_RULES["invite_friend"]
        assert rule.action == PointsAction.INVITE_FRIEND
        assert rule.points == 100
        assert rule.max_daily == 10

    def test_all_rules_have_valid_actions(self) -> None:
        """Test that all rules have valid actions."""
        for key, rule in POINTS_RULES.items():
            assert isinstance(rule.action, PointsAction)
            assert rule.points > 0
            assert rule.max_daily >= 0

    def test_all_rules_have_descriptions(self) -> None:
        """Test that all rules have descriptions."""
        for key, rule in POINTS_RULES.items():
            assert len(rule.description) > 0


class TestGetVipMultiplier:
    """Test get_vip_multiplier function."""

    def test_get_vip_multiplier_is_async(self) -> None:
        """Test get_vip_multiplier is async."""
        import inspect
        assert inspect.iscoroutinefunction(get_vip_multiplier)

    @pytest.mark.asyncio
    async def test_get_vip_multiplier_returns_float(self) -> None:
        """Test get_vip_multiplier returns a float."""
        # Mock database session properly
        mock_scalar_result = MagicMock(return_value=None)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = mock_scalar_result
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await get_vip_multiplier(123, mock_db)
        assert isinstance(result, float)
        assert result == 1.0  # Currently returns 1.0

    @pytest.mark.asyncio
    async def test_get_vip_multiplier_with_different_users(self) -> None:
        """Test get_vip_multiplier with different user IDs."""
        # Mock database session properly
        mock_scalar_result = MagicMock(return_value=None)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = mock_scalar_result
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result1 = await get_vip_multiplier(1, mock_db)
        result2 = await get_vip_multiplier(999, mock_db)
        assert result1 == result2 == 1.0


class TestGetPointsRule:
    """Test get_points_rule function."""

    def test_get_points_rule_existing_action(self) -> None:
        """Test get_points_rule with existing action."""
        rule = get_points_rule("daily_signin")
        assert rule is not None
        assert rule.action == PointsAction.DAILY_SIGNIN

    def test_get_points_rule_nonexistent_action(self) -> None:
        """Test get_points_rule with nonexistent action."""
        rule = get_points_rule("nonexistent_action")
        assert rule is None

    def test_get_points_rule_returns_points_rule(self) -> None:
        """Test get_points_rule returns PointsRule."""
        rule = get_points_rule("ai_consultation")
        assert isinstance(rule, PointsRule)

    def test_get_points_rule_all_actions(self) -> None:
        """Test get_points_rule for all actions."""
        for action_key in POINTS_RULES.keys():
            rule = get_points_rule(action_key)
            assert rule is not None
            assert rule == POINTS_RULES[action_key]


class TestPointsServiceBaseIntegration:
    """Integration tests for points service base."""

    def test_module_exports(self) -> None:
        """Test that module exports are correct."""
        from app.services.points import points_service_base
        assert hasattr(points_service_base, 'PointsAction')
        assert hasattr(points_service_base, 'PointsRule')
        assert hasattr(points_service_base, 'POINTS_RULES')
        assert hasattr(points_service_base, 'get_vip_multiplier')
        assert hasattr(points_service_base, 'get_points_rule')

    def test_rule_count(self) -> None:
        """Test that POINTS_RULES has expected number of rules."""
        assert len(POINTS_RULES) == 11  # Should have 11 rules

    def test_action_to_rule_mapping(self) -> None:
        """Test that actions map to rules correctly."""
        for key, rule in POINTS_RULES.items():
            # The action value should match the rule action
            action_value = rule.action.value
            # This is a sanity check
            assert isinstance(action_value, str)

    def test_rules_with_requires_auth(self) -> None:
        """Test rules that require authentication."""
        auth_rules = [k for k, r in POINTS_RULES.items() if r.requires_auth]
        assert "ai_consultation" in auth_rules
        assert "post_created" in auth_rules
        assert "comment_created" in auth_rules

    def test_rules_without_requires_auth(self) -> None:
        """Test rules that don't require authentication."""
        no_auth_rules = [k for k, r in POINTS_RULES.items() if not r.requires_auth]
        assert "daily_signin" in no_auth_rules
        assert "share_content" in no_auth_rules
