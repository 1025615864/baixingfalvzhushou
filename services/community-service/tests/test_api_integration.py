"""社区服务 API 集成测试"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.database import Base, engine, AsyncSessionLocal
from app.models.post import Post
from app.models.comment import Comment
from app.models.topic import Topic


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database):
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_user_client():
    mock = MagicMock()
    mock.get_user_info = AsyncMock(return_value={
        "id": 1,
        "nickname": "测试用户",
        "avatar": "http://example.com/avatar.png",
        "is_lawyer": False
    })
    mock.verify_token = AsyncMock(return_value={
        "user_id": 1,
        "role": "user",
        "nickname": "测试用户"
    })
    return mock


@pytest.fixture
def mock_event_bus():
    mock = MagicMock()
    mock.publish_post_created = AsyncMock()
    mock.publish_post_updated = AsyncMock()
    mock.publish_post_deleted = AsyncMock()
    mock.publish_post_liked = AsyncMock()
    mock.publish_comment_created = AsyncMock()
    return mock


class TestHealthEndpoints:
    def test_liveness(self, client):
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "uptime" in data

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestPostEndpoints:
    def test_list_posts(self, client):
        response = client.get("/api/v1/community/posts/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_list_posts_with_sort(self, client):
        response = client.get("/api/v1/community/posts/?sort_by=hot")
        assert response.status_code == 200

        response = client.get("/api/v1/community/posts/?sort_by=featured")
        assert response.status_code == 200

        response = client.get("/api/v1/community/posts/?sort_by=latest")
        assert response.status_code == 200

    def test_list_posts_invalid_sort(self, client):
        response = client.get("/api/v1/community/posts/?sort_by=invalid")
        assert response.status_code == 422

    def test_search_posts_validation(self, client):
        response = client.get("/api/v1/community/posts/search/?q=a")
        assert response.status_code == 422

        response = client.get("/api/v1/community/posts/search/?q=法律")
        assert response.status_code == 200

    def test_get_categories(self, client):
        response = client.get("/api/v1/community/posts/categories/")
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)
        assert "general" in categories


class TestCommentEndpoints:
    def test_list_comments_validation(self, client):
        response = client.get("/api/v1/community/comments/?post_id=1")
        assert response.status_code == 200


class TestHotEndpoints:
    def test_get_hot_posts(self, client):
        response = client.get("/api/v1/community/hot/posts")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestReportEndpoints:
    def test_list_reports_requires_auth(self, client):
        response = client.get("/api/v1/community/reports/")
        assert response.status_code == 401


class TestMetricsEndpoints:
    def test_get_metrics(self, client):
        response = client.get("/metrics/")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "post" in data
        assert "api" in data
        assert "cache" in data

    def test_reset_metrics(self, client):
        response = client.post("/metrics/reset")
        assert response.status_code == 200
        assert response.json()["message"] == "Metrics reset successfully"


class TestModerationService:
    def test_sensitive_word_filter(self):
        from app.services.moderation_service import ModerationService
        from app.utils.sensitive_words import SensitiveWordFilter

        service = ModerationService()
        result = service.sensitive_filter.check("包含赌博和毒品的内容")
        assert result[0] is True
        assert len(result[1]) > 0

    def test_contact_info_detection(self):
        from app.services.moderation_service import ModerationService

        service = ModerationService()

        assert service.check_contact_info("电话：13812345678") is True
        assert service.check_contact_info("微信：lawyer123") is True
        assert service.check_contact_info("邮箱：test@example.com") is True
        assert service.check_contact_info("正常内容") is False

    def test_content_filtering(self):
        from app.services.moderation_service import ModerationService

        service = ModerationService()

        blocked_result = asyncio.get_event_loop().run_until_complete(
            service.check_content("毒品和赌博网站")
        )
        assert blocked_result.blocked is True


class TestScoringUtils:
    def test_hot_score_calculation(self):
        from app.utils.scoring import calculate_hot_score

        score = calculate_hot_score(
            likes=10,
            comments=5,
            views=100,
            favorites=2
        )
        assert score > 0

    def test_lawyer_bonus(self):
        from app.utils.scoring import calculate_hot_score

        regular = calculate_hot_score(
            likes=10, comments=5, views=100, favorites=2, is_lawyer_post=False
        )
        lawyer = calculate_hot_score(
            likes=10, comments=5, views=100, favorites=2, is_lawyer_post=True
        )
        assert lawyer > regular

    def test_time_decay(self):
        from app.utils.scoring import calculate_hot_score

        old_score = calculate_hot_score(
            likes=100, comments=50, views=10000, favorites=20,
            created_at=datetime(2020, 1, 1, tzinfo=timezone.utc)
        )
        new_score = calculate_hot_score(
            likes=100, comments=50, views=10000, favorites=20,
            created_at=datetime.now(timezone.utc)
        )
        assert new_score > old_score


class TestTopicService:
    def test_topic_service_creation(self):
        from app.services.topic_service import TopicService
        from app.database import AsyncSessionLocal

        session = AsyncSessionLocal()
        service = TopicService(session)
        assert service.db is not None


class TestBestAnswerService:
    def test_best_answer_service_creation(self):
        from app.services.topic_service import BestAnswerService
        from app.database import AsyncSessionLocal

        session = AsyncSessionLocal()
        service = BestAnswerService(session)
        assert service.db is not None


class TestPostCache:
    def test_cache_key_generation(self):
        from app.cache.post_cache import PostCache

        cache = PostCache()
        assert cache.detail_ttl == 600
        assert cache.list_ttl == 300


class TestMetricsCollector:
    def test_metrics_collector_singleton(self):
        from app.services.metrics import get_metrics_collector, CommunityMetricsCollector

        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is collector2

    @pytest.mark.asyncio
    async def test_record_api_request(self):
        from app.services.metrics import get_metrics_collector

        collector = get_metrics_collector()
        await collector.record_api_request(
            endpoint="/api/v1/community/posts/",
            status_code=200,
            latency_ms=50,
            success=True
        )
        metrics = await collector.get_metrics()
        assert metrics["api"]["total_requests"] >= 1


class TestAuthMiddleware:
    def test_auth_user_dataclass(self):
        from app.middleware.auth import AuthUser

        user = AuthUser(
            id=1,
            role="user",
            nickname="测试",
            is_lawyer=False
        )
        assert user.id == 1
        assert user.role == "user"
        assert user.is_lawyer is False


class TestErrorCodes:
    def test_community_error_codes(self):
        from app.errors.error_codes import ErrorCode

        assert ErrorCode.POST_NOT_FOUND[0] == "C40401"
        assert ErrorCode.POST_NO_PERMISSION[0] == "C40301"
        assert ErrorCode.CONTENT_BLOCKED[0] == "C42201"
        assert ErrorCode.RATE_LIMITED[0] == "C42901"


class TestSensitiveWords:
    def test_sensitive_word_filter(self):
        from app.utils.sensitive_words import SensitiveWordFilter

        filter = SensitiveWordFilter()

        blocked, words = filter.check("这个网站包含赌博内容")
        assert blocked is True
        assert len(words) > 0

        clean, clean_words = filter.check("正常法律咨询内容")
        assert clean is False
        assert len(clean_words) == 0

    def test_filter_replacement(self):
        from app.utils.sensitive_words import SensitiveWordFilter

        filter = SensitiveWordFilter()
        result = filter.filter("包含毒品的内容", replace_char="#")
        assert "毒品" not in result
        assert "#" in result


class TestRateLimiter:
    def test_rate_limiter_creation(self):
        from app.middleware.rate_limit import rate_limiter
        assert rate_limiter is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
