"""审计日志服务测试"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


class TestAuditLogger:
    """审计日志记录器测试"""

    def test_log_action(self):
        """测试记录审计日志"""
        from app.services.data_security import AuditLogger

        logger = AuditLogger()
        result = logger.log(
            action="user.login",
            user_id=123,
            resource_type="user",
            resource_id="123",
            details={"method": "password"},
            ip_address="192.168.1.1",
        )

        assert result["logged"] is True
        assert "audit_" in result["audit_id"]

    def test_get_logs_no_filter(self):
        """测试获取所有日志"""
        from app.services.data_security import AuditLogger

        logger = AuditLogger()
        logger.log("action1", 1, "type1", "id1")
        logger.log("action2", 2, "type2", "id2")

        logs = logger.get_logs()
        assert len(logs) == 2

    def test_get_logs_filter_by_user(self):
        """测试按用户ID筛选日志"""
        from app.services.data_security import AuditLogger

        logger = AuditLogger()
        logger.log("action1", 1, "type1", "id1")
        logger.log("action2", 2, "type2", "id2")
        logger.log("action3", 1, "type3", "id3")

        logs = logger.get_logs(user_id=1)
        assert len(logs) == 2
        for log in logs:
            assert log["user_id"] == 1

    def test_get_logs_filter_by_resource_type(self):
        """测试按资源类型筛选日志"""
        from app.services.data_security import AuditLogger

        logger = AuditLogger()
        logger.log("action1", 1, "user", "id1")
        logger.log("action2", 2, "order", "id2")
        logger.log("action3", 1, "user", "id3")

        logs = logger.get_logs(resource_type="user")
        assert len(logs) == 2
        for log in logs:
            assert log["resource_type"] == "user"

    def test_get_logs_with_limit(self):
        """测试获取日志数量限制"""
        from app.services.data_security import AuditLogger

        logger = AuditLogger()
        for i in range(10):
            logger.log(f"action{i}", i, "type", f"id{i}")

        logs = logger.get_logs(limit=5)
        assert len(logs) == 5

    def test_get_stats(self):
        """测试获取统计信息"""
        from app.services.data_security import AuditLogger

        logger = AuditLogger()
        logger.log("login", 1, "user", "id1")
        logger.log("login", 2, "user", "id2")
        logger.log("logout", 1, "user", "id1")

        stats = logger.get_stats()
        assert stats["total_logs"] == 3
        assert stats["action_counts"]["login"] == 2
        assert stats["action_counts"]["logout"] == 1
        assert stats["retention_days"] == 90

    def test_log_without_user_id(self):
        """测试记录不带用户ID的日志"""
        from app.services.data_security import AuditLogger

        logger = AuditLogger()
        result = logger.log(
            action="system.startup",
            user_id=None,
            resource_type="system",
            resource_id="startup",
        )

        assert result["logged"] is True

    def test_log_with_empty_details(self):
        """测试记录带空详情的日志"""
        from app.services.data_security import AuditLogger

        logger = AuditLogger()
        result = logger.log(
            action="action",
            user_id=1,
            resource_type="type",
            resource_id="id",
            details=None,
        )

        assert result["logged"] is True


class TestDataSecurityServiceAudit:
    """数据安全服务审计功能测试"""

    def test_audit_action(self):
        """测试审计操作"""
        import asyncio
        from app.services.data_security import DataSecurityService

        service = DataSecurityService()
        result = asyncio.run(service.audit_action(
            action="user.update",
            user_id=123,
            resource_type="user",
            resource_id="123",
            details={"field": "email"},
            ip_address="192.168.1.1",
        ))

        assert result["logged"] is True

    def test_get_audit_logs(self):
        """测试获取审计日志"""
        import asyncio
        from app.services.data_security import DataSecurityService

        service = DataSecurityService()
        asyncio.run(service.audit_action("action1", 1, "type1", "id1"))
        asyncio.run(service.audit_action("action2", 2, "type2", "id2"))

        logs = asyncio.run(service.get_audit_logs(user_id=1))
        assert len(logs) == 1

    def test_get_security_report(self):
        """测试获取安全报告"""
        import asyncio
        from app.services.data_security import DataSecurityService

        service = DataSecurityService()
        asyncio.run(service.audit_action("login", 1, "user", "1"))
        asyncio.run(service.audit_action("logout", 1, "user", "1"))

        report = asyncio.run(service.get_security_report())
        assert "audit_stats" in report
        assert "classification_count" in report
        assert "mask_rules_count" in report


class TestAuditActionFunction:
    """审计操作函数测试"""

    def test_audit_action_function(self):
        """测试审计操作函数"""
        import asyncio
        from app.services.data_security import audit_action

        result = asyncio.run(audit_action(
            action="test.action",
            user_id=456,
            resource_type="test",
            resource_id="test123",
        ))

        assert result["logged"] is True
