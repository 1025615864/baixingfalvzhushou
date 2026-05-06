"""Audit context middleware for knowledge service"""
import logging
from typing import Optional
from fastapi import Request

logger = logging.getLogger(__name__)


class AuditContext:
    """Audit context holder"""
    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None,
                 request_id: Optional[str] = None, ip_address: Optional[str] = None):
        self.user_id = user_id
        self.user_role = user_role
        self.request_id = request_id
        self.ip_address = ip_address


async def get_audit_context(request: Request, user_id: Optional[int] = None, user_role: Optional[str] = None) -> AuditContext:
    """Get audit context for request"""
    client_host = request.client.host if request.client else None
    
    return AuditContext(
        user_id=user_id,
        user_role=user_role,
        request_id=request.headers.get("x-request-id"),
        ip_address=client_host,
    )
