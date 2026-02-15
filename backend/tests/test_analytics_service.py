"""用户行为分析服务测试"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics.core import AnalyticsService


def _mock_scalars_all(rows):
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    return result


class TestAnalyticsService:
    @pytest.fixture
    def service(self):
        return AnalyticsService()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_log_behavior(self, service, mock_db):
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        log = await service.log_behavior(
            mock_db,
            user_id=1,
            action=service.ACTION_PAGE_VIEW,
            resource_type=service.RESOURCE_NEWS,
            resource_id=10,
            metadata={"source": "landing"},
            ip_address="127.0.0.1",
            user_agent="pytest",
            referrer="/home",
            session_id="sess-1",
        )

        assert log.user_id == 1
        assert log.action == service.ACTION_PAGE_VIEW
        assert log.resource_type == service.RESOURCE_NEWS
        assert log.resource_id == 10
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_user_behavior_history(self, service, mock_db):
        rows = [MagicMock(), MagicMock()]
        mock_db.execute = AsyncMock(return_value=_mock_scalars_all(rows))

        result = await service.get_user_behavior_history(
            mock_db,
            user_id=1,
            action=service.ACTION_CLICK,
            resource_type=service.RESOURCE_NEWS,
            limit=10,
            offset=0,
        )

        assert result == rows

    @pytest.mark.asyncio
    async def test_get_resource_view_count(self, service, mock_db):
        rows = [MagicMock(), MagicMock(), MagicMock()]
        mock_db.execute = AsyncMock(return_value=_mock_scalars_all(rows))

        count = await service.get_resource_view_count(
            mock_db,
            resource_type=service.RESOURCE_NEWS,
            resource_id=11,
        )

        assert count == 3

    @pytest.mark.asyncio
    async def test_get_user_session_activities(self, service, mock_db):
        rows = [MagicMock()]
        mock_db.execute = AsyncMock(return_value=_mock_scalars_all(rows))

        result = await service.get_user_session_activities(
            mock_db,
            session_id="sess-1",
            limit=20,
        )

        assert result == rows

    @pytest.mark.asyncio
    async def test_get_daily_active_users(self, service, mock_db):
        rows = [1, 2, 3]
        mock_db.execute = AsyncMock(return_value=_mock_scalars_all(rows))

        count = await service.get_daily_active_users(
            mock_db,
            date=datetime.now(timezone.utc),
        )

        assert count == 3

    @pytest.mark.asyncio
    async def test_get_action_statistics(self, service, mock_db):
        actions = [service.ACTION_CLICK, service.ACTION_CLICK, service.ACTION_SEARCH]
        mock_db.execute = AsyncMock(return_value=_mock_scalars_all(actions))

        stats = await service.get_action_statistics(
            mock_db,
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc),
        )

        assert stats[service.ACTION_CLICK] == 2
        assert stats[service.ACTION_SEARCH] == 1

    @pytest.mark.asyncio
    async def test_get_conversion_funnel(self, service, mock_db):
        service._get_step_users = AsyncMock(side_effect=[{1, 2, 3}, {1, 2, 3}, {1}])

        steps = [
            {"name": "view", "action": service.ACTION_PAGE_VIEW},
            {"name": "click", "action": service.ACTION_CLICK},
        ]
        now = datetime.now(timezone.utc)
        result = await service.get_conversion_funnel(
            mock_db,
            start_date=now - timedelta(days=1),
            end_date=now,
            funnel_steps=steps,
        )

        assert result[0]["count"] == 3
        assert result[0]["conversion_rate"] == 100
        assert result[1]["count"] == 1
        assert result[1]["drop_rate"] == round(((3 - 1) / 3) * 100, 2)

    @pytest.mark.asyncio
    async def test_get_step_users(self, service, mock_db):
        mock_db.execute = AsyncMock(return_value=_mock_scalars_all([1, 2, None]))
        now = datetime.now(timezone.utc)

        result = await service._get_step_users(
            mock_db,
            start_date=now - timedelta(days=1),
            end_date=now,
            action=service.ACTION_PAGE_VIEW,
            resource_type=service.RESOURCE_NEWS,
        )

        assert result == {1, 2}

    @pytest.mark.asyncio
    async def test_get_user_retention_empty_cohort(self, service, mock_db):
        mock_db.execute = AsyncMock(return_value=_mock_scalars_all([]))
        now = datetime.now(timezone.utc)

        result = await service.get_user_retention(
            mock_db,
            cohort_date=now,
            retention_days=[1, 7],
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_user_retention(self, service, mock_db):
        cohort_result = _mock_scalars_all([1, 2, 3])
        day1_result = _mock_scalars_all([1, 2])
        day7_result = _mock_scalars_all([2])
        mock_db.execute = AsyncMock(side_effect=[cohort_result, day1_result, day7_result])

        now = datetime.now(timezone.utc)
        result = await service.get_user_retention(
            mock_db,
            cohort_date=now,
            retention_days=[1, 7],
        )

        assert result[0]["day"] == 1
        assert result[0]["count"] == 2
        assert result[0]["rate"] == round(2 / 3 * 100, 2)
        assert result[1]["day"] == 7
        assert result[1]["count"] == 1
        assert result[1]["rate"] == round(1 / 3 * 100, 2)
