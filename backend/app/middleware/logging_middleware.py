"""请求日志中间件（敏感信息脱敏）"""
import json
import time
import logging
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.rate_limiter import get_client_ip
from ..utils.data_sanitizer import DataSanitizer, MaskLevel
from ..config import get_settings

logger = logging.getLogger("api.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志记录中间件（支持敏感信息脱敏）"""

    def __init__(self, app, mask_level: MaskLevel | None = None):
        """初始化中间件

        Args:
            app: FastAPI应用
            mask_level: 可选的脱敏级别覆盖
        """
        super().__init__(app)
        self._sanitizer = DataSanitizer()
        self._custom_mask_level = mask_level
        self._init_sanitizer()

    def _init_sanitizer(self) -> None:
        """初始化脱敏器配置"""
        settings = get_settings()

        # 确定脱敏级别
        if self._custom_mask_level:
            level = self._custom_mask_level
        elif settings.debug and settings.log_mask_disable_in_debug:
            level = MaskLevel.NONE
        else:
            try:
                level = MaskLevel(settings.log_mask_level.lower())
            except ValueError:
                level = MaskLevel.STANDARD

        self._sanitizer.set_mask_level(level)

        # 添加自定义敏感字段
        if settings.log_mask_fields:
            for field in settings.log_mask_fields:
                self._sanitizer.add_sensitive_field(field)

    def _mask_ip(self, ip: str | None) -> str | None:
        """对IP地址进行部分脱敏

        保留前两段，后两段用*代替
        例如：192.168.1.100 -> 192.168.***

        Args:
            ip: 原始IP地址

        Returns:
            脱敏后的IP地址
        """
        if not ip:
            return None

        try:
            # IPv4
            if "." in ip:
                parts = ip.split(".")
                if len(parts) == 4:
                    return f"{'.'.join(parts[:2])}.***"
            # IPv6
            if ":" in ip:
                parts = ip.split(":")
                if len(parts) >= 4:
                    return f"{':'.join(parts[:2])}::***"
        except Exception:
            logger.exception("Failed to sanitize IP address")

        return "***"

    def _mask_user_id(self, user_id: str | int | None) -> str | None:
        """对用户ID进行脱敏

        Args:
            user_id: 用户ID

        Returns:
            脱敏后的用户ID
        """
        if not user_id:
            return None

        user_str = str(user_id)
        if len(user_str) >= 3:
            return f"{'*' * (len(user_str) - 3)}{user_str[-3:]}"
        return "***"

    async def dispatch(self, request: Request, call_next: Callable[[
                       Request], Awaitable[Response]]) -> Response:
        """处理请求并记录日志"""
        start_time = time.time()

        # 获取请求信息
        method = request.method
        path = request.url.path
        query_string = str(request.url.query)
        client_ip = get_client_ip(request)
        
        # 安全获取 request_id，避免深层嵌套
        request_id = ""
        request_state = getattr(request, "state", None)
        if request_state is not None:
            request_id = str(getattr(request_state, "request_id", "") or "").strip()

        # 获取用户ID（脱敏处理）
        user_id: int | None = None
        if request_state is not None:
            user_id = getattr(request_state, "user_id", None)
        safe_user_id = self._mask_user_id(user_id)

        # 脱敏路径和查询参数
        safe_path = self._sanitizer.sanitize_url_path(path)
        safe_query = self._sanitizer.sanitize_query_string(query_string) if query_string else None

        # 跳过健康检查和静态文件的日志
        skip_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/metrics",  # 避免记录metrics日志
        ]
        should_log = not any(path.startswith(p) for p in skip_paths)

        try:
            response = await call_next(request)

            # 计算响应时间
            duration_ms = (time.time() - start_time) * 1000

            if should_log:
                # 根据状态码选择日志级别
                status_code = response.status_code
                payload = {
                    "event": "http_request",
                    "request_id": request_id or None,
                    "user_id": safe_user_id,
                    "method": method,
                    "path": safe_path,
                    "query": safe_query,
                    "status": int(status_code),
                    "duration_ms": round(float(duration_ms), 2),
                    "client_ip": self._mask_ip(client_ip),
                }

                # 移除None值
                payload = {k: v for k, v in payload.items() if v is not None}

                log_msg = json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(
                        ",",
                        ":"))

                if status_code >= 500:
                    logger.error(log_msg)
                elif status_code >= 400:
                    logger.warning(log_msg)
                else:
                    logger.info(log_msg)

            # 添加响应头
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            # 脱敏错误信息（避免记录敏感数据）
            safe_error_msg = self._sanitizer.sanitize_log_message(str(e))

            payload = {
                "event": "http_request_error",
                "request_id": request_id or None,
                "user_id": safe_user_id,
                "method": method,
                "path": safe_path,
                "query": safe_query,
                "status": None,
                "duration_ms": round(float(duration_ms), 2),
                "client_ip": self._mask_ip(client_ip),
                "error_type": type(e).__name__,
                "error": safe_error_msg,
            }

            # 移除None值
            payload = {k: v for k, v in payload.items() if v is not None}

            logger.error(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(
                        ",",
                        ":")),
                exc_info=True)
            raise


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """错误日志记录中间件（敏感信息脱敏）"""

    def __init__(self, app, mask_level: MaskLevel | None = None):
        """初始化中间件

        Args:
            app: FastAPI应用
            mask_level: 可选的脱敏级别覆盖
        """
        super().__init__(app)
        self._sanitizer = DataSanitizer()
        self._custom_mask_level = mask_level
        self._init_sanitizer()

    def _init_sanitizer(self) -> None:
        """初始化脱敏器配置"""
        settings = get_settings()

        if self._custom_mask_level:
            level = self._custom_mask_level
        elif settings.debug and settings.log_mask_disable_in_debug:
            level = MaskLevel.NONE
        else:
            try:
                level = MaskLevel(settings.log_mask_level.lower())
            except ValueError:
                level = MaskLevel.STANDARD

        self._sanitizer.set_mask_level(level)

    def _mask_user_id(self, user_id: str | int | None) -> str | None:
        """对用户ID进行脱敏"""
        if not user_id:
            return None

        user_str = str(user_id)
        if len(user_str) >= 3:
            return f"{'*' * (len(user_str) - 3)}{user_str[-3:]}"
        return "***"

    async def dispatch(self, request: Request, call_next: Callable[[
                       Request], Awaitable[Response]]) -> Response:
        """捕获并记录未处理的异常（应用脱敏）"""
        try:
            return await call_next(request)
        except Exception as e:
            request_id = str(
                getattr(
                    getattr(
                        request,
                        "state",
                        None),
                    "request_id",
                    "") or "").strip()
            user_id = getattr(getattr(request, "state", None), "user_id", None)

            # 对user_id进行脱敏
            safe_user_id = self._mask_user_id(user_id)

            # 脱敏错误信息
            safe_error_msg = self._sanitizer.sanitize_log_message(str(e))

            # 脱敏请求路径
            safe_path = self._sanitizer.sanitize_url_path(request.url.path)

            payload = {
                "event": "unhandled_exception",
                "request_id": request_id or None,
                "user_id": safe_user_id,
                "method": request.method,
                "path": safe_path,
                "error_type": type(e).__name__,
                "error": safe_error_msg,
            }

            # 移除None值
            payload = {k: v for k, v in payload.items() if v is not None}

            logger.exception(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(
                        ",",
                        ":")))
            raise


class BodyLoggingMiddleware(BaseHTTPMiddleware):
    """请求/响应体日志中间件（用于调试，慎用）"""

    def __init__(self, app, max_body_size: int = 10000, log_responses: bool = False):
        """初始化中间件

        Args:
            app: FastAPI应用
            max_body_size: 最大记录体大小
            log_responses: 是否记录响应体
        """
        super().__init__(app)
        self.max_body_size = max_body_size
        self.log_responses = log_responses
        self._sanitizer = DataSanitizer()
        self._init_sanitizer()

    def _init_sanitizer(self) -> None:
        """初始化脱敏器"""
        settings = get_settings()
        try:
            level = MaskLevel(settings.log_mask_level.lower())
        except ValueError:
            level = MaskLevel.STANDARD
        self._sanitizer.set_mask_level(level)

    async def dispatch(self, request: Request, call_next: Callable[[
                       Request], Awaitable[Response]]) -> Response:
        """处理请求并记录请求/响应体"""
        # 只记录特定路径的请求体
        sensitive_paths = ["/api/payment", "/api/auth", "/api/user/login", "/api/user/register"]
        should_log_body = any(str(request.url.path).startswith(p) for p in sensitive_paths)

        if should_log_body:
            body = await request.body()
            if body:
                try:
                    body_str = body.decode("utf-8", errors="replace")[:self.max_body_size]
                    # 尝试解析为JSON并脱敏
                    try:
                        body_json = json.loads(body_str)
                        sanitized_body = self._sanitizer.sanitize_dict(body_json)
                        logger.debug(f"Request body: {json.dumps(sanitized_body)}")
                    except json.JSONDecodeError:
                        # 非JSON内容，直接脱敏字符串
                        sanitized_body = self._sanitizer.sanitize_log_message(body_str)
                        logger.debug(f"Request body: {sanitized_body}")
                except Exception as e:
                    logger.warning(f"Failed to log request body: {e}")

            # 重新设置请求体以便后续中间件可以读取
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive

        response = await call_next(request)

        if self.log_responses and should_log_body:
            # 注意：记录响应体可能影响性能
            pass

        return response
