"""
积分服务单元测试

测试覆盖：
- 积分规则配置
- 积分发放
- 积分消费
- 积分查询
- 交易记录
- VIP倍数计算
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.points import (
    PointsService,
    PointsAction,
    PointsRule,
    PointsHistoryItem,
    POINTS_RULES,
    get_points_service,
    award_points,
    redeem_points,
    get_balance,
    get_vip_multiplier,
    get_points_rule,
)


class TestPointsRules:
    """积分规则测试类"""

    def test_points_rules_structure(self):
        """测试积分规则结构"""
        assert isinstance(POINTS_RULES, dict)
        assert len(POINTS_RULES) > 0

    def test_daily_signin_rule_exists(self):
        """测试每日签到规则存在"""
        rule = POINTS_RULES.get("daily_signin")
        assert rule is not None
        assert rule.action == PointsAction.DAILY_SIGNIN
        assert rule.points == 5
        assert rule.max_daily == 1

    def test_ai_consultation_rule_exists(self):
        """测试AI咨询规则存在"""
        rule = POINTS_RULES.get("ai_consultation")
        assert rule is not None
        assert rule.action == PointsAction.AI_CONSULTATION
        assert rule.points == 2
        assert rule.max_daily == 10

    def test_post_created_rule_exists(self):
        """测试发布帖子规则存在"""
        rule = POINTS_RULES.get("post_created")
        assert rule is not None
        assert rule.action == PointsAction.POST_CREATED
        assert rule.points == 10

    def test_get_points_rule_exists(self):
        """测试获取存在的积分规则"""
        rule = get_points_rule("daily_signin")
        assert rule is not None
        assert rule.action == PointsAction.DAILY_SIGNIN
        assert rule.points == 5

    def test_get_points_rule_not_exists(self):
        """测试获取不存在的积分规则"""
        rule = get_points_rule("nonexistent_rule")
        assert rule is None


class TestPointsService:
    """积分服务测试类"""

    def test_points_service_initialization(self):
        """测试积分服务初始化"""
        service = PointsService()
        assert service is not None
        assert hasattr(service, '_user_points')
        assert hasattr(service, '_user_history')
        assert hasattr(service, '_daily_counts')

    def test_get_balance_new_user(self):
        """测试获取新用户的余额"""
        service = PointsService()
        balance = service.get_balance(999)
        assert balance == 0

    def test_get_balance_existing_user(self):
        """测试获取已存在用户的余额"""
        service = PointsService()
        service._user_points[1] = 100
        balance = service.get_balance(1)
        assert balance == 100

    async def test_award_points_success(self):
        """测试成功奖励积分"""
        service = PointsService()
        points, error = await service.award_points(
            user_id=1,
            action="daily_signin",
            description="每日签到",
        )
        assert points == 5
        assert error is None
        assert service.get_balance(1) == 5

    async def test_award_points_unknown_action(self):
        """测试未知动作奖励积分"""
        service = PointsService()
        points, error = await service.award_points(
            user_id=1,
            action="unknown_action",
            description="未知动作",
        )
        assert points == 0
        assert error is not None
        assert "未知的积分动作" in error

    async def test_award_points_exceed_daily_limit(self):
        """测试超过每日限制"""
        service = PointsService()
        
        # 每日签到只能1次
        await service.award_points(
            user_id=1,
            action="daily_signin",
            description="每日签到",
        )
        
        points, error = await service.award_points(
            user_id=1,
            action="daily_signin",
            description="每日签到",
        )
        assert points == 0
        assert error is not None
        assert "今日" in error

    async def test_award_points_requires_auth(self):
        """测试需要认证的动作"""
        service = PointsService()
        
        # AI咨询需要认证，用户ID <= 0表示未登录
        points, error = await service.award_points(
            user_id=0,
            action="ai_consultation",
            description="AI咨询",
        )
        assert points == 0
        assert error is not None

    async def test_redeem_points_success(self):
        """测试成功消费积分"""
        service = PointsService()
        service._user_points[1] = 100
        
        success, error = await service.redeem_points(
            user_id=1,
            points=30,
            product_id="test_product",
            description="测试消费",
        )
        assert success is True
        assert error is None
        assert service.get_balance(1) == 70

    async def test_redeem_points_insufficient_balance(self):
        """测试余额不足消费积分"""
        service = PointsService()
        service._user_points[1] = 10
        
        success, error = await service.redeem_points(
            user_id=1,
            points=30,
            product_id="test_product",
            description="测试消费",
        )
        assert success is False
        assert error is not None
        assert "积分不足" in error

    async def test_redeem_points_user_not_exists(self):
        """测试用户不存在消费积分"""
        service = PointsService()
        
        success, error = await service.redeem_points(
            user_id=999,
            points=30,
            product_id="test_product",
            description="测试消费",
        )
        assert success is False
        assert error is not None

    def test_get_history_empty(self):
        """测试获取空历史记录"""
        service = PointsService()
        history = service.get_history(1)
        assert history == []

    def test_get_history_with_data(self):
        """测试获取有数据的历史记录"""
        service = PointsService()
        
        service._user_history[1] = [
            PointsHistoryItem(
                id=1,
                user_id=1,
                action="daily_signin",
                points=5,
                balance_after=5,
                description="每日签到",
                created_at=datetime.now(timezone.utc),
            )
        ]
        
        history = service.get_history(1)
        assert len(history) == 1
        assert history[0].action == "daily_signin"
        assert history[0].points == 5


class TestPointsHelpers:
    """积分服务辅助函数测试"""

    def test_get_points_service_singleton(self):
        """测试获取积分服务单例"""
        service1 = get_points_service()
        service2 = get_points_service()
        assert service1 is service2

    def test_balance_helper_new_user(self):
        """测试余额辅助函数（新用户）"""
        balance = get_balance(9999)
        assert balance == 0

    def test_balance_helper_existing_user(self):
        """测试余额辅助函数（已存在用户）"""
        service = get_points_service()
        service._user_points[1] = 100
        balance = get_balance(1)
        assert balance == 100


class TestVipMultiplier:
    """VIP倍数测试"""

    def test_vip_multiplier_in_rule(self):
        """测试规则中的VIP倍数"""
        rule = POINTS_RULES.get("ai_consultation")
        assert rule.vip_multiplier == 1.5

    def test_rule_without_vip_multiplier(self):
        """测试没有VIP倍数的规则"""
        rule = POINTS_RULES.get("daily_signin")
        assert rule.vip_multiplier == 1.0


class TestPointsActions:
    """积分动作枚举测试"""

    def test_actions_exist(self):
        """测试所有动作存在"""
        assert PointsAction.DAILY_SIGNIN.value == "daily_signin"
        assert PointsAction.AI_CONSULTATION.value == "ai_consultation"
        assert PointsAction.POST_CREATED.value == "post_created"
        assert PointsAction.COMMENT_CREATED.value == "comment_created"
        assert PointsAction.SHARE_CONTENT.value == "share_content"


class TestDailyLimits:
    """每日限制测试"""

    def test_daily_signin_limit(self):
        """测试每日签到的限制"""
        rule = POINTS_RULES.get("daily_signin")
        assert rule.max_daily == 1

    def test_ai_consultation_limit(self):
        """测试AI咨询的每日限制"""
        rule = POINTS_RULES.get("ai_consultation")
        assert rule.max_daily == 10

    def test_post_created_limit(self):
        """测试发布帖子的每日限制"""
        rule = POINTS_RULES.get("post_created")
        assert rule.max_daily == 5


class TestContinuousBonus:
    """连续奖励测试"""

    def test_daily_signin_bonus_exists(self):
        """测试每日签到的连续奖励"""
        rule = POINTS_RULES.get("daily_signin")
        assert rule.continuous_bonus is not None
        assert "7_days" in rule.continuous_bonus
        assert "30_days" in rule.continuous_bonus

    def test_7_days_bonus(self):
        """测试7天连续奖励"""
        rule = POINTS_RULES.get("daily_signin")
        bonus = rule.continuous_bonus["7_days"]
        assert bonus["bonus"] == 10

    def test_30_days_bonus(self):
        """测试30天连续奖励"""
        rule = POINTS_RULES.get("daily_signin")
        bonus = rule.continuous_bonus["30_days"]
        assert bonus["bonus"] == 50


class TestRequiresAuth:
    """认证要求测试"""

    def test_ai_consultation_requires_auth(self):
        """测试AI咨询需要认证"""
        rule = POINTS_RULES.get("ai_consultation")
        assert rule.requires_auth is True

    def test_daily_signin_no_auth(self):
        """测试每日签到不需要认证"""
        rule = POINTS_RULES.get("daily_signin")
        assert rule.requires_auth is False


class TestPointsScenarios:
    """积分场景测试"""

    async def test_complete_workflow(self):
        """测试完整的积分流程"""
        service = PointsService()
        user_id = 1

        # 1. 每日签到获得5积分
        points, error = await service.award_points(
            user_id=user_id,
            action="daily_signin",
            description="每日签到",
        )
        assert points == 5
        assert service.get_balance(user_id) == 5

        # 2. 发表评论获得5积分
        points, error = await service.award_points(
            user_id=user_id,
            action="comment_created",
            description="发表评论",
        )
        assert points == 5
        assert service.get_balance(user_id) == 10

        # 3. 发布帖子获得10积分
        points, error = await service.award_points(
            user_id=user_id,
            action="post_created",
            description="发布帖子",
        )
        assert points == 10
        assert service.get_balance(user_id) == 20

        # 4. 消费积分
        success, error = await service.redeem_points(
            user_id=user_id,
            points=15,
            product_id="gift",
            description="兑换礼物",
        )
        assert success is True
        assert service.get_balance(user_id) == 5

        # 5. 验证历史记录
        history = service.get_history(user_id)
        assert len(history) == 4  # 3个获得 + 1个消费
