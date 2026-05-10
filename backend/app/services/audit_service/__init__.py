"""Audit service."""
from __future__ import annotations
import enum
import uuid
import contextvars
from datetime import datetime, timezone
from typing import Optional, Any
from dataclasses import dataclass, field


class AuditAction(enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"
    EXPORT = "export"
    IMPORT = "import"
    ADMIN_ACTION = "admin_action"
    API_CALL = "api_call"
    SYSTEM = "system"


class AuditSeverity(enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditLogEntry:
    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    details: Optional[dict] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    severity: AuditSeverity = AuditSeverity.INFO
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Optional[dict] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id, "action": self.action.value,
            "resource_type": self.resource_type, "resource_id": self.resource_id,
            "timestamp": self.timestamp, "success": self.success,
        }


_audit_context: contextvars.ContextVar[Optional[dict]] = contextvars.ContextVar("audit_context", default=None)


class AuditContext:
    def __init__(self, user_id=None, username=None, ip_address=None, request_id=None):
        self._data = {"user_id": user_id, "username": username, "ip_address": ip_address, "request_id": request_id}

    async def __aenter__(self):
        self._token = _audit_context.set(self._data)
        return self._data

    async def __aexit__(self, *args):
        _audit_context.reset(self._token)


class AuditLogger:
    def __init__(self, async_mode: bool = True, batch_size: int = 100, flush_interval: float = 5.0):
        self.async_mode = async_mode
        self.batch_size = batch_size
        self.flush_interval = flush_interval

    def create_entry(self, action: AuditAction, resource_type: str, resource_id: Optional[str] = None, **kwargs) -> AuditLogEntry:
        return AuditLogEntry(action=action, resource_type=resource_type, resource_id=resource_id, **kwargs)


def get_current_audit_context() -> Optional[dict]:
    return _audit_context.get()


_logger_instance: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AuditLogger(async_mode=False)
    return _logger_instance


def log_audit(action: AuditAction, resource_type: str, **kwargs) -> AuditLogEntry:
    logger = get_audit_logger()
    return logger.create_entry(action, resource_type, **kwargs)
