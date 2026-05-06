"""审计日志服务"""
import csv
import io
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from services.common.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """审计日志服务类"""

    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        service: str,
        action: str,
        resource_type: str,
        resource_id: int,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLog:
        """记录审计日志"""
        audit_log = AuditLog(
            service=service,
            user_id=user_id,
            user_role=user_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        logger.info(f"Audit log created: {action} on {resource_type}:{resource_id}")
        return audit_log

    def get_audit_trail(
        self,
        service: Optional[str] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """查询审计日志，支持分页和筛选"""
        query = self.db.query(AuditLog)

        if service:
            query = query.filter(AuditLog.service == service)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        total = query.count()
        query = query.order_by(desc(AuditLog.created_at))
        offset = (page - 1) * page_size
        logs = query.offset(offset).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "items": logs,
        }

    def export_audit_logs(
        self,
        service: Optional[str] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """导出审计日志为CSV格式"""
        query = self.db.query(AuditLog)

        if service:
            query = query.filter(AuditLog.service == service)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        logs = query.order_by(desc(AuditLog.created_at)).all()

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "ID", "服务", "用户ID", "用户角色", "操作",
            "资源类型", "资源ID", "变更内容", "IP地址",
            "用户代理", "请求ID", "创建时间"
        ])

        for log in logs:
            writer.writerow([
                log.id,
                log.service,
                log.user_id,
                log.user_role,
                log.action,
                log.resource_type,
                log.resource_id,
                str(log.changes) if log.changes else "",
                log.ip_address,
                log.user_agent,
                log.request_id,
                log.created_at.isoformat() if log.created_at else "",
            ])

        return output.getvalue()

    def get_resource_history(
        self,
        resource_type: str,
        resource_id: int,
        service: Optional[str] = None,
    ) -> List[AuditLog]:
        """获取特定资源的操作历史"""
        query = self.db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
        )
        if service:
            query = query.filter(AuditLog.service == service)

        return query.order_by(desc(AuditLog.created_at)).all()
