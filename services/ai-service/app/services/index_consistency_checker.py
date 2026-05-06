"""索引一致性校验服务"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyReport:
    """一致性报告"""
    service: str
    total_in_db: int
    total_in_vector: int
    missing_in_vector: List[int]
    orphaned_in_vector: List[int]
    inconsistent_status: List[int]
    checked_at: datetime


class IndexConsistencyChecker:
    """索引一致性校验服务"""

    def __init__(self):
        self._last_report: Optional[ConsistencyReport] = None

    def _get_knowledge_indexed_ids(self) -> set:
        """获取向量库中知识ID列表"""
        try:
            from app.services.knowledge_vector_store import get_all_knowledge_ids
            return set(get_all_knowledge_ids())
        except Exception as e:
            logger.error(f"Failed to get knowledge indexed IDs: {e}")
            return set()

    def _get_archive_indexed_ids(self) -> set:
        """获取向量库中案例ID列表"""
        try:
            from app.services.archive_vector_store import get_all_archive_ids
            return set(get_all_archive_ids())
        except Exception as e:
            logger.error(f"Failed to get archive indexed IDs: {e}")
            return set()

    def _get_published_knowledge_ids(self) -> set:
        """获取PG中已发布知识ID"""
        try:
            from app.database import engine
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT id FROM legal_knowledge WHERE status = 'published' AND is_deleted = false")
                )
                return {row[0] for row in result}
        except Exception as e:
            logger.error(f"Failed to get published knowledge IDs: {e}")
            return set()

    def _get_published_archive_ids(self) -> set:
        """获取PG中已发布案例ID"""
        try:
            from app.database import engine
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT id FROM legal_case WHERE status = 'published' AND is_deleted = false")
                )
                return {row[0] for row in result}
        except Exception as e:
            logger.error(f"Failed to get published archive IDs: {e}")
            return set()

    def check_knowledge_consistency(self) -> Dict:
        """检查知识库一致性"""
        db_ids = self._get_published_knowledge_ids()
        vector_ids = self._get_knowledge_indexed_ids()

        missing_in_vector = list(db_ids - vector_ids)
        orphaned_in_vector = list(vector_ids - db_ids)

        self._last_report = ConsistencyReport(
            service="knowledge",
            total_in_db=len(db_ids),
            total_in_vector=len(vector_ids),
            missing_in_vector=missing_in_vector,
            orphaned_in_vector=orphaned_in_vector,
            inconsistent_status=[],
            checked_at=datetime.now()
        )

        return self._format_report(self._last_report)

    def check_archive_consistency(self) -> Dict:
        """检查案例库一致性"""
        db_ids = self._get_published_archive_ids()
        vector_ids = self._get_archive_indexed_ids()

        missing_in_vector = list(db_ids - vector_ids)
        orphaned_in_vector = list(vector_ids - db_ids)

        self._last_report = ConsistencyReport(
            service="archive",
            total_in_db=len(db_ids),
            total_in_vector=len(vector_ids),
            missing_in_vector=missing_in_vector,
            orphaned_in_vector=orphaned_in_vector,
            inconsistent_status=[],
            checked_at=datetime.now()
        )

        return self._format_report(self._last_report)

    def generate_consistency_report(self, service: str = "both") -> Dict:
        """生成一致性报告"""
        if service == "knowledge":
            return self.check_knowledge_consistency()
        elif service == "archive":
            return self.check_archive_consistency()
        else:
            knowledge_report = self.check_knowledge_consistency()
            archive_report = self.check_archive_consistency()
            return {
                "knowledge": knowledge_report,
                "archive": archive_report,
                "generated_at": datetime.now().isoformat()
            }

    def get_last_report(self) -> Optional[Dict]:
        """获取最新报告"""
        if self._last_report:
            return self._format_report(self._last_report)
        return None

    def _format_report(self, report: ConsistencyReport) -> Dict:
        """格式化报告"""
        return {
            "service": report.service,
            "total_in_db": report.total_in_db,
            "total_in_vector": report.total_in_vector,
            "missing_in_vector": report.missing_in_vector,
            "missing_count": len(report.missing_in_vector),
            "orphaned_in_vector": report.orphaned_in_vector,
            "orphaned_count": len(report.orphaned_in_vector),
            "inconsistent_status": report.inconsistent_status,
            "inconsistent_count": len(report.inconsistent_status),
            "is_consistent": len(report.missing_in_vector) == 0 and len(report.orphaned_in_vector) == 0,
            "checked_at": report.checked_at.isoformat()
        }

    def fix_missing_vectors(self, service: str) -> Dict:
        """修复缺失的向量"""
        if service == "knowledge":
            report = self.check_knowledge_consistency()
            missing_ids = report["missing_in_vector"]
        elif service == "archive":
            report = self.check_archive_consistency()
            missing_ids = report["missing_in_vector"]
        else:
            return {"error": "Invalid service"}

        if not missing_ids:
            return {"message": "No missing vectors to fix", "fixed_count": 0}

        fixed_count = 0
        failed_ids = []

        for entity_id in missing_ids:
            try:
                if service == "knowledge":
                    self._rebuild_knowledge_vector(entity_id)
                else:
                    self._rebuild_archive_vector(entity_id)
                fixed_count += 1
            except Exception as e:
                logger.error(f"Failed to rebuild {service} vector {entity_id}: {e}")
                failed_ids.append(entity_id)

        return {
            "service": service,
            "total_missing": len(missing_ids),
            "fixed_count": fixed_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids
        }

    def _rebuild_knowledge_vector(self, knowledge_id: int):
        """重建单个知识向量"""
        try:
            import requests
            import os
            base_url = os.getenv("KNOWLEDGE_SERVICE_URL", "http://localhost:8081")
            response = requests.post(
                f"{base_url}/api/v1/vector/rebuild/{knowledge_id}",
                timeout=30
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to rebuild knowledge vector {knowledge_id}: {e}")
            raise

    def _rebuild_archive_vector(self, case_id: int):
        """重建单个案例向量"""
        try:
            import requests
            import os
            base_url = os.getenv("ARCHIVE_SERVICE_URL", "http://localhost:8082")
            response = requests.post(
                f"{base_url}/api/v1/vector/rebuild/{case_id}",
                timeout=30
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to rebuild archive vector {case_id}: {e}")
            raise

    def cleanup_orphaned_vectors(self, service: str) -> Dict:
        """清理孤立的向量"""
        if service == "knowledge":
            report = self.check_knowledge_consistency()
            orphaned_ids = report["orphaned_in_vector"]
        elif service == "archive":
            report = self.check_archive_consistency()
            orphaned_ids = report["orphaned_in_vector"]
        else:
            return {"error": "Invalid service"}

        if not orphaned_ids:
            return {"message": "No orphaned vectors to clean", "cleaned_count": 0}

        cleaned_count = 0
        failed_ids = []

        for entity_id in orphaned_ids:
            try:
                if service == "knowledge":
                    self._delete_knowledge_vector(entity_id)
                else:
                    self._delete_archive_vector(entity_id)
                cleaned_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {service} vector {entity_id}: {e}")
                failed_ids.append(entity_id)

        return {
            "service": service,
            "total_orphaned": len(orphaned_ids),
            "cleaned_count": cleaned_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids
        }

    def _delete_knowledge_vector(self, knowledge_id: int):
        """删除知识向量"""
        try:
            from app.services.knowledge_vector_store import delete_knowledge
            delete_knowledge(str(knowledge_id))
        except Exception as e:
            logger.error(f"Failed to delete knowledge vector {knowledge_id}: {e}")
            raise

    def _delete_archive_vector(self, case_id: int):
        """删除案例向量"""
        try:
            from app.services.archive_vector_store import delete_archive
            delete_archive(str(case_id))
        except Exception as e:
            logger.error(f"Failed to delete archive vector {case_id}: {e}")
            raise


consistency_checker = IndexConsistencyChecker()
