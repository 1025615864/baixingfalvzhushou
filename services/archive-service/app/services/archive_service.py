"""案例库服务层"""
import os
import json
import logging
import re
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

try:
    from aiokafka import AIOKafkaProducer
except ImportError:
    AIOKafkaProducer = None

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.archive import LegalCase
from app.services.archive_vector_store import add_archive, delete_archive

try:
    from services.common.events import (
        EventType,
        EventTopic,
        VectorSyncEvent,
        create_archive_event,
    )
except ImportError:
    import json as _json

    class EventType:
        PUBLISHED = "published"
        DELETED = "deleted"
        UPDATED = "updated"

    class EventTopic:
        ARCHIVE = "archive"

    class VectorSyncEvent:
        def __init__(self, topic, event_type, entity_id, data):
            self.topic = topic
            self.event_type = event_type
            self.entity_id = entity_id
            self.data = data

        def to_json(self):
            return _json.dumps({
                "topic": self.topic,
                "event_type": self.event_type,
                "entity_id": self.entity_id,
                "data": self.data,
            })

    def create_archive_event(event_type, case_id, data):
        return VectorSyncEvent(
            topic=EventTopic.ARCHIVE,
            event_type=event_type,
            entity_id=case_id,
            data=data,
        )

logger = logging.getLogger(__name__)


class ArchiveService:
    """案例库服务类"""

    def __init__(self, db: Session):
        self.db = db
        self._kafka_enabled = os.getenv("KAFKA_ENABLED", "false").lower() in {"1", "true", "yes"}
        self._kafka_producer = None
        self._kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self._kafka_topic = os.getenv("KAFKA_TOPIC", "baixing.archive.events")

    def _get_kafka_producer(self):
        if not self._kafka_enabled:
            return None
        if self._kafka_producer is None and AIOKafkaProducer:
            self._kafka_producer = AIOKafkaProducer(
                bootstrap_servers=self._kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        return self._kafka_producer

    def _close_kafka_producer(self):
        if self._kafka_producer:
            self._kafka_producer.stop()
            self._kafka_producer = None

    def _send_kafka_event(self, event: VectorSyncEvent):
        if not self._kafka_enabled:
            logger.info(f"Kafka disabled, skipping event: {event.event_type}")
            return

        producer = self._get_kafka_producer()
        if not producer:
            logger.warning("Kafka producer not available")
            return

        try:
            producer.send(
                self._kafka_topic,
                value=event.to_json(),
                key=str(event.entity_id).encode("utf-8"),
            )
            logger.info(f"Published Kafka event: {event.event_type} for case_id: {event.entity_id}")
        except Exception as e:
            logger.error(f"Failed to publish Kafka event: {e}")

    def create_case(self, request) -> LegalCase:
        """创建案例"""
        if request.case_number:
            existing = self.db.query(LegalCase).filter(
                LegalCase.case_number == request.case_number
            ).first()
            if existing:
                raise ValueError("案号已存在")

        case = LegalCase(
            case_number=request.case_number,
            case_type=request.case_type,
            title=request.title,
            facts=request.facts,
            legal_basis=request.legal_basis,
            judgment=request.judgment,
            result=request.result,
            category=request.category,
            keywords=request.keywords,
            court=request.court,
            court_level=request.court_level,
            judge_date=request.judge_date,
            cause_of_action=request.cause_of_action,
            judgment_result=request.judgment_result,
            key_points=request.key_points,
            applicable_laws=request.applicable_laws,
            source=request.source,
            source_url=request.source_url,
            is_guiding_case=request.is_guiding_case,
            effective_date=request.effective_date,
            expiry_date=request.expiry_date,
            weight=request.weight,
            created_by=request.created_by,
            meta_data=request.metadata,
            status="draft"
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def get_case(self, case_id: int) -> Optional[LegalCase]:
        """获取案例详情"""
        case = self.db.query(LegalCase).filter(
            LegalCase.id == case_id,
            LegalCase.is_deleted == False
        ).first()
        return case

    def update_case(self, case_id: int, request) -> LegalCase:
        """更新案例"""
        case = self.get_case(case_id)
        if not case:
            raise ValueError("案例不存在")

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case, field, value)

        case.version += 1
        self.db.commit()
        self.db.refresh(case)

        self._sync_vector_event(case, EventType.UPDATED)
        return case

    def delete_case(self, case_id: int) -> None:
        """删除案例(软删除)"""
        case = self.get_case(case_id)
        if not case:
            raise ValueError("案例不存在")

        case.is_deleted = True
        case.deleted_at = datetime.now()
        case.is_active = False
        self.db.commit()

        self._sync_vector_event(case, EventType.DELETED)

    def submit_for_review(self, case_id: int) -> LegalCase:
        """提交审核 - draft -> pending_review"""
        case = self.get_case(case_id)
        if not case:
            raise ValueError("案例不存在")

        if case.status != "draft":
            raise ValueError("只能提交草稿状态的案例")

        case.status = "pending_review"
        self.db.commit()
        self.db.refresh(case)
        return case

    def publish_case(self, case_id: int, reviewed_by: Optional[int] = None) -> LegalCase:
        """发布案例"""
        case = self.get_case(case_id)
        if not case:
            raise ValueError("案例不存在")

        if case.status not in ["draft", "pending_review"]:
            raise ValueError(f"无法从状态 '{case.status}' 发布")

        case.status = "published"
        case.is_active = True
        case.reviewed_by = reviewed_by
        case.reviewed_at = datetime.now()
        case.is_vectorized = False
        self.db.commit()
        self.db.refresh(case)

        self._sync_vector_event(case, EventType.PUBLISHED)
        return case

    def unpublish_case(self, case_id: int) -> LegalCase:
        """下线案例 - published -> archived"""
        case = self.get_case(case_id)
        if not case:
            raise ValueError("案例不存在")

        if case.status != "published":
            raise ValueError("只能下线已发布的案例")

        case.status = "archived"
        case.is_active = False
        self.db.commit()
        self.db.refresh(case)

        self._sync_vector_event(case, EventType.DELETED)
        return case

    def _build_case_data(self, case: LegalCase) -> dict:
        """构建案例数据字典"""
        return {
            "id": case.id,
            "case_number": case.case_number,
            "case_type": case.case_type,
            "title": case.title,
            "facts": case.facts,
            "legal_basis": case.legal_basis,
            "judgment": case.judgment,
            "result": case.result,
            "category": case.category,
            "keywords": case.keywords,
            "court": case.court,
            "court_level": case.court_level,
            "judge_date": case.judge_date.isoformat() if case.judge_date else None,
            "cause_of_action": case.cause_of_action,
            "judgment_result": case.judgment_result,
            "key_points": case.key_points,
            "applicable_laws": case.applicable_laws,
            "source": case.source,
            "source_url": case.source_url,
            "is_guiding_case": case.is_guiding_case,
            "version": case.version,
            "status": case.status,
        }

    def _sync_vector_event(self, case: LegalCase, event_type: EventType):
        """同步向量存储并发送 Kafka 事件"""
        event = create_archive_event(
            event_type=event_type,
            case_id=case.id,
            data=self._build_case_data(case)
        )
        self._send_kafka_event(event)

    def get_published_cases(self):
        """获取所有已发布的案例"""
        return self.db.query(LegalCase).filter(
            LegalCase.status == "published",
            LegalCase.is_deleted == False
        ).all()

    def rebuild_vector(self, case_id: int) -> dict:
        """重建单个案例的向量"""
        case = self.get_case(case_id)
        if not case:
            raise ValueError("案例不存在")

        if case.status != "published":
            raise ValueError("只能重建已发布案例的向量")

        content = self._build_searchable_content(case)
        doc = {
            "content": content,
            "metadata": {
                "case_id": case.id,
                "case_number": case.case_number,
                "title": case.title,
                "category": case.category,
                "court": case.court,
                "is_guiding_case": case.is_guiding_case
            }
        }

        vector_id = f"archive_{case.id}"
        try:
            add_archive([doc], [vector_id])
            case.is_vectorized = True
            case.vector_id = vector_id
            case.vector_indexed = True
            case.vector_indexed_at = datetime.now()
            self.db.commit()
            return {"case_id": case.id, "status": "success", "vector_id": vector_id}
        except Exception as e:
            case.is_vectorized = False
            self.db.commit()
            return {"case_id": case.id, "status": "failed", "error": str(e)}

    def rebuild_all_vectors(self) -> dict:
        """重建所有已发布案例的向量"""
        cases = self.get_published_cases()
        results = []
        for case in cases:
            try:
                result = self.rebuild_vector(case.id)
                results.append(result)
            except Exception as e:
                results.append({"case_id": case.id, "status": "failed", "error": str(e)})

        return {
            "total": len(cases),
            "results": results,
            "success_count": sum(1 for r in results if r.get("status") == "success"),
            "failed_count": sum(1 for r in results if r.get("status") == "failed")
        }

    def _build_searchable_content(self, case: LegalCase) -> str:
        """构建可搜索的内容"""
        parts = [
            case.title,
            case.facts,
            case.legal_basis or "",
            case.judgment or "",
            case.result or "",
            case.key_points or "",
            case.applicable_laws or "",
            case.keywords or ""
        ]
        return " | ".join(filter(None, parts))

    def _parse_court_document(self, text: str) -> Dict[str, Any]:
        """解析裁判文书格式，提取关键字段"""
        result = {}

        case_number_pattern = r'[\u4e00-\u9fa5]\d{4}\u5e74[\u4e00-\u9fa5]\u5b57?第\d+号'
        match = re.search(case_number_pattern, text)
        if match:
            result['case_number'] = match.group()

        court_pattern = r'(\u4e0a\u6d77\u5e02|\u5317\u4eac\u5e02|\u6df1\u5733\u5e02)?[\u4e00-\u9fa5]{2,10}\u4eba\u6c11\u6cd5\u9662'
        match = re.search(court_pattern, text)
        if match:
            result['court'] = match.group()

        date_pattern = r'\d{4}\u5e74\d{1,2}\u6708\d{1,2}\u65e5'
        match = re.search(date_pattern, text)
        if match:
            try:
                date_str = match.group()
                result['judge_date'] = datetime.strptime(date_str, '%Y年%m月%d日')
            except ValueError:
                pass

        return result

    def batch_create_cases(
        self,
        items: List,
        skip_duplicates: bool = True,
        parse_court_doc: bool = False
    ) -> Tuple[int, int, List[Dict]]:
        """批量创建案例

        Args:
            items: 案例数据列表
            skip_duplicates: 是否跳过重复案号
            parse_court_doc: 是否解析裁判文书格式

        Returns:
            (成功数, 失败数, 错误列表)
        """
        MAX_BATCH_SIZE = 200
        if len(items) > MAX_BATCH_SIZE:
            raise ValueError(f"单次批量导入最多{MAX_BATCH_SIZE}条数据")

        successful = 0
        failed = 0
        errors = []

        for idx, item in enumerate(items):
            try:
                if parse_court_doc:
                    parsed = self._parse_court_document(item.facts or item.title or "")
                    for key, value in parsed.items():
                        if not getattr(item, key, None):
                            setattr(item, key, value)

                if item.case_number:
                    existing = self.db.query(LegalCase).filter(
                        LegalCase.case_number == item.case_number
                    ).first()
                    if existing:
                        if skip_duplicates:
                            continue
                        else:
                            raise ValueError(f"案号 '{item.case_number}' 已存在")

                case = LegalCase(
                    case_number=item.case_number,
                    case_type=item.case_type,
                    title=item.title,
                    facts=item.facts,
                    legal_basis=item.legal_basis,
                    judgment=item.judgment,
                    result=item.result,
                    category=item.category,
                    keywords=item.keywords,
                    court=item.court,
                    court_level=item.court_level,
                    judge_date=item.judge_date,
                    cause_of_action=item.cause_of_action,
                    judgment_result=item.judgment_result,
                    key_points=item.key_points,
                    applicable_laws=item.applicable_laws,
                    source=item.source,
                    source_url=item.source_url,
                    is_guiding_case=item.is_guiding_case,
                    effective_date=item.effective_date,
                    expiry_date=item.expiry_date,
                    weight=item.weight,
                    created_by=item.created_by,
                    meta_data=item.metadata,
                    status="draft"
                )
                self.db.add(case)
                self.db.flush()
                successful += 1
            except IntegrityError as e:
                self.db.rollback()
                failed += 1
                errors.append({
                    "index": idx,
                    "case_number": getattr(item, 'case_number', None),
                    "error": f"数据库约束错误: {str(e)}"
                })
            except Exception as e:
                self.db.rollback()
                failed += 1
                errors.append({
                    "index": idx,
                    "case_number": getattr(item, 'case_number', None),
                    "error": str(e)
                })

        if successful > 0:
            self.db.commit()

        return successful, failed, errors

    def export_cases(
        self,
        court_level: Optional[str] = None,
        case_type: Optional[str] = None,
        cause_of_action: Optional[str] = None,
        is_guiding_case: Optional[bool] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[List[LegalCase], int]:
        """导出案例（支持筛选和分页）

        Args:
            court_level: 法院级别筛选
            case_type: 案件类型筛选
            cause_of_action: 案由筛选
            is_guiding_case: 是否为指导性案例
            date_from: 开始日期
            date_to: 结束日期
            page: 页码
            page_size: 每页数量

        Returns:
            (案例列表, 总数)
        """
        query = self.db.query(LegalCase).filter(
            LegalCase.is_deleted == False
        )

        if court_level:
            query = query.filter(LegalCase.court_level == court_level)
        if case_type:
            query = query.filter(LegalCase.case_type == case_type)
        if cause_of_action:
            query = query.filter(LegalCase.cause_of_action == cause_of_action)
        if is_guiding_case is not None:
            query = query.filter(LegalCase.is_guiding_case == is_guiding_case)
        if date_from:
            query = query.filter(LegalCase.judge_date >= date_from)
        if date_to:
            query = query.filter(LegalCase.judge_date <= date_to)

        total = query.count()

        offset = (page - 1) * page_size
        cases = query.order_by(LegalCase.created_at.desc()).offset(offset).limit(page_size).all()

        return cases, total
