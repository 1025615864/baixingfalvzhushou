"""统一错误码定义"""
from enum import Enum
from typing import Optional, Any, Dict


class ErrorCode(str, Enum):
    POST_NOT_FOUND = "C40401"
    POST_NO_PERMISSION = "C40301"
    POST_ALREADY_DELETED = "C40402"
    POST_CONTENT_BLOCKED = "C42201"
    POST_RATE_LIMITED = "C42901"

    COMMENT_NOT_FOUND = "C40403"
    COMMENT_NO_PERMISSION = "C40302"
    COMMENT_CONTENT_BLOCKED = "C42202"

    USER_NOT_FOUND = "C40404"
    USER_BANNED = "C40303"

    REPORT_NOT_FOUND = "C40405"
    REPORT_ALREADY_EXISTS = "C40901"
    REPORT_ALREADY_HANDLED = "C40902"

    INVALID_PARAMETER = "C40001"
    INVALID_TOKEN = "C40101"
    TOKEN_EXPIRED = "C40102"

    SERVICE_UNAVAILABLE = "C50301"
    INTERNAL_ERROR = "C50001"


ERROR_MESSAGES: Dict[str, str] = {
    ErrorCode.POST_NOT_FOUND: "帖子不存在",
    ErrorCode.POST_NO_PERMISSION: "无权操作此帖子",
    ErrorCode.POST_ALREADY_DELETED: "帖子已被删除",
    ErrorCode.POST_CONTENT_BLOCKED: "内容包含违规信息",
    ErrorCode.POST_RATE_LIMITED: "发帖过于频繁，请稍后再试",

    ErrorCode.COMMENT_NOT_FOUND: "评论不存在",
    ErrorCode.COMMENT_NO_PERMISSION: "无权操作此评论",
    ErrorCode.COMMENT_CONTENT_BLOCKED: "评论内容包含违规信息",

    ErrorCode.USER_NOT_FOUND: "用户不存在",
    ErrorCode.USER_BANNED: "用户已被封禁",

    ErrorCode.REPORT_NOT_FOUND: "举报不存在",
    ErrorCode.REPORT_ALREADY_EXISTS: "您已举报过此内容",
    ErrorCode.REPORT_ALREADY_HANDLED: "举报已被处理",

    ErrorCode.INVALID_PARAMETER: "参数错误",
    ErrorCode.INVALID_TOKEN: "Token无效",
    ErrorCode.TOKEN_EXPIRED: "Token已过期",

    ErrorCode.SERVICE_UNAVAILABLE: "服务暂时不可用",
    ErrorCode.INTERNAL_ERROR: "内部错误",
}


class CommunityException(Exception):
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
