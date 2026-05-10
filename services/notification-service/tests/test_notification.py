import pytest
from app.models import Notification, NotificationSettings


class TestHealthEndpoints:

    @pytest.mark.asyncio
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "notification-service"

    @pytest.mark.asyncio
    async def test_readiness(self, client):
        response = await client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    @pytest.mark.asyncio
    async def test_liveness(self, client):
        response = await client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"


class TestNotificationList:

    @pytest.mark.asyncio
    async def test_list_notifications(self, client, db_session):
        notification = Notification(
            user_id=1,
            type="system",
            title="系统通知",
            content="这是一条系统通知",
            is_read=False,
        )
        db_session.add(notification)
        await db_session.commit()

        response = await client.get("/api/v1/notifications/?user_id=1")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "unread_count" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_notifications_unread_only(self, client, db_session):
        read_notif = Notification(
            user_id=2,
            type="system",
            title="已读通知",
            content="已读",
            is_read=True,
        )
        unread_notif = Notification(
            user_id=2,
            type="system",
            title="未读通知",
            content="未读",
            is_read=False,
        )
        db_session.add_all([read_notif, unread_notif])
        await db_session.commit()

        response = await client.get("/api/v1/notifications/?user_id=2&unread_only=true")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["is_read"] is False

    @pytest.mark.asyncio
    async def test_list_notifications_with_pagination(self, client, db_session):
        for i in range(5):
            notification = Notification(
                user_id=3,
                type="system",
                title=f"通知{i}",
                content=f"内容{i}",
                is_read=False,
            )
            db_session.add(notification)
        await db_session.commit()

        response = await client.get("/api/v1/notifications/?user_id=3&page=1&page_size=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 3

    @pytest.mark.asyncio
    async def test_list_notifications_empty(self, client):
        response = await client.get("/api/v1/notifications/?user_id=9999")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestNotificationCreate:

    @pytest.mark.asyncio
    async def test_create_notification(self, client, db_session):
        response = await client.post(
            "/api/v1/notifications/",
            json={
                "user_id": 10,
                "type": "consultation_reply",
                "title": "律师回复通知",
                "content": "张律师已回复您的咨询",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 10
        assert data["type"] == "consultation_reply"
        assert data["title"] == "律师回复通知"
        assert data["is_read"] is False

    @pytest.mark.asyncio
    async def test_create_batch_notifications(self, client, db_session):
        response = await client.post(
            "/api/v1/notifications/batch",
            params={
                "user_ids": [20, 21, 22],
                "type": "system_announcement",
                "title": "系统公告",
                "content": "系统将于今晚维护",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 3

    @pytest.mark.asyncio
    async def test_create_notification_missing_fields(self, client):
        response = await client.post(
            "/api/v1/notifications/",
            json={"user_id": 1},
        )
        assert response.status_code == 422


class TestNotificationRead:

    @pytest.mark.asyncio
    async def test_mark_as_read(self, client, db_session):
        notification = Notification(
            user_id=30,
            type="system",
            title="标记已读测试",
            content="内容",
            is_read=False,
        )
        db_session.add(notification)
        await db_session.commit()

        response = await client.patch(f"/api/v1/notifications/{notification.id}/read")
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, client):
        response = await client.patch("/api/v1/notifications/99999/read")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, client, db_session):
        for i in range(3):
            notification = Notification(
                user_id=40,
                type="system",
                title=f"批量已读{i}",
                content="内容",
                is_read=False,
            )
            db_session.add(notification)
        await db_session.commit()

        response = await client.patch("/api/v1/notifications/read-all?user_id=40")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] >= 3


class TestUnreadCount:

    @pytest.mark.asyncio
    async def test_get_unread_count(self, client, db_session):
        for i in range(2):
            notification = Notification(
                user_id=50,
                type="system",
                title=f"未读{i}",
                content="内容",
                is_read=False,
            )
            db_session.add(notification)
        read_notif = Notification(
            user_id=50,
            type="system",
            title="已读",
            content="内容",
            is_read=True,
        )
        db_session.add(read_notif)
        await db_session.commit()

        response = await client.get("/api/v1/notifications/unread-count?user_id=50")
        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] >= 2
        assert data["user_id"] == 50


class TestNotificationDetail:

    @pytest.mark.asyncio
    async def test_get_notification(self, client, db_session):
        notification = Notification(
            user_id=60,
            type="payment_success",
            title="支付成功",
            content="您已成功支付100元",
            is_read=False,
        )
        db_session.add(notification)
        await db_session.commit()

        response = await client.get(f"/api/v1/notifications/{notification.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == notification.id
        assert data["title"] == "支付成功"
        assert data["type"] == "payment_success"

    @pytest.mark.asyncio
    async def test_get_notification_not_found(self, client):
        response = await client.get("/api/v1/notifications/99999")
        assert response.status_code == 404


class TestNotificationDelete:

    @pytest.mark.asyncio
    async def test_delete_notification(self, client, db_session):
        notification = Notification(
            user_id=70,
            type="system",
            title="待删除通知",
            content="内容",
            is_read=False,
        )
        db_session.add(notification)
        await db_session.commit()

        response = await client.delete(f"/api/v1/notifications/{notification.id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_delete_notification_not_found(self, client):
        response = await client.delete("/api/v1/notifications/99999")
        assert response.status_code == 404


class TestNotificationSettings:

    @pytest.mark.asyncio
    async def test_get_settings(self, client, db_session):
        settings = NotificationSettings(
            user_id=80,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
        )
        db_session.add(settings)
        await db_session.commit()

        response = await client.get("/api/v1/notifications/settings?user_id=80")
        assert response.status_code == 200
        data = response.json()
        assert data["email_enabled"] is True
        assert data["sms_enabled"] is False
        assert data["push_enabled"] is True

    @pytest.mark.asyncio
    async def test_get_settings_auto_create(self, client, db_session):
        response = await client.get("/api/v1/notifications/settings?user_id=9999")
        assert response.status_code == 200
        data = response.json()
        assert "email_enabled" in data
        assert "sms_enabled" in data
        assert "push_enabled" in data

    @pytest.mark.asyncio
    async def test_update_settings(self, client, db_session):
        settings = NotificationSettings(
            user_id=90,
            email_enabled=True,
            sms_enabled=True,
            push_enabled=True,
        )
        db_session.add(settings)
        await db_session.commit()

        response = await client.put(
            "/api/v1/notifications/settings?user_id=90",
            json={
                "email_enabled": False,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email_enabled"] is False
        assert data["quiet_hours_start"] == "22:00"
        assert data["quiet_hours_end"] == "08:00"


class TestNotificationTemplates:

    @pytest.mark.asyncio
    async def test_list_templates(self, client):
        response = await client.get("/api/v1/notifications/templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)
        assert len(data["templates"]) > 0

    @pytest.mark.asyncio
    async def test_render_template(self, client):
        response = await client.post(
            "/api/v1/notifications/template/system_announcement/render",
            json={"title": "系统升级公告", "content": "系统将于今晚进行升级"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "系统升级公告"
        assert data["content"] == "系统将于今晚进行升级"

    @pytest.mark.asyncio
    async def test_render_template_not_found(self, client):
        response = await client.post(
            "/api/v1/notifications/template/nonexistent_template/render",
            json={"key": "value"},
        )
        assert response.status_code == 404
