"""Common middleware package"""
from .rate_limit import (
    RateLimiter,
    rate_limiter,
    check_request_rate_limit,
    check_register_rate_limit,
    check_vector_search_rate_limit,
    check_search_rate_limit,
    check_vector_rebuild_rate_limit,
    check_seed_rate_limit,
    check_batch_rate_limit,
)
from .auth import (
    AuthConfig,
    TokenPayload,
    verify_token,
    get_current_user,
    get_optional_user,
    require_roles,
    create_access_token,
    ROLES,
    check_permission,
)
from .audit_middleware import AuditContext, get_audit_context
from .telemetry import OpenTelemetryMiddleware, setup_telemetry

__all__ = [
    "RateLimiter",
    "rate_limiter",
    "check_request_rate_limit",
    "check_register_rate_limit",
    "check_vector_search_rate_limit",
    "check_search_rate_limit",
    "check_vector_rebuild_rate_limit",
    "check_seed_rate_limit",
    "check_batch_rate_limit",
    "AuthConfig",
    "TokenPayload",
    "verify_token",
    "get_current_user",
    "get_optional_user",
    "require_roles",
    "create_access_token",
    "ROLES",
    "check_permission",
    "AuditContext",
    "get_audit_context",
    "OpenTelemetryMiddleware",
    "setup_telemetry",
]
