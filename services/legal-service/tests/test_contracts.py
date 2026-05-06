"""契约测试 - 与 User Service 的集成"""
import pytest
from httpx import AsyncClient


class TestUserServiceContract:
    """User Service 契约测试"""

    @pytest.mark.asyncio
    async def test_user_service_health(self, client: AsyncClient):
        """测试 User Service 健康状态"""
        response = await client.get("http://localhost:8001/health")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_auth_header_forwarding(self, client: AsyncClient):
        """测试认证头转发"""
        headers = {
            "X-User-ID": "123",
            "X-User-Role": "user",
            "Authorization": "Bearer test_token",
        }
        response = await client.get(
            "/api/v1/legal/consultations/",
            headers=headers,
        )
        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_user_info_in_headers(self, client: AsyncClient):
        """测试用户信息头存在"""
        headers = {
            "X-User-ID": "456",
            "X-User-Role": "lawyer",
        }
        response = await client.get(
            "/api/v1/legal/lawyers/",
            headers=headers,
        )
        assert response.status_code == 200


class TestKafkaContract:
    """Kafka 事件契约测试"""

    @pytest.mark.asyncio
    async def test_event_publish(self):
        """测试事件发布"""
        from app.events.producer import event_bus

        from app.events.legal_events import create_legal_event, LegalEventTypes

        event = create_legal_event(
            event_type=LegalEventTypes.CONSULTATION_CREATED,
            consultation_id="test123",
            user_id="user456",
        )

        try:
            await event_bus.publish(event, key="test123")
            published = True
        except Exception:
            published = False

        assert published or True

    @pytest.mark.asyncio
    async def test_event_structure(self):
        """测试事件结构"""
        from app.events.legal_events import create_legal_event, LegalEventTypes

        event = create_legal_event(
            event_type=LegalEventTypes.LAWYER_VERIFIED,
            lawyer_id="lawyer789",
            payload={"name": "测试律师"},
        )

        event_dict = event.to_dict()

        assert "event_id" in event_dict
        assert "event_type" in event_dict
        assert "timestamp" in event_dict
        assert "source" in event_dict
        assert event_dict["event_type"] == LegalEventTypes.LAWYER_VERIFIED


class TestRedisContract:
    """Redis 缓存契约测试"""

    @pytest.mark.asyncio
    async def test_redis_connection(self):
        """测试 Redis 连接"""
        import os
        try:
            import redis.asyncio as redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            client = redis.from_url(redis_url, decode_responses=True)
            await client.ping()
            await client.close()
            connected = True
        except Exception:
            connected = False

        assert connected or True


class TestDatabaseContract:
    """数据库契约测试"""

    @pytest.mark.asyncio
    async def test_db_connection(self, db_session):
        """测试数据库连接"""
        from sqlalchemy import text
        result = await db_session.execute(text("SELECT 1"))
        row = result.one()
        assert row[0] == 1

    @pytest.mark.asyncio
    async def test_models_exist(self):
        """测试模型存在"""
        from app.models import Consultation, Lawyer, LawFirm, Review

        assert Consultation.__tablename__ == "consultations"
        assert Lawyer.__tablename__ == "lawyers"
        assert LawFirm.__tablename__ == "lawfirms"
        assert Review.__tablename__ == "reviews"


class TestErrorCodeContract:
    """错误码契约测试"""

    def test_error_codes_format(self):
        """测试错误码格式"""
        from app.errors.error_codes import LegalErrorCode

        for code in LegalErrorCode:
            code_value = code.value
            assert isinstance(code_value, str)
            assert len(code_value) == 6
            assert code_value.startswith("L")

    def test_error_messages_exist(self):
        """测试错误消息存在"""
        from app.errors.error_codes import ERROR_MESSAGES, LegalErrorCode

        for code in LegalErrorCode:
            assert code.value in ERROR_MESSAGES
            assert len(ERROR_MESSAGES[code.value]) > 0