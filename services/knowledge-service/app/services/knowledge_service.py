"""知识库 Service 层"""
import os
import json
import logging
from datetime import datetime
from typing import Optional

try:
    from aiokafka import AIOKafkaProducer
except ImportError:
    AIOKafkaProducer = None

from sqlalchemy.orm import Session
from app.models.knowledge import LegalKnowledge
from app.services.knowledge_vector_store import add_knowledge, delete_knowledge
from services.common.events import (
    EventType,
    EventTopic,
    VectorSyncEvent,
    create_knowledge_event,
)

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识库 Service 类"""

    def __init__(self, db: Session):
        self.db = db
        self._kafka_enabled = os.getenv("KAFKA_ENABLED", "false").lower() in {"1", "true", "yes"}
        self._kafka_producer = None
        self._kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self._kafka_topic = os.getenv("KAFKA_TOPIC", "baixing.knowledge.events")

    async def _get_kafka_producer(self):
        if not self._kafka_enabled:
            return None
        if self._kafka_producer is None and AIOKafkaProducer:
            self._kafka_producer = AIOKafkaProducer(
                bootstrap_servers=self._kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._kafka_producer.start()
        return self._kafka_producer

    async def _close_kafka_producer(self):
        if self._kafka_producer:
            await self._kafka_producer.stop()
            self._kafka_producer = None

    async def _send_kafka_event(self, event: VectorSyncEvent):
        if not self._kafka_enabled:
            logger.info(f"Kafka disabled, skipping event: {event.event_type}")
            return

        producer = await self._get_kafka_producer()
        if not producer:
            logger.warning("Kafka producer not available")
            return

        try:
            await producer.send_and_wait(
                self._kafka_topic,
                value=event.to_json(),
                key=str(event.entity_id).encode("utf-8"),
            )
            logger.info(f"Published Kafka event: {event.event_type} for knowledge_id: {event.entity_id}")
        except Exception as e:
            logger.error(f"Failed to publish Kafka event: {e}")

    def _build_vector_document(self, knowledge: LegalKnowledge) -> dict:
        """构建向量文档"""
        return {
            "content": knowledge.content,
            "metadata": {
                "id": knowledge.id,
                "title": knowledge.title,
                "knowledge_type": knowledge.knowledge_type,
                "category": knowledge.category,
                "keywords": knowledge.keywords,
                "status": knowledge.status,
                "version": knowledge.version,
            }
        }

    async def _sync_vector_store(self, knowledge: LegalKnowledge, event_type: EventType):
        """同步向量存储并发送 Kafka 事件"""
        event_data = {
            "knowledge_id": knowledge.id,
            "title": knowledge.title,
            "knowledge_type": knowledge.knowledge_type,
            "status": knowledge.status,
            "version": knowledge.version,
        }
        event = VectorSyncEvent(
            topic=EventTopic.KNOWLEDGE,
            event_type=event_type,
            entity_id=knowledge.id,
            data=event_data,
        )
        await self._send_kafka_event(event)

    def create_knowledge(self, request) -> LegalKnowledge:
        """创建知识，状态=draft"""
        knowledge = LegalKnowledge(
            knowledge_type=request.knowledge_type,
            title=request.title,
            article_number=request.article_number,
            content=request.content,
            summary=request.summary,
            category=request.category,
            keywords=request.keywords,
            source=request.source,
            effective_date=request.effective_date,
            expiry_date=request.expiry_date,
            law_number=request.law_number,
            jurisdiction=request.jurisdiction,
            weight=request.weight,
            created_by=request.created_by,
            metadata=request.metadata,
            status="draft"
        )
        self.db.add(knowledge)
        self.db.commit()
        self.db.refresh(knowledge)
        return knowledge

    def get_knowledge(self, knowledge_id: int) -> Optional[LegalKnowledge]:
        """获取知识详情"""
        knowledge = self.db.query(LegalKnowledge).filter(
            LegalKnowledge.id == knowledge_id,
            LegalKnowledge.is_deleted == False
        ).first()
        return knowledge

    def update_knowledge(self, knowledge_id: int, request) -> Optional[LegalKnowledge]:
        """更新知识，version+1"""
        knowledge = self.get_knowledge(knowledge_id)
        if not knowledge:
            return None

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(knowledge, field, value)

        knowledge.version += 1
        self.db.commit()
        self.db.refresh(knowledge)
        return knowledge

    async def delete_knowledge(self, knowledge_id: int) -> bool:
        """软删除知识"""
        knowledge = self.get_knowledge(knowledge_id)
        if not knowledge:
            return False

        knowledge.is_deleted = True
        knowledge.deleted_at = datetime.now()
        knowledge.is_active = False
        self.db.commit()

        await self._sync_vector_store(knowledge, EventType.DELETED)
        return True

    async def publish_knowledge(self, knowledge_id: int, reviewed_by: Optional[int] = None) -> Optional[LegalKnowledge]:
        """发布知识，发送 Kafka 事件"""
        knowledge = self.get_knowledge(knowledge_id)
        if not knowledge:
            return None

        if knowledge.status not in ["draft", "pending_review"]:
            raise ValueError(f"无法从状态 '{knowledge.status}' 发布")

        knowledge.status = "published"
        knowledge.is_active = True
        knowledge.reviewed_by = reviewed_by
        knowledge.reviewed_at = datetime.now()
        knowledge.is_vectorized = False

        self.db.commit()
        self.db.refresh(knowledge)

        await self._sync_vector_store(knowledge, EventType.PUBLISHED)
        return knowledge

    async def unpublish_knowledge(self, knowledge_id: int) -> Optional[LegalKnowledge]:
        """下线知识，发送 Kafka 事件"""
        knowledge = self.get_knowledge(knowledge_id)
        if not knowledge:
            return None

        if knowledge.status != "published":
            raise ValueError("只能下线已发布的知识")

        knowledge.status = "archived"
        knowledge.is_active = False
        self.db.commit()
        self.db.refresh(knowledge)

        await self._sync_vector_store(knowledge, EventType.DELETED)
        return knowledge

    def submit_for_review(self, knowledge_id: int) -> Optional[LegalKnowledge]:
        """提交审核"""
        knowledge = self.get_knowledge(knowledge_id)
        if not knowledge:
            return None

        if knowledge.status not in ["draft"]:
            raise ValueError("只能提交草稿状态的知识的审核")

        knowledge.status = "pending_review"
        self.db.commit()
        self.db.refresh(knowledge)
        return knowledge

    async def rebuild_vector(self, knowledge_id: int) -> bool:
        """重建单个知识的向量索引"""
        knowledge = self.get_knowledge(knowledge_id)
        if not knowledge:
            return False

        if knowledge.status != "published":
            raise ValueError("只能重建已发布知识的向量索引")

        doc = self._build_vector_document(knowledge)
        vector_id = f"knowledge_{knowledge.id}_v{knowledge.version}"
        add_knowledge([doc], [vector_id])

        knowledge.is_vectorized = True
        knowledge.vector_id = vector_id
        knowledge.vector_indexed = True
        knowledge.vector_indexed_at = datetime.now()
        self.db.commit()

        await self._sync_vector_store(knowledge, EventType.UPDATED)
        return True

    async def rebuild_all_vectors(self) -> dict:
        """全量重建所有已发布知识的向量索引"""
        published_knowledge = self.db.query(LegalKnowledge).filter(
            LegalKnowledge.status == "published",
            LegalKnowledge.is_deleted == False,
            LegalKnowledge.is_active == True,
        ).all()

        rebuilt_count = 0
        failed_ids = []

        for knowledge in published_knowledge:
            try:
                doc = self._build_vector_document(knowledge)
                vector_id = f"knowledge_{knowledge.id}_v{knowledge.version}"
                add_knowledge([doc], [vector_id])

                knowledge.is_vectorized = True
                knowledge.vector_id = vector_id
                knowledge.vector_indexed = True
                knowledge.vector_indexed_at = datetime.now()
                rebuilt_count += 1
            except Exception as e:
                logger.error(f"Failed to rebuild vector for knowledge {knowledge.id}: {e}")
                failed_ids.append(knowledge.id)

        self.db.commit()

        return {
            "total": len(published_knowledge),
            "rebuilt": rebuilt_count,
            "failed": len(failed_ids),
            "failed_ids": failed_ids,
        }
