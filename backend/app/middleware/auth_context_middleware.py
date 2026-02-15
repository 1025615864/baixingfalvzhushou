from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.security import decode_access_token

logger = logging.getLogger(__name__)


class AuthContextMiddleware(BaseHTTPMiddleware):
    """认证上下文中间件 - 支持Authorization Header和Cookie双重认证"""

    async def dispatch(self, request: Request, call_next: Callable[[
                       Request], Awaitable[Response]]) -> Response:
        user_id: int | None = None
        try:
            # 优先从Authorization Header获取token
            auth = str(request.headers.get("authorization") or "").strip()
            if auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1].strip()
                payload = decode_access_token(token)
                if payload is not None:
                    sub = payload.get("sub")
                    if sub is not None:
                        try:
                            user_id = int(str(sub))
                        except Exception:
                            logger.exception("Failed to extract user_id from token in auth context")
                            user_id = None

            # 如果Header中没有，尝试从Cookie获取
            if user_id is None:
                access_token = request.cookies.get("access_token")
                if access_token:
                    payload = decode_access_token(access_token)
                    if payload is not None:
                        sub = payload.get("sub")
                        if sub is not None:
                            try:
                                user_id = int(str(sub))
                            except Exception:
                                logger.exception("Failed to extract user_id from Authorization header")
                                user_id = None
        except Exception:
            logger.exception("Failed to extract user_id in auth context middleware")
            user_id = None

        request.state.user_id = user_id
        return await call_next(request)
