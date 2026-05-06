"""共享测试工具

提供测试辅助工具，支持：
- 测试数据库 fixture
- 模拟 Kafka Producer
- 模拟 Redis
- HTTP 测试客户端
- 断言辅助函数
"""
import os
import pytest
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport


class MockKafkaProducer:
    """模拟 Kafka Producer"""

    def __init__(self):
        self.sent_messages: list[dict] = []
        self._started = False

    async def start(self):
        self._started = True

    async def stop(self):
        self._started = False

    async def send_and_wait(self, topic: str, value: any, key: bytes = None):
        self.sent_messages.append({
            "topic": topic,
            "value": value,
            "key": key.decode() if key else None,
        })

    def send(self, topic: str, value: any, key: bytes = None):
        self.sent_messages.append({
            "topic": topic,
            "value": value,
            "key": key.decode() if key else None,
        })
        future = MagicMock()
        future.result.return_value = {"status": "success"}
        return future


class MockRedis:
    """模拟 Redis 客户端"""

    def __init__(self):
        self._store: dict[str, str] = {}
        self._ttls: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int = None):
        self._store[key] = value
        if ex:
            self._ttls[key] = ex

    async def setex(self, key: str, time: int, value: str):
        self._store[key] = value
        self._ttls[key] = time

    async def incr(self, key: str) -> int:
        current = int(self._store.get(key, 0))
        self._store[key] = str(current + 1)
        return current + 1

    async def ttl(self, key: str) -> int:
        return self._ttls.get(key, -1)

    async def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            if key in self._store:
                del self._store[key]
                self._ttls.pop(key, None)
                deleted += 1
        return deleted

    async def ping(self) -> bool:
        return True


def assert_response_success(response: any, status_code: int = 200):
    """断言响应成功"""
    assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"


def assert_error_response(response: any, expected_code: str, status_code: int = 400):
    """断言错误响应"""
    assert response.status_code == status_code
    data = response.json()
    assert data.get("code") == expected_code, f"Expected code {expected_code}, got {data.get('code')}"


def assert_pagination(response: any, expected_total: int, expected_page: int = 1, expected_page_size: int = 20):
    """断言分页响应"""
    data = response.json()
    assert data.get("total") == expected_total
    assert data.get("page") == expected_page
    assert data.get("page_size") == expected_page_size


@pytest.fixture
def mock_kafka_producer() -> MockKafkaProducer:
    """提供模拟 Kafka Producer"""
    return MockKafkaProducer()


@pytest.fixture
def mock_redis() -> MockRedis:
    """提供模拟 Redis 客户端"""
    return MockRedis()


@pytest.fixture
async def test_client(app) -> AsyncGenerator[AsyncClient, None]:
    """提供测试 HTTP 客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_db_url() -> str:
    """提供测试数据库 URL"""
    return os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/baixing_test")
