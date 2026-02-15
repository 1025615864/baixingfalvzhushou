"""通知服务测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.notification_service import (
    NotificationService,
    NotificationList,
    NotificationPreferences,
)
from app.models.notification import Notification, NotificationType


class TestNotificationService:
    """NotificationService 测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self):
        """创建通知服务实例"""
        return NotificationService()

    @pytest.mark.asyncio
    async def test_send_creates_notification(self, service, mock_db):
        """测试发送通知创建记录"""
        notification = Notification(
            id=1,
            user_id=123,
            type=NotificationType.SYSTEM,
            title="测试通知",
            content="测试内容",
            is_read=False,
        )
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()

        with patch("app.services.notification_service.Notification") as MockNotification:
            MockNotification.return_value = notification
            result = await service.send(
                mock_db,
                user_id=123,
                title="测试通知",
                content="测试内容",
                type=NotificationType.SYSTEM,
            )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert result.user_id == 123
        assert result.title == "测试通知"

    @pytest.mark.asyncio
    async def test_get_list_returns_paginated_results(self, service, mock_db):
        """测试获取通知列表返回分页结果"""
        notifications = [
            Notification(id=1, user_id=123, title="通知1"),
            Notification(id=2, user_id=123, title="通知2"),
        ]

        # 模拟 total 查询
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 2

        # 模拟查询结果
        mock_query = MagicMock()
        mock_query.order_by.return_value.offset.return_value.limit.return_value = mock_query
        mock_query.scalars.return_value.all.return_value = notifications
        mock_query.scalars.return_value = MagicMock(all=lambda: notifications)

        mock_db.execute = AsyncMock()
        mock_db.execute.side_effect = [mock_total_result, mock_query]

        result = await service.get_list(mock_db, user_id=123, page=1, page_size=20)

        assert isinstance(result, NotificationList)
        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_get_unread_count(self, service, mock_db):
        """测试获取未读通知数量"""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_unread_count(mock_db, user_id=123)

        assert result == 5

    @pytest.mark.asyncio
    async def test_mark_as_read_success(self, service, mock_db):
        """测试标记通知为已读成功"""
        notification = Notification(id=1, user_id=123, is_read=False)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = notification
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.mark_as_read(mock_db, notification_id=1)

        assert result is True
        assert notification.is_read is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, service, mock_db):
        """测试标记不存在的通知"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.mark_as_read(mock_db, notification_id=999)

        assert result is False
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, service, mock_db):
        """测试标记所有通知为已读"""
        notifications = [
            Notification(id=1, user_id=123, is_read=False),
            Notification(id=2, user_id=123, is_read=False),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = notifications
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.mark_all_as_read(mock_db, user_id=123)

        assert result is True
        assert all(n.is_read for n in notifications)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_success(self, service, mock_db):
        """测试删除通知成功"""
        notification = Notification(id=1, user_id=123)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = notification
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()

        result = await service.delete(mock_db, notification_id=1)

        assert result is True
        mock_db.delete.assert_called_once_with(notification)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, service, mock_db):
        """测试删除不存在的通知"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.delete(mock_db, notification_id=999)

        assert result is False
        mock_db.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_by_type(self, service, mock_db):
        """测试按类型获取通知"""
        notifications = [
            Notification(id=1, user_id=123, type=NotificationType.SYSTEM),
            Notification(id=2, user_id=123, type=NotificationType.SYSTEM),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = notifications
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_by_type(mock_db, user_id=123, notification_type=NotificationType.SYSTEM)

        assert len(result) == 2
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_preferences(self, service):
        """测试获取用户通知偏好"""
        result = await service.get_user_preferences(None, user_id=123)

        assert isinstance(result, NotificationPreferences)
        assert result.email_enabled is True
        assert result.push_enabled is True

    @pytest.mark.asyncio
    async def test_update_preferences(self, service, mock_db):
        """测试更新通知偏好"""
        result = await service.update_preferences(
            mock_db,
            user_id=123,
            email_enabled=False,
            push_enabled=True,
        )

        assert result is True

        # 验证偏好已更新
        prefs = await service.get_user_preferences(mock_db, user_id=123)
        assert prefs.email_enabled is False
        assert prefs.push_enabled is True

    def test_get_template(self, service):
        """测试获取通知模板"""
        template = service.get_template("system")
        assert template is not None
        assert template["title"] == "系统通知"
        assert "{content}" in template["content"]

    def test_get_template_not_found(self, service):
        """测试获取不存在的模板"""
        template = service.get_template("unknown_type")
        assert template is None


class TestNotificationList:
    """NotificationList 数据类测试"""

    def test_creation(self):
        """测试创建 NotificationList"""
        notifications = [Notification(id=1), Notification(id=2)]
        notification_list = NotificationList(
            items=notifications,
            total=10,
            page=2,
            page_size=5,
        )

        assert len(notification_list.items) == 2
        assert notification_list.total == 10
        assert notification_list.page == 2
        assert notification_list.page_size == 5


class TestNotificationPreferences:
    """NotificationPreferences 数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        prefs = NotificationPreferences()

        assert prefs.email_enabled is True
        assert prefs.push_enabled is True

    def test_custom_values(self):
        """测试自定义值"""
        prefs = NotificationPreferences(email_enabled=False, push_enabled=False)

        assert prefs.email_enabled is False
        assert prefs.push_enabled is False
