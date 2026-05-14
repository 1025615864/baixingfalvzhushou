"""Outbox 模式实现

提供可靠的消息发布机制，确保数据库事务和消息发布的原子性。
支持：
- 消息持久化到 Outbox 表
- 可靠的消息发布（带重试）
- 消息去重和幂等性处理
- 发布状态跟踪
"""
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, Index, Boolean
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

Base = DeclarativeBase()


class OutboxStatus(str, Enum):
    """Outbox 消息状态"""
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


class OutboxMessage(Base):
    """Outbox 消息表"""
    __tablename__ = "outbox_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aggregate_type = Column(String(50), index=True)
    aggregate_id = Column(String(50), index=True)
    event_type = Column(String(50), index=True)
    topic = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)
    key = Column(String(100), nullable=True)
    status = Column(String(20), default=OutboxStatus.PENDING.value, index=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_outbox_status_created", "status", "created_at"),
        Index("ix_outbox_aggregate", "aggregate_type", "aggregate_id"),
        Index("ix_outbox_topic_status", "topic", "status"),
    )


class OutboxPublisher:
    """Outbox 发布器"""

    def __init__(self, db_session_factory, kafka_producer=None, max_retries: int = 3):
        self.db_session_factory = db_session_factory
        self.kafka_producer = kafka_producer
        self.max_retries = max_retries

    def save_message(
        self,
        db,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        topic: str,
        payload: dict,
        key: str = None,
    ) -> OutboxMessage:
        """保存消息到 Outbox 表（在事务内调用）"""
        message = OutboxMessage(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            topic=topic,
            payload=json.dumps(payload),
            key=key,
            status=OutboxStatus.PENDING.value,
            max_retries=self.max_retries,
        )
        db.add(message)
        return message

    async def publish_pending_messages(self, batch_size: int = 100) -> int:
        """发布待处理的消息"""
        db = self.db_session_factory()
        published_count = 0

        try:
            pending_messages = (
                db.query(OutboxMessage)
                .filter(OutboxMessage.status == OutboxStatus.PENDING.value)
                .order_by(OutboxMessage.created_at.asc())
                .limit(batch_size)
                .all()
            )

            for message in pending_messages:
                success = await self._publish_message(message)
                if success:
                    published_count += 1

            db.commit()
            logger.info(f"Published {published_count} outbox messages")
            return published_count

        except Exception as e:
            logger.error(f"Failed to publish outbox messages: {e}")
            db.rollback()
            return published_count

        finally:
            db.close()

    async def _publish_message(self, message: OutboxMessage) -> bool:
        """发布单条消息"""
        if not self.kafka_producer:
            logger.warning("Kafka producer not available, skipping message publish")
            return False

        try:
            payload = json.loads(message.payload)
            
            await self.kafka_producer.send_and_wait(
                message.topic,
                value=payload,
                key=message.key.encode() if message.key else None,
            )

            message.status = OutboxStatus.PUBLISHED.value
            message.published_at = datetime.now(timezone.utc)
            message.error_message = None
            logger.info(f"Published outbox message {message.id} to {message.topic}")
            return True

        except Exception as e:
            message.retry_count += 1
            message.error_message = str(e)

            if message.retry_count >= message.max_retries:
                message.status = OutboxStatus.FAILED.value
                logger.error(f"Failed to publish outbox message {message.id} after {message.retry_count} retries: {e}")
            else:
                logger.warning(f"Retry {message.retry_count}/{message.max_retries} for outbox message {message.id}: {e}")

            return False

    async def retry_failed_messages(self, batch_size: int = 50) -> int:
        """重试失败的消息"""
        db = self.db_session_factory()
        retried_count = 0

        try:
            failed_messages = (
                db.query(OutboxMessage)
                .filter(
                    OutboxMessage.status == OutboxStatus.FAILED.value,
                    OutboxMessage.retry_count < OutboxMessage.max_retries,
                )
                .order_by(OutboxMessage.updated_at.asc())
                .limit(batch_size)
                .all()
            )

            for message in failed_messages:
                message.status = OutboxStatus.PENDING.value
                message.error_message = None
                retried_count += 1

            db.commit()

            if retried_count > 0:
                await self.publish_pending_messages(batch_size=retried_count)

            logger.info(f"Retried {retried_count} failed outbox messages")
            return retried_count

        except Exception as e:
            logger.error(f"Failed to retry failed messages: {e}")
            db.rollback()
            return 0

        finally:
            db.close()

    def cleanup_old_messages(self, retention_days: int = 30) -> int:
        """清理旧消息"""
        db = self.db_session_factory()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        try:
            deleted = (
                db.query(OutboxMessage)
                .filter(
                    OutboxMessage.status == OutboxStatus.PUBLISHED.value,
                    OutboxMessage.published_at < cutoff_date,
                )
                .delete(synchronize_session=False)
            )
            db.commit()
            logger.info(f"Cleaned up {deleted} old outbox messages")
            return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup old messages: {e}")
            db.rollback()
            return 0
        finally:
            db.close()

    def get_stats(self) -> dict:
        """获取 Outbox 统计信息"""
        db = self.db_session_factory()
        try:
            total = db.query(OutboxMessage).count()
            pending = db.query(OutboxMessage).filter(
                OutboxMessage.status == OutboxStatus.PENDING.value
            ).count()
            published = db.query(OutboxMessage).filter(
                OutboxMessage.status == OutboxStatus.PUBLISHED.value
            ).count()
            failed = db.query(OutboxMessage).filter(
                OutboxMessage.status == OutboxStatus.FAILED.value
            ).count()

            return {
                "total": total,
                "pending": pending,
                "published": published,
                "failed": failed,
            }
        finally:
            db.close()
