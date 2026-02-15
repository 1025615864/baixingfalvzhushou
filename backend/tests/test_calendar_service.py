"""日历提醒服务测试"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.calendar import (
    create_reminder,
    delete_reminder,
    get_owned_reminder,
    list_reminders,
    update_reminder,
)
from app.schemas.calendar import (
    CalendarReminderCreate,
    CalendarReminderUpdate,
)
from app.models.calendar import CalendarReminder
from app.models.user import User


class TestCalendarService:
    """日历提醒服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        user = MagicMock(spec=User)
        user.id = 123
        return user

    @pytest.fixture
    def mock_reminder(self):
        """创建模拟提醒"""
        reminder = MagicMock(spec=CalendarReminder)
        reminder.id = 1
        reminder.user_id = 123
        reminder.title = "测试提醒"
        reminder.note = "测试备注"
        reminder.due_at = datetime.now(timezone.utc)
        reminder.remind_at = datetime.now(timezone.utc)
        reminder.is_done = False
        reminder.done_at = None
        return reminder

    @pytest.mark.asyncio
    async def test_create_reminder(self, mock_db, mock_user, mock_reminder):
        """测试创建提醒"""
        payload = CalendarReminderCreate(
            title="测试提醒",
            note="测试备注",
            due_at=datetime.now(timezone.utc),
            remind_at=datetime.now(timezone.utc),
        )

        with patch("app.services.calendar.core.CalendarReminder") as MockReminder:
            MockReminder.return_value = mock_reminder
            mock_db.refresh = AsyncMock()

            result = await create_reminder(
                payload=payload,
                current_user=mock_user,
                db=mock_db,
            )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_list_reminders_pagination(self, mock_db, mock_user, mock_reminder):
        """测试获取提醒列表（分页）"""
        reminders = [mock_reminder]

        # 模拟 count 查询
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # 模拟查询结果
        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value.limit.return_value = mock_query
        mock_query.scalars.return_value.all.return_value = reminders

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_query])

        result = await list_reminders(
            current_user=mock_user,
            db=mock_db,
            page=1,
            page_size=20,
        )

        assert result.total == 1
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_list_reminders_filter_by_done(self, mock_db, mock_user):
        """测试按完成状态筛选提醒"""
        mock_reminder_done = MagicMock(spec=CalendarReminder)
        mock_reminder_done.id = 2
        mock_reminder_done.user_id = 123
        mock_reminder_done.title = "已完成的提醒"
        mock_reminder_done.note = "备注"
        mock_reminder_done.due_at = datetime.now(timezone.utc)
        mock_reminder_done.remind_at = datetime.now(timezone.utc)
        mock_reminder_done.is_done = True
        mock_reminder_done.done_at = datetime.now(timezone.utc)
        mock_reminder_done.created_at = datetime.now(timezone.utc)

        mock_query = MagicMock()
        mock_query.where = MagicMock(return_value=mock_query)
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value.limit.return_value = mock_query
        mock_query.scalars.return_value.all.return_value = [mock_reminder_done]

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_query])

        result = await list_reminders(
            current_user=mock_user,
            db=mock_db,
            done=True,
        )

        # 验证返回结果包含筛选后的数据
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == 2

    @pytest.mark.asyncio
    async def test_get_owned_reminder_found(self, mock_db, mock_user, mock_reminder):
        """测试获取拥有的提醒（存在）"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_reminder
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_owned_reminder(
            db=mock_db,
            reminder_id=1,
            user_id=123,
        )

        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_owned_reminder_not_found(self, mock_db):
        """测试获取拥有的提醒（不存在）"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_owned_reminder(
            db=mock_db,
            reminder_id=999,
            user_id=123,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_reminder_success(self, mock_db, mock_user, mock_reminder):
        """测试更新提醒成功"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_reminder
        mock_db.execute = AsyncMock(return_value=mock_result)

        payload = CalendarReminderUpdate(title="更新后的标题")
        mock_db.refresh = AsyncMock()

        result = await update_reminder(
            reminder_id=1,
            payload=payload,
            current_user=mock_user,
            db=mock_db,
        )

        assert mock_reminder.title == "更新后的标题"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_reminder_not_found(self, mock_db, mock_user):
        """测试更新不存在的提醒"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        payload = CalendarReminderUpdate(title="更新后的标题")

        with pytest.raises(Exception) as exc_info:
            await update_reminder(
                reminder_id=999,
                payload=payload,
                current_user=mock_user,
                db=mock_db,
            )

        assert "提醒不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_reminder_mark_as_done(self, mock_db, mock_user, mock_reminder):
        """测试标记提醒为已完成"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_reminder
        mock_db.execute = AsyncMock(return_value=mock_result)

        payload = CalendarReminderUpdate(is_done=True)
        mock_db.refresh = AsyncMock()

        result = await update_reminder(
            reminder_id=1,
            payload=payload,
            current_user=mock_user,
            db=mock_db,
        )

        assert mock_reminder.is_done is True
        assert mock_reminder.done_at is not None

    @pytest.mark.asyncio
    async def test_delete_reminder_success(self, mock_db, mock_user, mock_reminder):
        """测试删除提醒成功"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_reminder
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()

        result = await delete_reminder(
            reminder_id=1,
            current_user=mock_user,
            db=mock_db,
        )

        assert result["message"] == "删除成功"
        mock_db.delete.assert_called_once_with(mock_reminder)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_reminder_not_found(self, mock_db, mock_user):
        """测试删除不存在的提醒"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(Exception) as exc_info:
            await delete_reminder(
                reminder_id=999,
                current_user=mock_user,
                db=mock_db,
            )

        assert "提醒不存在" in str(exc_info.value)


class TestCalendarReminderCreate:
    """CalendarReminderCreate 测试类"""

    def test_create_reminder_payload(self):
        """测试创建提醒负载"""
        now = datetime.now(timezone.utc)
        payload = CalendarReminderCreate(
            title="法律咨询提醒",
            note="联系律师",
            due_at=now,
            remind_at=now,
        )

        assert payload.title == "法律咨询提醒"
        assert payload.note == "联系律师"
        assert payload.due_at == now
        assert payload.remind_at == now


class TestCalendarReminderUpdate:
    """CalendarReminderUpdate 测试类"""

    def test_update_reminder_partial(self):
        """测试部分更新提醒"""
        payload = CalendarReminderUpdate(title="新标题")

        assert payload.title == "新标题"
        assert payload.note is None
        assert payload.due_at is None

    def test_update_reminder_complete(self):
        """测试完整更新提醒"""
        now = datetime.now(timezone.utc)
        payload = CalendarReminderUpdate(
            title="完整更新",
            note="完整备注",
            due_at=now,
            remind_at=now,
            is_done=True,
        )

        assert payload.title == "完整更新"
        assert payload.is_done is True
