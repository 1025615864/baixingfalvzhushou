"""Outbox 模式单元测试"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from services.common.outbox.publisher import (
    OutboxPublisher,
    OutboxMessage,
    OutboxStatus,
)


class MockDBSession:
    """模拟数据库会话"""

    def __init__(self):
        self.messages = []
        self.committed = False
        self.closed = False
        self.rolled_back = False

    def add(self, obj):
        self.messages.append(obj)

    def query(self, model):
        return MockQuery(self.messages)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class MockQuery:
    """模拟 SQLAlchemy 查询"""

    def __init__(self, data):
        self._data = data
        self._filters = []
        self._order = None
        self._limit = None

    def filter(self, *conditions):
        self._filters.extend(conditions)
        return self

    def order_by(self, order):
        self._order = order
        return self

    def limit(self, limit):
        self._limit = limit
        return self

    def all(self):
        results = self._data[:]
        if self._limit:
            results = results[:self._limit]
        return results

    def count(self):
        return len(self._data)

    def delete(self, synchronize_session=False):
        count = len(self._data)
        self._data.clear()
        return count


def mock_db_session_factory():
    """创建模拟数据库会话工厂"""
    return MockDBSession


class TestOutboxMessage:
    """Outbox 消息模型测试"""

    def test_create_message(self):
        """测试创建消息"""
        message = OutboxMessage(
            aggregate_type="order",
            aggregate_id="order-123",
            event_type="order.created",
            topic="order-events",
            payload=json.dumps({"order_id": "123", "amount": 100.0}),
            key="order-123",
            status=OutboxStatus.PENDING.value,
        )

        assert message.aggregate_type == "order"
        assert message.aggregate_id == "order-123"
        assert message.event_type == "order.created"
        assert message.topic == "order-events"
        assert message.status == "pending"
        assert message.retry_count == 0
        assert message.max_retries == 3

    def test_message_default_values(self):
        """测试消息默认值"""
        message = OutboxMessage(
            aggregate_type="user",
            aggregate_id="user-456",
            event_type="user.registered",
            topic="user-events",
            payload=json.dumps({"user_id": "456"}),
        )

        assert message.status == "pending"
        assert message.retry_count == 0
        assert message.max_retries == 3
        assert message.key is None


class TestOutboxPublisher:
    """Outbox 发布器测试"""

    @pytest.fixture
    def publisher(self):
        """创建测试发布器"""
        return OutboxPublisher(
            db_session_factory=mock_db_session_factory(),
            kafka_producer=None,
            max_retries=3,
        )

    @pytest.fixture
    def publisher_with_kafka(self):
        """创建带 Kafka 的测试发布器"""
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        return OutboxPublisher(
            db_session_factory=mock_db_session_factory(),
            kafka_producer=mock_producer,
            max_retries=3,
        )

    def test_save_message(self, publisher):
        """测试保存消息到 Outbox"""
        db = MockDBSession()

        message = publisher.save_message(
            db=db,
            aggregate_type="order",
            aggregate_id="order-123",
            event_type="order.created",
            topic="order-events",
            payload={"order_id": "123", "amount": 100.0},
            key="order-123",
        )

        assert len(db.messages) == 1
        assert message.aggregate_type == "order"
        assert message.status == "pending"

    def test_save_message_with_optional_key(self, publisher):
        """测试保存不带 key 的消息"""
        db = MockDBSession()

        message = publisher.save_message(
            db=db,
            aggregate_type="user",
            aggregate_id="user-456",
            event_type="user.updated",
            topic="user-events",
            payload={"user_id": "456"},
        )

        assert message.key is None

    @pytest.mark.asyncio
    async def test_publish_without_kafka(self, publisher):
        """测试无 Kafka 时跳过发布"""
        result = await publisher.publish_pending_messages()
        assert result == 0

    @pytest.mark.asyncio
    async def test_publish_with_kafka(self, publisher_with_kafka):
        """测试使用 Kafka 发布消息"""
        db = MockDBSession()
        message = OutboxMessage(
            aggregate_type="order",
            aggregate_id="order-123",
            event_type="order.created",
            topic="order-events",
            payload=json.dumps({"order_id": "123"}),
            key="order-123",
            status=OutboxStatus.PENDING.value,
        )
        db.messages.append(message)

        result = await publisher_with_kafka.publish_pending_messages()
        assert result == 1
        assert publisher_with_kafka.kafka_producer.send_and_wait.called

    @pytest.mark.asyncio
    async def test_publish_message_failure(self, publisher_with_kafka):
        """测试消息发布失败时的重试逻辑"""
        db = MockDBSession()
        message = OutboxMessage(
            aggregate_type="order",
            aggregate_id="order-456",
            event_type="order.created",
            topic="order-events",
            payload=json.dumps({"order_id": "456"}),
            status=OutboxStatus.PENDING.value,
            max_retries=3,
        )
        db.messages.append(message)

        publisher_with_kafka.kafka_producer.send_and_wait.side_effect = Exception("Kafka error")

        result = await publisher_with_kafka.publish_pending_messages()
        assert result == 0
        assert message.retry_count == 1
        assert message.error_message == "Kafka error"

    @pytest.mark.asyncio
    async def test_publish_exceeds_max_retries(self, publisher_with_kafka):
        """测试超过最大重试次数后标记为失败"""
        db = MockDBSession()
        message = OutboxMessage(
            aggregate_type="order",
            aggregate_id="order-789",
            event_type="order.created",
            topic="order-events",
            payload=json.dumps({"order_id": "789"}),
            status=OutboxStatus.PENDING.value,
            max_retries=1,
            retry_count=0,
        )
        db.messages.append(message)

        publisher_with_kafka.kafka_producer.send_and_wait.side_effect = Exception("Kafka error")

        result = await publisher_with_kafka.publish_pending_messages()
        assert result == 0
        assert message.status == "failed"

    @pytest.mark.asyncio
    async def test_retry_failed_messages(self, publisher_with_kafka):
        """测试重试失败的消息"""
        db = MockDBSession()
        failed_message = OutboxMessage(
            aggregate_type="order",
            aggregate_id="order-fail",
            event_type="order.created",
            topic="order-events",
            payload=json.dumps({"order_id": "fail"}),
            status=OutboxStatus.FAILED.value,
            retry_count=0,
            max_retries=3,
        )
        db.messages.append(failed_message)

        publisher_with_kafka.kafka_producer.send_and_wait = AsyncMock()

        result = await publisher_with_kafka.retry_failed_messages()
        assert result == 1
        assert failed_message.status == "pending"
        assert failed_message.error_message is None

    def test_cleanup_old_messages(self, publisher):
        """测试清理旧消息"""
        db = MockDBSession()
        old_message = OutboxMessage(
            aggregate_type="order",
            aggregate_id="order-old",
            event_type="order.created",
            topic="order-events",
            payload=json.dumps({}),
            status=OutboxStatus.PUBLISHED.value,
            published_at=datetime.utcnow() - timedelta(days=60),
        )
        db.messages.append(old_message)

        result = publisher.cleanup_old_messages(retention_days=30)
        assert result == 1
        assert len(db.messages) == 0

    def test_cleanup_preserves_recent_messages(self, publisher):
        """测试清理时保留最近的消息"""
        db = MockDBSession()
        recent_message = OutboxMessage(
            aggregate_type="order",
            aggregate_id="order-recent",
            event_type="order.created",
            topic="order-events",
            payload=json.dumps({}),
            status=OutboxStatus.PUBLISHED.value,
            published_at=datetime.utcnow() - timedelta(days=10),
        )
        db.messages.append(recent_message)

        result = publisher.cleanup_old_messages(retention_days=30)
        assert result == 0
        assert len(db.messages) == 1

    def test_get_stats(self, publisher):
        """测试获取统计信息"""
        db = MockDBSession()
        db.messages = [
            OutboxMessage(
                aggregate_type="order", aggregate_id="1",
                event_type="order.created", topic="order-events",
                payload=json.dumps({}), status=OutboxStatus.PENDING.value,
            ),
            OutboxMessage(
                aggregate_type="order", aggregate_id="2",
                event_type="order.created", topic="order-events",
                payload=json.dumps({}), status=OutboxStatus.PUBLISHED.value,
            ),
            OutboxMessage(
                aggregate_type="order", aggregate_id="3",
                event_type="order.created", topic="order-events",
                payload=json.dumps({}), status=OutboxStatus.FAILED.value,
            ),
        ]

        stats = publisher.get_stats()

        assert stats["total"] == 3
        assert stats["pending"] == 1
        assert stats["published"] == 1
        assert stats["failed"] == 1

    def test_outbox_status_enum(self):
        """测试 OutboxStatus 枚举"""
        assert OutboxStatus.PENDING.value == "pending"
        assert OutboxStatus.PUBLISHED.value == "published"
        assert OutboxStatus.FAILED.value == "failed"
