"""错误分类细化工具

提供详细的错误分类和错误码体系。
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """错误码枚举"""

    # 通用错误 (1xxx)
    SUCCESS = "0000"
    UNKNOWN_ERROR = "1000"
    INVALID_REQUEST = "1001"
    UNAUTHORIZED = "1002"
    FORBIDDEN = "1003"
    NOT_FOUND = "1004"
    METHOD_NOT_ALLOWED = "1005"
    REQUEST_TIMEOUT = "1006"
    CONFLICT = "1007"
    UNPROCESSABLE_ENTITY = "1008"

    # 认证授权错误 (2xxx)
    TOKEN_INVALID = "2001"
    TOKEN_EXPIRED = "2002"
    TOKEN_MISSING = "2003"
    PERMISSION_DENIED = "2004"
    ACCOUNT_LOCKED = "2005"
    ACCOUNT_DISABLED = "2006"

    # 业务逻辑错误 (3xxx)
    BUSINESS_ERROR = "3000"
    INVALID_PARAMETER = "3001"
    RESOURCE_NOT_FOUND = "3002"
    RESOURCE_ALREADY_EXISTS = "3003"
    OPERATION_NOT_ALLOWED = "3004"
    QUOTA_EXCEEDED = "3005"
    BALANCE_INSUFFICIENT = "3006"

    # 支付错误 (4xxx)
    PAYMENT_ERROR = "4000"
    PAYMENT_FAILED = "4001"
    PAYMENT_TIMEOUT = "4002"
    PAYMENT_CANCELLED = "4003"
    PAYMENT_REFUND_FAILED = "4004"
    PAYMENT_CALLBACK_INVALID = "4005"

    # 数据库错误 (5xxx)
    DATABASE_ERROR = "5000"
    DATABASE_CONNECTION_FAILED = "5001"
    DATABASE_TIMEOUT = "5002"
    DATABASE_CONSTRAINT_VIOLATION = "5003"
    DATABASE_DEADLOCK = "5004"

    # 外部服务错误 (6xxx)
    EXTERNAL_SERVICE_ERROR = "6000"
    AI_SERVICE_ERROR = "6001"
    AI_SERVICE_TIMEOUT = "6002"
    AI_SERVICE_RATE_LIMIT = "6003"
    AI_SERVICE_UNAVAILABLE = "6004"

    # 系统错误 (7xxx)
    SYSTEM_ERROR = "7000"
    INTERNAL_SERVER_ERROR = "7001"
    SERVICE_UNAVAILABLE = "7002"
    MAINTENANCE_MODE = "7003"


class ErrorSeverity(str, Enum):
    """错误严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """错误类别"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS = "business"
    PAYMENT = "payment"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"


class ErrorDetail:
    """错误详情"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        details: dict[str, Any] | None = None
    ) -> None:
        self.code = code
        self.message = message
        self.severity = severity
        self.category = category
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """转换为字典

        Returns:
            字典表示
        """
        return {
            "code": self.code.value,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "details": self.details,
        }


class ErrorClassifier:
    """错误分类器"""

    @staticmethod
    def classify_error(
        exception: Exception
    ) -> ErrorDetail:
        """分类错误

        Args:
            exception: 异常对象

        Returns:
            错误详情
        """
        # 认证错误
        if "token" in str(exception).lower():
            return ErrorDetail(
                code=ErrorCode.TOKEN_INVALID,
                message="令牌无效",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.AUTHENTICATION,
            )

        # 数据库错误
        if "database" in str(exception).lower():
            return ErrorDetail(
                code=ErrorCode.DATABASE_ERROR,
                message="数据库错误",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.DATABASE,
            )

        # 支付错误
        if "payment" in str(exception).lower():
            return ErrorDetail(
                code=ErrorCode.PAYMENT_ERROR,
                message="支付错误",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.PAYMENT,
            )

        # AI服务错误
        if "ai" in str(exception).lower() or "openai" in str(exception).lower():
            return ErrorDetail(
                code=ErrorCode.AI_SERVICE_ERROR,
                message="AI服务错误",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.EXTERNAL_SERVICE,
            )

        # 默认错误
        return ErrorDetail(
            code=ErrorCode.UNKNOWN_ERROR,
            message="未知错误",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYSTEM,
        )

    @staticmethod
    def get_error_message(code: ErrorCode) -> str:
        """获取错误消息

        Args:
            code: 错误码

        Returns:
            错误消息
        """
        messages = {
            ErrorCode.SUCCESS: "成功",
            ErrorCode.UNKNOWN_ERROR: "未知错误",
            ErrorCode.INVALID_REQUEST: "无效请求",
            ErrorCode.UNAUTHORIZED: "未授权",
            ErrorCode.FORBIDDEN: "禁止访问",
            ErrorCode.NOT_FOUND: "资源不存在",
            ErrorCode.TOKEN_INVALID: "令牌无效",
            ErrorCode.TOKEN_EXPIRED: "令牌过期",
            ErrorCode.PAYMENT_FAILED: "支付失败",
            ErrorCode.DATABASE_ERROR: "数据库错误",
            ErrorCode.AI_SERVICE_ERROR: "AI服务错误",
            ErrorCode.INTERNAL_SERVER_ERROR: "内部服务器错误",
        }

        return messages.get(code, "未知错误")


# 错误码映射表
ERROR_CODE_MAP = {
    # 通用错误
    "0000": {"message": "成功", "severity": "info"},
    "1000": {"message": "未知错误", "severity": "error"},
    "1001": {"message": "无效请求", "severity": "error"},
    "1002": {"message": "未授权", "severity": "error"},
    "1003": {"message": "禁止访问", "severity": "error"},
    "1004": {"message": "资源不存在", "severity": "error"},

    # 认证授权错误
    "2001": {"message": "令牌无效", "severity": "error"},
    "2002": {"message": "令牌过期", "severity": "error"},
    "2003": {"message": "令牌缺失", "severity": "error"},

    # 业务逻辑错误
    "3000": {"message": "业务错误", "severity": "error"},
    "3001": {"message": "无效参数", "severity": "error"},
    "3002": {"message": "资源不存在", "severity": "error"},

    # 支付错误
    "4000": {"message": "支付错误", "severity": "error"},
    "4001": {"message": "支付失败", "severity": "error"},

    # 数据库错误
    "5000": {"message": "数据库错误", "severity": "error"},
    "5001": {"message": "数据库连接失败", "severity": "critical"},

    # 外部服务错误
    "6000": {"message": "外部服务错误", "severity": "error"},
    "6001": {"message": "AI服务错误", "severity": "error"},

    # 系统错误
    "7000": {"message": "系统错误", "severity": "error"},
    "7001": {"message": "内部服务器错误", "severity": "critical"},
}


def get_error_info(code: str) -> dict[str, Any]:
    """获取错误信息

    Args:
        code: 错误码

    Returns:
        错误信息
    """
    return ERROR_CODE_MAP.get(code, {
        "message": "未知错误",
        "severity": "error",
    })
