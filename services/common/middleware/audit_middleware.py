"""审计上下文中间件"""
import logging
from contextvars import ContextVar
from typing import Optional
from fastapi import Request

logger = logging.getLogger(__name__)

# Context variables for audit logging
audit_user_id: ContextVar[Optional[int]] = ContextVar("audit_user_id", default=None)
audit_user_role: ContextVar[Optional[str]] = ContextVar("audit_user_role", default=None)
audit_request_id: ContextVar[Optional[str]] = ContextVar("audit_request_id", default=None)
audit_ip_address: ContextVar[Optional[str]] = ContextVar("audit_ip_address", default=None)


class AuditContext:
    """审计上下文管理器"""
    
    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None,
                 request_id: Optional[str] = None, ip_address: Optional[str] = None):
        self.user_id = user_id
        self.user_role = user_role
        self.request_id = request_id
        self.ip_address = ip_address

    def __enter__(self):
        self._reset_user_id = audit_user_id.set(self.user_id)
        self._reset_user_role = audit_user_role.set(self.user_role)
        self._reset_request_id = audit_request_id.set(self.request_id)
        self._reset_ip_address = audit_ip_address.set(self.ip_address)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        audit_user_id.reset(self._reset_user_id)
        audit_user_role.reset(self._reset_user_role)
        audit_request_id.reset(self._reset_request_id)
        audit_ip_address.reset(self._reset_ip_address)


async def get_audit_context(request: Request, user_id: Optional[int] = None, user_role: Optional[str] = None) -> AuditContext:
    """获取审计上下文（用于依赖注入）"""
    client_host = request.client.host if request.client else None
    
    return AuditContext(
        user_id=user_id,
        user_role=user_role,
        request_id=request.headers.get("x-request-id"),
        ip_address=client_host,
    )


def get_current_audit_context() -> dict:
    """获取当前审计上下文"""
    return {
        "user_id": audit_user_id.get(),
        "user_role": audit_user_role.get(),
        "request_id": audit_request_id.get(),
        "ip_address": audit_ip_address.get(),
    }
