from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logging.structured_logger import (
    set_request_id,
    set_trace_id,
    set_user_id,
)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[
                       Request], Awaitable[Response]]) -> Response:
        incoming = str(request.headers.get("X-Request-Id") or "").strip()
        request_id = incoming if incoming else uuid.uuid4().hex
        request.state.request_id = request_id

        # 设置到上下文变量（用于结构化日志）
        set_request_id(request_id)

        response = await call_next(request)
        response.headers.setdefault("X-Request-Id", request_id)
        return response


class TracingMiddleware(BaseHTTPMiddleware):
    """链路追踪中间件

    功能：
    1. 为每个请求生成唯一的 trace_id
    2. 将 request_id 和 user_id 设置到上下文变量
    3. 支持请求头传递 trace_id（用于分布式追踪）
    """

    async def dispatch(self, request: Request, call_next: Callable[[
                       Request], Awaitable[Response]]) -> Response:
        # 获取或生成 trace_id
        incoming_trace = str(request.headers.get("X-Trace-Id") or "").strip()
        trace_id = incoming_trace if incoming_trace else uuid.uuid4().hex

        # 获取 user_id（如果已认证）
        user_id = getattr(request.state, "user_id", None)

        # 设置上下文变量
        set_trace_id(trace_id)
        if user_id:
            set_user_id(user_id)

        # 添加到请求状态
        request.state.trace_id = trace_id

        response = await call_next(request)

        # 添加追踪头到响应
        response.headers.setdefault("X-Trace-Id", trace_id)

        return response
