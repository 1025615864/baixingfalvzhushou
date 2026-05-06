"""用户服务统一错误码

错误码格式: U + 模块(2位) + 序号(3位)
模块: 01=认证, 02=用户, 03=会员, 04=Token, 05=通用
"""
from enum import Enum
from typing import Optional, Any, Dict


class ErrorCode(str, Enum):
    AUTH_PHONE_EXISTS = "U01001"
    AUTH_WEAK_PASSWORD = "U01002"
    AUTH_INVALID_CREDENTIALS = "U01003"
    AUTH_ACCOUNT_LOCKED = "U01004"
    AUTH_TOKEN_EXPIRED = "U01005"
    AUTH_TOKEN_INVALID = "U01006"
    AUTH_TOKEN_REVOKED = "U01007"
    AUTH_REFRESH_TOKEN_USED = "U01008"
    AUTH_REFRESH_TOKEN_REUSED = "U01009"

    USER_NOT_FOUND = "U02001"
    USER_ALREADY_EXISTS = "U02002"
    USER_NO_PERMISSION = "U02003"
    USER_BANNED = "U02004"
    USER_DELETED = "U02005"
    USER_PHONE_EXISTS = "U02006"
    USER_EMAIL_EXISTS = "U02007"
    USER_INVALID_ROLE = "U02008"

    MEMBERSHIP_NOT_VIP = "U03001"
    MEMBERSHIP_EXPIRED = "U03002"
    MEMBERSHIP_TIER_INVALID = "U03003"
    MEMBERSHIP_UPGRADE_FAILED = "U03004"
    MEMBERSHIP_PERMISSION_DENIED = "U03005"

    TOKEN_BLACKLISTED = "U04001"
    TOKEN_NOT_FOUND = "U04002"
    TOKEN_ALREADY_REVOKED = "U04003"

    COMMON_INVALID_PARAMETER = "U05001"
    COMMON_INTERNAL_ERROR = "U05002"
    COMMON_SERVICE_UNAVAILABLE = "U05003"
    COMMON_NOT_IMPLEMENTED = "U05004"


ERROR_MESSAGES: Dict[str, str] = {
    ErrorCode.AUTH_PHONE_EXISTS: "手机号已注册",
    ErrorCode.AUTH_WEAK_PASSWORD: "密码强度不足",
    ErrorCode.AUTH_INVALID_CREDENTIALS: "用户名或密码错误",
    ErrorCode.AUTH_ACCOUNT_LOCKED: "账户已被锁定",
    ErrorCode.AUTH_TOKEN_EXPIRED: "Token已过期",
    ErrorCode.AUTH_TOKEN_INVALID: "Token无效",
    ErrorCode.AUTH_TOKEN_REVOKED: "Token已撤销",
    ErrorCode.AUTH_REFRESH_TOKEN_USED: "Refresh Token已使用",
    ErrorCode.AUTH_REFRESH_TOKEN_REUSED: "Refresh Token已被使用（可能被盗用）",

    ErrorCode.USER_NOT_FOUND: "用户不存在",
    ErrorCode.USER_ALREADY_EXISTS: "用户已存在",
    ErrorCode.USER_NO_PERMISSION: "无权操作",
    ErrorCode.USER_BANNED: "用户已被封禁",
    ErrorCode.USER_DELETED: "用户已注销",
    ErrorCode.USER_PHONE_EXISTS: "手机号已被使用",
    ErrorCode.USER_EMAIL_EXISTS: "邮箱已被使用",
    ErrorCode.USER_INVALID_ROLE: "无效的用户角色",

    ErrorCode.MEMBERSHIP_NOT_VIP: "非VIP会员",
    ErrorCode.MEMBERSHIP_EXPIRED: "会员已过期",
    ErrorCode.MEMBERSHIP_TIER_INVALID: "无效的会员等级",
    ErrorCode.MEMBERSHIP_UPGRADE_FAILED: "会员升级失败",
    ErrorCode.MEMBERSHIP_PERMISSION_DENIED: "会员权限不足",

    ErrorCode.TOKEN_BLACKLISTED: "Token已在黑名单",
    ErrorCode.TOKEN_NOT_FOUND: "Token不存在",
    ErrorCode.TOKEN_ALREADY_REVOKED: "Token已撤销",

    ErrorCode.COMMON_INVALID_PARAMETER: "参数错误",
    ErrorCode.COMMON_INTERNAL_ERROR: "内部错误",
    ErrorCode.COMMON_SERVICE_UNAVAILABLE: "服务暂时不可用",
    ErrorCode.COMMON_NOT_IMPLEMENTED: "功能未实现",
}


class UserServiceException(Exception):
    """用户服务异常基类"""

    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        detail: Optional[Any] = None,
        trace_id: Optional[str] = None,
    ):
        self.code = code.value
        self.message = message or ERROR_MESSAGES.get(code.value, "未知错误")
        self.detail = detail
        self.trace_id = trace_id
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.detail is not None:
            result["detail"] = self.detail
        if self.trace_id is not None:
            result["trace_id"] = self.trace_id
        return result


class AuthException(UserServiceException):
    """认证异常"""
    pass


class UserException(UserServiceException):
    """用户异常"""
    pass


class MembershipException(UserServiceException):
    """会员异常"""
    pass


class TokenException(UserServiceException):
    """Token异常"""
    pass


def get_error_response(code: ErrorCode, message: Optional[str] = None, detail: Any = None) -> Dict[str, Any]:
    """生成错误响应字典"""
    return {
        "code": code.value,
        "message": message or ERROR_MESSAGES.get(code.value, "未知错误"),
        "detail": detail,
    }
