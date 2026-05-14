"""通知服务契约测试"""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestNotificationServiceContract:
    """通知服务契约测试"""

    @pytest.mark.asyncio
    async def test_list_notifications(self, client: AsyncClient):
        """测试获取通知列表"""
        response = await client.get(
            "/api/v1/notifications/",
            params={"user_id": 1, "page": 1, "page_size": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "unread_count" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_unread_notifications(self, client: AsyncClient):
        """测试获取未读通知"""
        response = await client.get(
            "/api/v1/notifications/",
            params={"user_id": 1, "unread_only": True}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_unread_count(self, client: AsyncClient):
        """测试获取未读数量"""
        response = await client.get(
            "/api/v1/notifications/unread-count",
            params={"user_id": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "unread_count" in data

    @pytest.mark.asyncio
    async def test_create_notification(self, client: AsyncClient):
        """测试创建通知"""
        response = await client.post(
            "/api/v1/notifications/",
            json={
                "user_id": 1,
                "type": "system",
                "title": "测试通知",
                "content": "这是一条测试通知"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "user_id" in data
        assert "title" in data
        assert "is_read" in data

    @pytest.mark.asyncio
    async def test_batch_create_notifications(self, client: AsyncClient):
        """测试批量创建通知"""
        response = await client.post(
            "/api/v1/notifications/batch",
            json={
                "user_ids": [1, 2, 3],
                "type": "system",
                "title": "系统公告",
                "content": "这是一条系统公告"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_mark_notification_as_read(self, client: AsyncClient):
        """测试标记通知为已读"""
        response = await client.patch(
            "/api/v1/notifications/1/read"
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, client: AsyncClient):
        """测试标记所有为已读"""
        response = await client.patch(
            "/api/v1/notifications/read-all",
            params={"user_id": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_delete_notification(self, client: AsyncClient):
        """测试删除通知"""
        response = await client.delete(
            "/api/v1/notifications/1"
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_settings(self, client: AsyncClient):
        """测试获取通知设置"""
        response = await client.get(
            "/api/v1/notifications/settings",
            params={"user_id": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert "email_enabled" in data
        assert "sms_enabled" in data
        assert "push_enabled" in data

    @pytest.mark.asyncio
    async def test_update_settings(self, client: AsyncClient):
        """测试更新通知设置"""
        response = await client.put(
            "/api/v1/notifications/settings",
            params={"user_id": 1},
            json={
                "email_enabled": True,
                "sms_enabled": False,
                "push_enabled": True,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "email_enabled" in data
        assert "quiet_hours_start" in data


class TestNotificationTemplateContract:
    """通知模板契约测试"""

    @pytest.mark.asyncio
    async def test_render_template(self, client: AsyncClient):
        """测试渲染通知模板"""
        response = await client.post(
            "/api/v1/notifications/template/system_announcement/render",
            json={
                "title": "系统维护公告",
                "content": "系统将于今晚 22:00 进行维护"
            }
        )
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "title" in data
            assert "content" in data

    @pytest.mark.asyncio
    async def test_list_templates(self, client: AsyncClient):
        """测试列出所有模板"""
        response = await client.get(
            "/api/v1/notifications/templates"
        )
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)


class TestNotificationModelsContract:
    """通知服务模型契约测试"""

    def test_notification_model_fields(self):
        """测试通知模型字段"""
        from app.models import Notification

        assert Notification.__tablename__ == "notifications"
        assert hasattr(Notification, "id")
        assert hasattr(Notification, "user_id")
        assert hasattr(Notification, "type")
        assert hasattr(Notification, "title")
        assert hasattr(Notification, "content")
        assert hasattr(Notification, "is_read")
        assert hasattr(Notification, "sent_at")
        assert hasattr(Notification, "created_at")

    def test_notification_settings_model_fields(self):
        """测试通知设置模型字段"""
        from app.models import NotificationSettings

        assert NotificationSettings.__tablename__ == "notification_settings"
        assert hasattr(NotificationSettings, "id")
        assert hasattr(NotificationSettings, "user_id")
        assert hasattr(NotificationSettings, "email_enabled")
        assert hasattr(NotificationSettings, "sms_enabled")
        assert hasattr(NotificationSettings, "push_enabled")
        assert hasattr(NotificationSettings, "quiet_hours_start")
        assert hasattr(NotificationSettings, "quiet_hours_end")


class TestNotificationServiceResponseContract:
    """通知服务响应格式契约测试"""

    def test_notification_response_schema(self):
        """测试通知响应格式"""
        from app.routers.notification import NotificationResponse
        from datetime import datetime, timezone

        response = NotificationResponse(
            id=1,
            user_id=1,
            type="system",
            title="测试通知",
            content="测试内容",
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )

        assert response.id == 1
        assert response.type == "system"
        assert isinstance(response.is_read, bool)

    def test_notification_list_response_schema(self):
        """测试通知列表响应格式"""
        from app.routers.notification import NotificationListResponse, NotificationResponse

        response = NotificationListResponse(
            items=[
                NotificationResponse(
                    id=1,
                    user_id=1,
                    type="system",
                    title="通知1",
                    is_read=False,
                    created_at=None
                )
            ],
            total=1,
            unread_count=1
        )

        assert len(response.items) == 1
        assert response.total == 1
        assert isinstance(response.unread_count, int)

    def test_settings_response_schema(self):
        """测试设置响应格式"""
        from app.routers.notification import SettingsResponse

        response = SettingsResponse(
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )

        assert response.email_enabled is True
        assert response.sms_enabled is False
        assert isinstance(response.quiet_hours_start, str)
