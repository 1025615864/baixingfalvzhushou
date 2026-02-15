"""结构化日志与链路追踪工具

提供 JSON 格式的结构化日志输出和请求 ID 贯穿链路的能力。
"""
import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# 请求 ID 上下文变量
_request_id_ctx: ContextVar[Optional[str]
                            ] = ContextVar("request_id", default=None)
_user_id_ctx: ContextVar[Optional[int]] = ContextVar("user_id", default=None)
_trace_id_ctx: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def get_request_id() -> Optional[str]:
    """获取当前请求 ID"""
    return _request_id_ctx.get()


def set_request_id(request_id: str) -> None:
    """设置当前请求 ID"""
    _request_id_ctx.set(request_id)


def get_user_id() -> Optional[int]:
    """获取当前用户 ID"""
    return _user_id_ctx.get()


def set_user_id(user_id: int) -> None:
    """设置当前用户 ID"""
    _user_id_ctx.set(user_id)


def get_trace_id() -> Optional[str]:
    """获取当前追踪 ID"""
    return _trace_id_ctx.get()


def set_trace_id(trace_id: str) -> None:
    """设置当前追踪 ID"""
    _trace_id_ctx.set(trace_id)


class StructuredLogFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """将日志记录格式化为 JSON 字符串"""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加请求 ID（从上下文获取）
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id

        # 添加用户 ID（从上下文获取）
        user_id = get_user_id()
        if user_id:
            log_data["user_id"] = user_id

        # 添加追踪 ID（从上下文获取）
        trace_id = get_trace_id()
        if trace_id:
            log_data["trace_id"] = trace_id

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(
                    record.exc_info[1]) if record.exc_info[1] else None,
                "stacktrace": self.formatException(
                    record.exc_info) if record.exc_info[1] else None,
            }

        # 添加额外字段（通过 record.__dict__ 中的 extra 属性）
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "info",
                "warn",
                "warning",
                "error",
                "critical",
                "fatal",
                "exception",
                "message",
            ):
                log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False, separators=(",", ":"))


class JSONLogFormatter(logging.Formatter):
    """JSON 日志格式化器（生产环境使用）"""

    def format(self, record: logging.LogRecord) -> str:
        """将日志记录格式化为标准 JSON 格式"""
        log_data: dict[str, Any] = {
            "level": record.levelname,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
            "message": record.getMessage(),
        }

        # 添加标准字段
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id

        user_id = get_user_id()
        if user_id:
            log_data["user_id"] = user_id

        trace_id = get_trace_id()
        if trace_id:
            log_data["trace_id"] = trace_id

        # 添加日志名称
        log_data["logger"] = record.name

        # 添加位置信息
        log_data["location"] = {
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["error"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(
                    record.exc_info[1]) if record.exc_info[1] else None,
                "stack_trace": self.formatException(
                    record.exc_info),
            }

        # 添加额外字段
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "info",
                "warn",
                "warning",
                "error",
                "critical",
                "fatal",
                "exception",
                "message",
            ):
                extra_fields[key] = value

        if extra_fields:
            log_data["extra"] = extra_fields

        return json.dumps(log_data, ensure_ascii=False)


def setup_structured_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    app_name: str = "baixing_law",
    use_json: bool = True,
) -> None:
    """
    配置结构化日志系统

    Args:
        log_level: 日志级别
        log_dir: 日志目录
        app_name: 应用名称
        use_json: 是否使用 JSON 格式输出
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 选择格式化器
    if use_json:
        formatter = JSONLogFormatter()
    else:
        formatter = StructuredLogFormatter()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器 - 普通日志
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    file_handler = logging.FileHandler(
        log_path / f"{app_name}_{today}.log",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 文件处理器 - 错误日志
    error_handler = logging.FileHandler(
        log_path / f"{app_name}_error_{today}.log",
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # 降低第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logging.info(
        "Structured logging configured: level=%s, dir=%s, json=%s",
        log_level,
        log_dir,
        use_json)


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, name: str = "app"):
        self.logger = logging.getLogger(name)
        self.name = name

    def _log(
        self,
        level: int,
        message: str,
        extra: Optional[dict[str, Any]] = None,
        exc_info: bool = False,
    ) -> None:
        """记录日志"""
        log_extra = extra or {}
        self.logger.log(level, message, extra=log_extra, exc_info=exc_info)

    def info(self, message: str, **kwargs: Any) -> None:
        """INFO 级别日志"""
        self._log(logging.INFO, message, kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """DEBUG 级别日志"""
        self._log(logging.DEBUG, message, kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """WARNING 级别日志"""
        self._log(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """ERROR 级别日志"""
        self._log(logging.ERROR, message, kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """CRITICAL 级别日志"""
        self._log(logging.CRITICAL, message, kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """记录异常日志"""
        self._log(logging.ERROR, message, kwargs, exc_info=True)


def get_logger(name: str = "app") -> StructuredLogger:
    """获取结构化日志记录器"""
    return StructuredLogger(name)


# 单例实例
structured_logger = StructuredLogger()
