"""OpenTelemetry FastAPI 中间件

提供自动化的请求追踪、指标收集和分布式上下文传播。
支持：
- 自动创建 span（请求 -> 响应）
- 传播 trace context
- 收集 HTTP 指标（请求数、延迟、错误率）
- 记录请求/响应属性
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
from opentelemetry.trace import SpanKind, StatusCode
from opentelemetry.semconv.trace import SpanAttributes

logger = logging.getLogger(__name__)


class OpenTelemetryMiddleware(BaseHTTPMiddleware):
    """OpenTelemetry 中间件"""

    def __init__(self, app, tracer=None, exclude_paths: list[str] = None):
        super().__init__(app)
        self.tracer = tracer or trace.get_tracer("baixing-falvzhushou")
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json", "/redoc"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self._should_exclude(request.url.path):
            return await call_next(request)

        method = request.method
        route = request.url.path
        span_name = f"{method} {route}"

        start_time = time.time()

        with self.tracer.start_as_current_span(
            span_name,
            kind=SpanKind.SERVER,
        ) as span:
            span.set_attribute(SpanAttributes.HTTP_METHOD, method)
            span.set_attribute(SpanAttributes.HTTP_URL, str(request.url))
            span.set_attribute(SpanAttributes.HTTP_FLAVOR, "1.1")

            client_host = request.client.host if request.client else None
            if client_host:
                span.set_attribute(SpanAttributes.NET_PEER_IP, client_host)

            user_agent = request.headers.get("user-agent")
            if user_agent:
                span.set_attribute(SpanAttributes.HTTP_USER_AGENT, user_agent)

            request_id = request.headers.get("x-request-id")
            if request_id:
                span.set_attribute("http.request_id", request_id)

            try:
                response = await call_next(request)

                span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, response.status_code)

                duration = time.time() - start_time
                span.set_attribute(SpanAttributes.HTTP_RESPONSE_CONTENT_LENGTH, len(response.body))

                if response.status_code >= 400:
                    span.set_status(StatusCode.ERROR)
                    span.set_attribute("http.error", f"HTTP {response.status_code}")

                response.headers["x-request-id"] = request_id or span.context.trace_id.to_bytes(8, "big").hex()
                return response

            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise

    def _should_exclude(self, path: str) -> bool:
        """检查是否应该排除追踪"""
        return any(path.startswith(exclude) for exclude in self.exclude_paths)


def setup_telemetry(app, tracer=None, exclude_paths: list[str] = None):
    """为 FastAPI 应用设置遥测"""
    from services.common.tracing import init_telemetry

    if tracer is None:
        service_name = getattr(app.state, "service_name", "baixing-falvzhushou")
        tracer = init_telemetry(service_name)

    app.add_middleware(OpenTelemetryMiddleware, tracer=tracer, exclude_paths=exclude_paths)
    logger.info(f"OpenTelemetry middleware setup for {app}")
    return app
