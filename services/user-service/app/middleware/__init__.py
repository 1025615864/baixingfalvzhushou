"""中间件模块"""
from .auth import (
    get_current_user,
    get_current_user_optional,
    require_admin,
)

try:
    from services.common.middleware import check_request_rate_limit, rate_limiter

    __all__ = [
        "get_current_user",
        "get_current_user_optional",
        "require_admin",
        "check_request_rate_limit",
        "rate_limiter",
    ]
except ImportError:
    async def check_request_rate_limit(request):
        pass

    class rate_limiter:
        async def check_rate_limit(self, *args, **kwargs):
            return True, None, 100

    __all__ = [
        "get_current_user",
        "get_current_user_optional",
        "require_admin",
        "check_request_rate_limit",
        "rate_limiter",
    ]
