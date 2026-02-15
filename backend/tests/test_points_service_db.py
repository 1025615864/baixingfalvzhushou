"""PointsServiceDB 测试文件"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.points.points_service_db import (
    PointsServiceDB,
    PointsHistoryItem,
    get_balance_db,
    award_points_db,
    redeem_points_db,
)
from app.services.points.points_service_base import POINTS_RULES, PointsAction


class TestPointsHistoryItem:
    """积分历史记录数据类测试"""

    def test_create_points_history_item(self):
        """测试创建积分历史记录"""
        now = datetime.now(timezone.utc)
        item = PointsHistoryItem(
            id=1,
            user_id=100,
            action="daily_signin",
            points=10,
            balance_after=100,
            description="每日签到",
            created_at=now,
        )
        assert item.id == 1
        assert item.user_id == 100
        assert item.action == "daily_signin"
        assert item.points == 10
        assert item.balance_after == 100
        assert item.description == "每日签到"
        assert item.created_at == now
        assert item.extra_data is None

    def test_create_points_history_item_with_extra_data(self):
        """测试创建带额外数据的积分历史记录"""
        now = datetime.now(timezone.utc)
        extra = {"source": "app", "channel": "ios"}
        item = PointsHistoryItem(
            id=2,
            user_id=200,
            action="post_comment",
            points=5,
            balance_after=105,
            description="评论",
            created_at=now,
            extra_data=extra,
        )
        assert item.extra_data == extra


class TestPointsServiceDB:
    """积分服务测试类"""

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def points_service(self):
        """创建积分服务实例"""
        return PointsServiceDB()

    @pytest.fixture
    def mock_points_user(self):
        """模拟积分用户"""
        user = MagicMock()
        user.user_id = 100
        user.balance = 50
        user.total_earned = 100
        user.total_spent = 50
        user.continuous_signin_days = 0
        return user

    @pytest.fixture
    def mock_points_history(self):
        """模拟积分历史记录"""
        history = MagicMock()
        history.id = 1
        history.user_id = 100
        history.action = "daily_signin"
        history.points = 10
        history.balance_after = 60
        history.description = "每日签到"
        history.created_at = datetime.now(timezone.utc)
        history.metadata_json = None
        return history

    @pytest.fixture
    def mock_points_daily_count(self):
        """模拟每日计数"""
        daily = MagicMock()
        daily.user_id = 100
        daily.action = "daily_signin"
        daily.date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily.count = 0
        return daily

    def test_init(self, points_service):
        """测试服务初始化"""
        assert points_service is not None

    @pytest.mark.asyncio
    async def test_get_or_create_user_existing(self, points_service, mock_db_session, mock_points_user):
        """测试获取已存在的用户"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_points_user)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        user = await points_service._get_or_create_user(mock_db_session, 100)

        assert user == mock_points_user
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_user_new(self, points_service, mock_db_session):
        """测试创建新用户"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        user = await points_service._get_or_create_user(mock_db_session, 999)

        assert user is not None
        assert user.user_id == 999
        assert user.balance == 0
        assert user.total_earned == 0
        assert user.total_spent == 0
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_balance(self, points_service, mock_db_session, mock_points_user):
        """测试获取积分余额"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_points_user)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        balance = await points_service.get_balance(mock_db_session, 100)

        assert balance == 50
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_balance_new_user(self, points_service, mock_db_session):
        """测试新用户余额为0"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        balance = await points_service.get_balance(mock_db_session, 999)

        assert balance == 0

    @pytest.mark.asyncio
    async def test_award_points_unknown_action(self, points_service, mock_db_session):
        """测试未知动作的积分奖励"""
        points, error = await points_service.award_points(
            mock_db_session, 100, "unknown_action"
        )

        assert points == 0
        assert "未知的积分动作" in error

    @pytest.mark.asyncio
    async def test_award_points_requires_auth(self, points_service, mock_db_session):
        """测试需要认证的积分动作"""
        points, error = await points_service.award_points(
            mock_db_session, 0, "post_created"
        )

        assert points == 0
        assert error is not None
        assert "登录" in error or "auth" in error.lower()

    @pytest.mark.asyncio
    async def test_award_points_daily_limit_exceeded(self, points_service, mock_db_session, mock_points_user):
        """测试每日上限"""
        # 设置规则：daily_signin 每日上限为1
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_points_user)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # 模拟已达到上限
        daily_result = MagicMock()
        daily_result.scalar_one_or_none = MagicMock(return_value=MagicMock(count=1))
        mock_db_session.execute = AsyncMock(return_value=daily_result)

        points, error = await points_service.award_points(
            mock_db_session, 100, "daily_signin"
        )

        assert points == 0
        assert "次数已达上限" in error

    @pytest.mark.asyncio
    async def test_award_points_success(self, points_service, mock_db_session, mock_points_user):
        """测试成功奖励积分"""
        mock_points_user.balance = 50
        mock_points_user.total_earned = 100
        mock_points_user.continuous_signin_days = 0

        # 模拟用户存在
        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=mock_points_user)

        # 模拟每日计数为0
        daily_result = MagicMock()
        daily_result.scalar_one_or_none = MagicMock(return_value=None)

        # 返回用户查询结果或每日计数查询结果
        mock_db_session.execute = AsyncMock(side_effect=[
            user_result,  # _get_or_create_user
            daily_result,  # _get_daily_count
            daily_result,  # _update_daily_count (select)
            daily_result,  # _update_daily_count (refresh 不需要 mock)
        ])

        points, error = await points_service.award_points(
            mock_db_session, 100, "daily_signin", description="每日签到"
        )

        # daily_signin 是无需认证的动作，所以应该能获得积分
        assert error is None
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_record_transaction(self, points_service, mock_db_session, mock_points_user):
        """测试记录交易"""
        mock_points_user.balance = 100
        mock_points_user.total_earned = 100

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=mock_points_user)
        mock_db_session.execute = AsyncMock(return_value=user_result)
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        result = await points_service.record_transaction(
            mock_db_session,
            user_id=100,
            amount=50,
            transaction_type="deposit",
            source="payment",
            remark="充值",
        )

        assert result is not None
        assert result.action == "deposit"
        assert result.points == 50
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_record_transaction_negative_amount(self, points_service, mock_db_session, mock_points_user):
        """测试负数交易（消费）"""
        mock_points_user.balance = 100
        mock_points_user.total_earned = 100
        mock_points_user.total_spent = 0

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=mock_points_user)
        mock_db_session.execute = AsyncMock(return_value=user_result)
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        result = await points_service.record_transaction(
            mock_db_session,
            user_id=100,
            amount=-30,
            transaction_type="redeem",
            source="mall",
            remark="兑换商品",
        )

        assert result is not None
        assert result.points == -30
        mock_db_session.add.assert_called()

    @pytest.mark.asyncio
    async def test_redeem_points_insufficient_balance(self, points_service, mock_db_session, mock_points_user):
        """测试积分不足的兑换"""
        mock_points_user.balance = 50

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=mock_points_user)
        mock_db_session.execute = AsyncMock(return_value=user_result)

        success, error = await points_service.redeem_points(
            mock_db_session, 100, 100, "product1", "兑换商品"
        )

        assert success is False
        assert "积分不足" in error

    @pytest.mark.asyncio
    async def test_redeem_points_success(self, points_service, mock_db_session, mock_points_user):
        """测试成功兑换"""
        mock_points_user.balance = 200
        mock_points_user.total_earned = 200
        mock_points_user.total_spent = 0

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=mock_points_user)
        mock_db_session.execute = AsyncMock(return_value=user_result)
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()

        success, error = await points_service.redeem_points(
            mock_db_session, 100, 100, "product1", "兑换商品"
        )

        assert success is True
        assert error is None
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_get_history(self, points_service, mock_db_session, mock_points_history):
        """测试获取积分历史"""
        mock_result = MagicMock()
        mock_result.scalars().all = MagicMock(return_value=[mock_points_history])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        history = await points_service.get_history(mock_db_session, 100)

        assert len(history) == 1
        assert history[0].action == "daily_signin"
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history_with_pagination(self, points_service, mock_db_session):
        """测试带分页的积分历史"""
        mock_result = MagicMock()
        mock_result.scalars().all = MagicMock(return_value=[])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        history = await points_service.get_history(mock_db_session, 100, limit=10, offset=20)

        assert len(history) == 0
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_daily_stats(self, points_service, mock_db_session, mock_points_daily_count):
        """测试获取每日统计"""
        mock_result = MagicMock()
        mock_result.scalars().all = MagicMock(return_value=[mock_points_daily_count])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        stats = await points_service.get_daily_stats(mock_db_session, 100)

        assert "daily_signin" in stats
        assert stats["daily_signin"] == 0

    @pytest.mark.asyncio
    async def test_get_daily_stats_empty(self, points_service, mock_db_session):
        """测试空每日统计"""
        mock_result = MagicMock()
        mock_result.scalars().all = MagicMock(return_value=[])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        stats = await points_service.get_daily_stats(mock_db_session, 100)

        assert stats == {}

    @pytest.mark.asyncio
    async def test_get_continuous_days(self, points_service, mock_db_session, mock_points_user):
        """测试获取连续签到天数"""
        mock_points_user.continuous_signin_days = 7

        user_result = MagicMock()
        user_result.scalar_one_or_none = MagicMock(return_value=mock_points_user)
        mock_db_session.execute = AsyncMock(return_value=user_result)

        days = await points_service.get_continuous_days(mock_db_session, 100)

        assert days == 7

    def test_get_rules(self, points_service):
        """测试获取积分规则"""
        rules = points_service.get_rules()

        assert len(rules) > 0
        assert any(r["action"] == "daily_signin" for r in rules)
        assert any(r["action"] == "post_created" for r in rules)
        assert any(r["action"] == "comment_created" for r in rules)

    @pytest.mark.asyncio
    async def test_get_leaderboard(self, points_service, mock_db_session, mock_points_user):
        """测试获取排行榜"""
        mock_result = MagicMock()
        mock_result.scalars().all = MagicMock(return_value=[mock_points_user])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        leaderboard = await points_service.get_leaderboard(mock_db_session, top_k=10)

        assert len(leaderboard) == 1
        assert leaderboard[0]["rank"] == 1
        assert leaderboard[0]["user_id"] == 100
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_daily_counts(self, points_service, mock_db_session, mock_points_daily_count):
        """测试重置每日计数"""
        mock_result = MagicMock()
        mock_result.scalars().all = MagicMock(return_value=[mock_points_daily_count])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await points_service.reset_daily_counts(mock_db_session)

        mock_db_session.commit.assert_called_once()


class TestPointsServiceDBHelpers:
    """积分服务便捷函数测试"""

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.mark.asyncio
    async def test_get_balance_db(self, mock_db_session):
        """测试便捷函数：获取余额"""
        with patch('app.services.points.points_service_db.PointsServiceDB') as MockService:
            mock_service = MagicMock()
            mock_service.get_balance = AsyncMock(return_value=100)
            MockService.return_value = mock_service

            result = await get_balance_db(mock_db_session, 100)

            assert result == 100

    @pytest.mark.asyncio
    async def test_award_points_db(self, mock_db_session):
        """测试便捷函数：奖励积分"""
        with patch('app.services.points.points_service_db.PointsServiceDB') as MockService:
            mock_service = MagicMock()
            mock_service.award_points = AsyncMock(return_value=(10, None))
            MockService.return_value = mock_service

            result = await award_points_db(mock_db_session, 100, "daily_signin")

            assert result == (10, None)

    @pytest.mark.asyncio
    async def test_redeem_points_db(self, mock_db_session):
        """测试便捷函数：兑换积分"""
        with patch('app.services.points.points_service_db.PointsServiceDB') as MockService:
            mock_service = MagicMock()
            mock_service.redeem_points = AsyncMock(return_value=(True, None))
            MockService.return_value = mock_service

            result = await redeem_points_db(mock_db_session, 100, 50, "product1", "兑换")

            assert result == (True, None)


class TestPointsServiceDBSignin:
    """积分服务签到功能测试"""

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def points_service(self):
        """创建积分服务实例"""
        return PointsServiceDB()

    @pytest.fixture
    def mock_points_user(self):
        """模拟积分用户"""
        user = MagicMock()
        user.user_id = 100
        user.balance = 50
        user.total_earned = 100
        user.total_spent = 50
        user.continuous_signin_days = 0
        user.last_signin_at = None
        return user

    @pytest.mark.asyncio
    async def test_handle_signin_first_day(self, points_service, mock_db_session, mock_points_user):
        """测试首次签到"""
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        result = await points_service._handle_signin_bonus(
            mock_db_session, mock_points_user, 10, today
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_handle_signin_continuous_days(self, points_service, mock_db_session, mock_points_user):
        """测试连续签到"""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        mock_points_user.last_signin_at = datetime.strptime(yesterday, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        mock_points_user.continuous_signin_days = 2

        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        result = await points_service._handle_signin_bonus(
            mock_db_session, mock_points_user, 10, today
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_handle_signin_bonus_7_days(self, points_service, mock_db_session, mock_points_user):
        """测试7天连续签到奖励"""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        mock_points_user.last_signin_at = datetime.strptime(yesterday, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        mock_points_user.continuous_signin_days = 6

        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        result = await points_service._handle_signin_bonus(
            mock_db_session, mock_points_user, 10, today
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_handle_signin_bonus_30_days(self, points_service, mock_db_session, mock_points_user):
        """测试30天连续签到奖励"""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        mock_points_user.last_signin_at = datetime.strptime(yesterday, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        mock_points_user.continuous_signin_days = 29

        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        result = await points_service._handle_signin_bonus(
            mock_db_session, mock_points_user, 10, today
        )

        assert result is not None


class TestPointsServiceDBDailyCount:
    """积分服务每日计数测试"""

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def points_service(self):
        """创建积分服务实例"""
        return PointsServiceDB()

    @pytest.mark.asyncio
    async def test_get_daily_count_zero(self, points_service, mock_db_session):
        """测试获取每日计数（返回0）"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        count = await points_service._get_daily_count(
            mock_db_session, 100, "daily_signin", "2024-01-01"
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_get_daily_count_with_data(self, points_service, mock_db_session):
        """测试获取每日计数（有数据）"""
        mock_daily = MagicMock()
        mock_daily.count = 5

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_daily)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        count = await points_service._get_daily_count(
            mock_db_session, 100, "daily_signin", "2024-01-01"
        )

        assert count == 5

    @pytest.mark.asyncio
    async def test_update_daily_count_new(self, points_service, mock_db_session):
        """测试更新每日计数（新记录）"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()

        await points_service._update_daily_count(
            mock_db_session, 100, "daily_signin", "2024-01-01", 1
        )

        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_update_daily_count_existing(self, points_service, mock_db_session):
        """测试更新每日计数（已有记录）"""
        mock_daily = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_daily)
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()

        await points_service._update_daily_count(
            mock_db_session, 100, "daily_signin", "2024-01-01", 5
        )

        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_get_balance_before(self, points_service, mock_db_session):
        """测试获取操作前余额"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=100)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        balance = await points_service._get_balance_before(mock_db_session, 100)

        assert balance == 100

    @pytest.mark.asyncio
    async def test_get_balance_before_no_history(self, points_service, mock_db_session):
        """测试获取操作前余额（无历史记录）"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        balance = await points_service._get_balance_before(mock_db_session, 100)

        assert balance == 0
