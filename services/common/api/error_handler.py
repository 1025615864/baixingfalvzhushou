"""统一 API 错误响应

提供一致的错误响应格式、错误码体系和 HTTP 异常处理。
"""
from typing import Optional, Any
from enum import Enum
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorCode(str, Enum):
    """全局错误码

    格式: SVC-XXX
    SVC: 3位服务代码
    XXX: 3位错误序号

    服务代码:
    - AUTH: 认证服务
    - USER: 用户服务
    - LEGAL: 法律服务
    - AI: AI服务
    - COMM: 社区服务
    - ARCH: 档案服务
    - KNOW: 知识服务
    - NEWS: 新闻服务
    - NOTI: 通知服务
    - ORDR: 订单服务
    - PAY: 支付服务
    - PNT: 积分服务
    - SYS: 系统服务
    """

    # 通用错误 (SYS)
    INTERNAL_ERROR = "SYS-001"
    INVALID_REQUEST = "SYS-002"
    NOT_FOUND = "SYS-003"
    UNAUTHORIZED = "SYS-004"
    FORBIDDEN = "SYS-005"
    RATE_LIMITED = "SYS-006"
    SERVICE_UNAVAILABLE = "SYS-007"
    TIMEOUT = "SYS-008"

    # 认证错误 (AUTH)
    AUTH_INVALID_TOKEN = "AUTH-001"
    AUTH_TOKEN_EXPIRED = "AUTH-002"
    AUTH_INVALID_CREDENTIALS = "AUTH-003"
    AUTH_ACCOUNT_LOCKED = "AUTH-004"
    AUTH_PASSWORD_EXPIRED = "AUTH-005"

    # 用户错误 (USER)
    USER_DUPLICATE = "USER-001"
    USER_NOT_FOUND = "USER-002"
    USER_INVALID_EMAIL = "USER-003"
    USER_INVALID_PHONE = "USER-004"
    USER_PASSWORD_WEAK = "USER-005"

    # 法律知识错误 (LEGAL)
    LEGAL_NOT_FOUND = "LEGAL-001"
    LEGAL_INVALID_DATE = "LEGAL-002"

    # AI服务错误 (AI)
    AI_SERVICE_UNAVAILABLE = "AI-001"
    AI_RATE_LIMITED = "AI-002"
    AI_INVALID_PROMPT = "AI-003"

    # 社区错误 (COMM)
    COMM_POST_NOT_FOUND = "COMM-001"
    COMM_COMMENT_NOT_FOUND = "COMM-002"

    # 档案错误 (ARCH)
    ARCH_CASE_NOT_FOUND = "ARCH-001"
    ARCH_DUPLICATE_CASE = "ARCH-002"

    # 知识错误 (KNOW)
    KNOW_NOT_FOUND = "KNOW-001"
    KNOW_DUPLICATE = "KNOW-002"

    # 订单错误 (ORDR)
    ORDR_NOT_FOUND = "ORDR-001"
    ORDR_INVALID_STATUS = "ORDR-002"

    # 支付错误 (PAY)
    PAY_FAILED = "PAY-001"
    PAY_INSUFFICIENT_BALANCE = "PAY-002"
    PAY_DUPLICATE = "PAY-003"


class ErrorResponse(BaseModel):
    """统一错误响应格式"""
    code: str
    message: str
    details: Optional[dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: str


def create_error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: Optional[dict] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """创建统一错误响应"""
    from datetime import datetime, timezone

    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def create_http_exception(
    code: str,
    message: str,
    status_code: int = 400,
    details: Optional[dict] = None,
) -> HTTPException:
    """创建统一 HTTP 异常"""
    return HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "details": details,
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理器"""
    from datetime import datetime, timezone

    request_id = request.headers.get("x-request-id")

    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "code": detail.get("code", ErrorCode.INTERNAL_ERROR.value),
                    "message": detail.get("message", str(exc)),
                    "details": detail.get("details"),
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

    return JSONResponse(
        status_code=500,
        content={
            "code": ErrorCode.INTERNAL_ERROR.value,
            "message": "内部服务器错误",
            "details": None,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
