"""审计日志中间件 - 将操作记录写入数据库"""
import time
import uuid
import json
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.datastructures import Headers

from app.services.audit_service import get_current_audit_context, get_audit_logger, AuditAction, AuditSeverity

logger = logging.getLogger(__name__)

SENSITIVE_PATHS = {"/admin", "/settings", "/payment", "/users", "/roles", "/permissions"}
SENSITIVE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

HTTP_METHOD_TO_AUDIT_ACTION = {
    "GET": AuditAction.READ,
    "POST": AuditAction.CREATE,
    "PUT": AuditAction.UPDATE,
    "PATCH": AuditAction.UPDATE,
    "DELETE": AuditAction.DELETE,
}


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in ("/health", "/metrics", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        start_time = time.time()
        request_id = str(uuid.uuid4())
        ctx = get_current_audit_context()
        user_id = ctx.get("user_id") if ctx else None
        ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        logger.info(f"[AUDIT] Incoming request: request_id={request_id}, method={request.method}, path={request.url.path}, user_id={user_id}, ip={ip}")

        body = None
        if request.method in AUDIT_METHODS and not request.url.path.startswith("/docs"):
            try:
                body = await request.body()
                logger.info(f"[AUDIT] Request body captured, length={len(body) if body else 0}")
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
            except Exception as e:
                logger.warning(f"[AUDIT] Failed to read request body: {e}")
                body = None

        response = None
        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"[AUDIT] Request failed: error={e}, duration={duration_ms}ms")
            await self._persist_audit(
                request, request_id, user_id, ip, user_agent, response, duration_ms,
                action=str(request.method), success=False, error=str(e),
            )
            raise

        duration_ms = int((time.time() - start_time) * 1000)
        should_audit = self._should_audit(request)
        logger.info(f"[AUDIT] Should audit: {should_audit} (path={request.url.path}, method={request.method})")

        if should_audit:
            logger.info(f"[AUDIT] Persisting audit log for: {request.method} {request.url.path}")
            await self._persist_audit(
                request, request_id, user_id, ip, user_agent, response, duration_ms,
                action=str(request.method),
            )

        return response

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _should_audit(self, request: Request) -> bool:
        path = request.url.path
        logger.debug(f"[AUDIT] Should audit check: path={path}, method={request.method}")
        
        if not path.startswith("/api/"):
            logger.debug(f"[AUDIT] Not auditing (not /api/ path)")
            return False
        
        internal_path = path
        if internal_path.startswith("/api/v1/"):
            internal_path = internal_path[len("/api/v1/"):]
        elif internal_path.startswith("/api/"):
            internal_path = internal_path[len("/api/"):]
        internal_path = "/" + internal_path
        
        sensitive_match = any(internal_path.startswith(sp) for sp in SENSITIVE_PATHS)
        if not sensitive_match:
            logger.debug(f"[AUDIT] Not auditing (internal_path={internal_path} not in SENSITIVE_PATHS={SENSITIVE_PATHS})")
            return False
        
        method_match = request.method in SENSITIVE_METHODS
        if not method_match:
            logger.debug(f"[AUDIT] Not auditing (method not in SENSITIVE_METHODS={SENSITIVE_METHODS})")
            return False
        
        logger.info(f"[AUDIT] AUDIT TRIGGERED: path={path}, internal_path={internal_path}, method={request.method}")
        return True

    async def _persist_audit(
        self, request: Request, request_id: str, user_id: int | None,
        ip: str, user_agent: str, response: Response | None,
        duration_ms: int, action: str, success: bool = True, error: str | None = None,
    ):
        try:
            audit_logger = get_audit_logger()
            path = request.url.path

            from app.services.audit_service import get_current_audit_context
            ctx = get_current_audit_context()
            user_role = ctx.get("user_role") if ctx else None

            resource_type = self._extract_resource_type(path)
            resource_id = self._extract_resource_id(path)
            status_code = response.status_code if response else None
            
            audit_action = HTTP_METHOD_TO_AUDIT_ACTION.get(action, AuditAction.READ)
            
            logger.info(f"[AUDIT] Creating audit entry: request_id={request_id}, action={action}, resource={resource_type}, resource_id={resource_id}, status={status_code}")

            entry = audit_logger.create_entry(
                action=audit_action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                username=None,
                ip_address=ip,
                user_agent=user_agent,
                request_id=request_id,
                duration_ms=duration_ms,
                success=success,
                error_message=error,
                severity=AuditSeverity.WARNING if not success else AuditSeverity.INFO,
                metadata={
                    "method": request.method,
                    "path": path,
                    "query": str(request.query_params) if request.query_params else None,
                    "status_code": status_code,
                    "user_role": user_role,
                },
            )
            logger.info(f"[AUDIT] About to log async: request_id={request_id}")
            await audit_logger.log_async(
                audit_action,
                resource_type,
                resource_id=resource_id,
                user_id=user_id,
                username=None,
                ip_address=ip,
                user_agent=user_agent,
                request_id=request_id,
                duration_ms=duration_ms,
                success=success,
                error_message=error,
                severity=AuditSeverity.WARNING if not success else AuditSeverity.INFO,
                metadata={
                    "method": request.method,
                    "path": path,
                    "query": str(request.query_params) if request.query_params else None,
                    "status_code": status_code,
                    "user_role": user_role,
                },
            )
            logger.info(f"[AUDIT] Audit log persisted successfully: request_id={request_id}")
        except Exception as e:
            logger.error(f"[AUDIT] Failed to persist audit log: request_id={request_id}, error={e}", exc_info=True)

    def _extract_resource_type(self, path: str) -> str:
        parts = path.strip("/").split("/")
        if len(parts) >= 4:
            return parts[3]
        if len(parts) >= 3:
            return parts[2]
        return "unknown"

    def _extract_resource_id(self, path: str) -> str | None:
        parts = path.strip("/").split("/")
        if len(parts) >= 5 and parts[4].isdigit():
            return parts[4]
        if len(parts) >= 5:
            return parts[4]
        return None
