"""审计服务测试"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.audit_service import (
    AuditAction,
    AuditLogEntry,
    AuditLogger,
    AuditSeverity,
    get_current_audit_context,
    get_audit_logger,
    log_audit,
)


class TestAuditLogEntry:
    """审计日志条目测试"""

    def test_create_entry_minimal(self):
        """测试创建最小条目"""
        entry = AuditLogEntry(
            action=AuditAction.CREATE,
            resource_type="user",
        )
        assert entry.action == AuditAction.CREATE
        assert entry.resource_type == "user"
        assert entry.resource_id is None
        assert entry.success is True

    def test_create_entry_full(self):
        """测试创建完整条目"""
        entry = AuditLogEntry(
            action=AuditAction.UPDATE,
            resource_type="post",
            resource_id="456",
            user_id=2,
            username="testuser",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_id="req-123",
            details={"field": "value"},
            old_value={"title": "old"},
            new_value={"title": "new"},
            severity=AuditSeverity.WARNING,
            success=False,
            error_message="Access denied",
            duration_ms=150,
            metadata={"extra": "info"},
        )
        assert entry.action == AuditAction.UPDATE
        assert entry.resource_id == "456"
        assert entry.old_value == {"title": "old"}
        assert entry.new_value == {"title": "new"}
        assert entry.severity == AuditSeverity.WARNING
        assert entry.success is False

    def test_to_dict(self):
        """测试转换为字典"""
        entry = AuditLogEntry(
            action=AuditAction.DELETE,
            resource_type="file",
            resource_id="789",
        )
        data = entry.to_dict()
        assert "id" in data
        assert data["action"] == "delete"
        assert data["resource_type"] == "file"
        assert data["resource_id"] == "789"
        assert "timestamp" in data


class TestAuditLogger:
    """审计日志记录器测试"""

    def test_create_entry(self):
        """测试创建日志条目"""
        logger = AuditLogger(async_mode=False)
        entry = logger.create_entry(
            action=AuditAction.UPDATE,
            resource_type="post",
            resource_id="456",
            user_id=2,
            old_value={"title": "old"},
            new_value={"title": "new"},
        )
        assert entry.action == AuditAction.UPDATE
        assert entry.resource_type == "post"
        assert entry.resource_id == "456"
        assert entry.old_value == {"title": "old"}
        assert entry.new_value == {"title": "new"}
        assert entry.success is True

    def test_log_with_failure(self):
        """测试记录失败操作"""
        logger = AuditLogger(async_mode=False)
        entry = logger.create_entry(
            action=AuditAction.DELETE,
            resource_type="file",
            resource_id="789",
            success=False,
            error_message="Permission denied",
            severity=AuditSeverity.ERROR,
        )
        assert entry.success is False
        assert entry.error_message == "Permission denied"
        assert entry.severity == AuditSeverity.ERROR

    def test_logger_initialization(self):
        """测试记录器初始化"""
        logger = AuditLogger(async_mode=False)
        assert logger.async_mode is False
        assert logger.batch_size == 100
        assert logger.flush_interval == 5.0


class TestAuditContext:
    """审计上下文测试"""

    @pytest.mark.asyncio
    async def test_audit_context(self):
        """测试审计上下文"""
        from app.services.audit_service import AuditContext

        async with AuditContext(
            user_id=1,
            username="testuser",
            ip_address="192.168.1.1",
            request_id="req-123",
        ) as ctx:
            current_ctx = get_current_audit_context()
            assert current_ctx["user_id"] == 1
            assert current_ctx["username"] == "testuser"
            assert current_ctx["ip_address"] == "192.168.1.1"
            assert current_ctx["request_id"] == "req-123"

        assert get_current_audit_context() is None


class TestAuditSeverity:
    """审计级别测试"""

    def test_severity_order(self):
        """测试级别顺序"""
        severities = list(AuditSeverity)
        assert AuditSeverity.DEBUG in severities
        assert AuditSeverity.INFO in severities
        assert AuditSeverity.WARNING in severities
        assert AuditSeverity.ERROR in severities
        assert AuditSeverity.CRITICAL in severities

    def test_severity_values(self):
        """测试级别值"""
        assert AuditSeverity.DEBUG.value == "debug"
        assert AuditSeverity.INFO.value == "info"
        assert AuditSeverity.WARNING.value == "warning"
        assert AuditSeverity.ERROR.value == "error"
        assert AuditSeverity.CRITICAL.value == "critical"


class TestAuditAction:
    """审计操作类型测试"""

    def test_all_actions_defined(self):
        """测试所有操作类型都已定义"""
        expected_actions = [
            "create", "read", "update", "delete",
            "login", "logout", "login_failed", "password_change",
            "permission_change", "export", "import",
            "admin_action", "api_call", "system",
        ]
        actual_actions = [action.value for action in AuditAction]
        for expected in expected_actions:
            assert expected in actual_actions


class TestGetAuditLogger:
    """审计日志器获取测试"""

    def test_get_audit_logger(self):
        """测试获取审计日志器"""
        logger = get_audit_logger()
        assert logger is not None
        assert isinstance(logger, AuditLogger)


class TestAuditActionTypes:
    """审计操作类型详细测试"""

    def test_create_action(self):
        """测试创建操作"""
        action = AuditAction.CREATE
        assert action.value == "create"

    def test_read_action(self):
        """测试读取操作"""
        action = AuditAction.READ
        assert action.value == "read"

    def test_login_action(self):
        """测试登录操作"""
        action = AuditAction.LOGIN
        assert action.value == "login"

    def test_logout_action(self):
        """测试登出操作"""
        action = AuditAction.LOGOUT
        assert action.value == "logout"

    def test_admin_action(self):
        """测试管理操作"""
        action = AuditAction.ADMIN_ACTION
        assert action.value == "admin_action"

    def test_system_action(self):
        """测试系统操作"""
        action = AuditAction.SYSTEM
        assert action.value == "system"
