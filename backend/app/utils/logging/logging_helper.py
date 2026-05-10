"""日志规范工具

提供统一的日志记录方法，确保日志风格一致。
"""
from __future__ import annotations

import logging
import traceback
from typing import Any

logger = logging.getLogger(__name__)


def log_error_with_exc(
    logger: logging.Logger,
    message: str,
    exc: Exception | None = None,
    extra: dict[str, Any] | None = None
) -> None:
    """记录错误日志（带异常堆栈）

    Args:
        logger: 日志记录器
        message: 日志消息
        exc: 异常对象
        extra: 额外信息
    """
    if exc is not None:
        logger.error(
            message,
            exc_info=(type(exc), exc, exc.__traceback__),
            extra=extra or {}
        )
    else:
        logger.error(message, extra=extra or {})


def log_exception_with_exc(
    logger: logging.Logger,
    message: str,
    exc: Exception | None = None,
    extra: dict[str, Any] | None = None
) -> None:
    """记录异常日志（带异常堆栈）

    Args:
        logger: 日志记录器
        message: 日志消息
        exc: 异常对象
        extra: 额外信息
    """
    if exc is not None:
        logger.exception(
            message,
            extra=extra or {}
        )
    else:
        logger.exception(message, extra=extra or {})


def log_warning_with_exc(
    logger: logging.Logger,
    message: str,
    exc: Exception | None = None,
    extra: dict[str, Any] | None = None
) -> None:
    """记录警告日志（带异常堆栈）

    Args:
        logger: 日志记录器
        message: 日志消息
        exc: 异常对象
        extra: 额外信息
    """
    if exc is not None:
        logger.warning(
            message,
            exc_info=(type(exc), exc, exc.__traceback__),
            extra=extra or {}
        )
    else:
        logger.warning(message, extra=extra or {})


def get_request_id() -> str | None:
    """获取当前请求ID

    Returns:
        请求ID，如果不存在则返回None
    """
    try:
        from fastapi import Request
        from starlette.middleware.base import BaseHTTPMiddleware

        # 尝试从上下文获取request_id
        # 这里简化处理，实际应该从上下文中获取
        return None
    except Exception:
        return None


def add_request_id_to_context(
    context: dict[str, Any] | None
) -> dict[str, Any]:
    """将请求ID添加到上下文中

    Args:
        context: 上下文字典

    Returns:
        包含request_id的上下文字典
    """
    if context is None:
        context = {}

    request_id = get_request_id()
    if request_id is not None:
        context["request_id"] = request_id

    return context
