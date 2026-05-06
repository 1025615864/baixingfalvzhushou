"""统一错误码定义"""
from enum import Enum
from typing import Optional, Any, Dict


class LegalErrorCode(Enum):
    CONSULTATION_NOT_FOUND = "L14041"
    CONSULTATION_ALREADY_CLOSED = "L14091"
    CONSULTATION_LIMIT_EXCEEDED = "L14291"
    CONSULTATION_STATUS_INVALID = "L14092"

    LAWYER_NOT_FOUND = "L24041"
    LAWYER_NOT_AVAILABLE = "L24091"
    LAWYER_ALREADY_VERIFIED = "L24092"
    LAWYER_NOT_VERIFIED = "L24093"
    LAWYER_SELF_ASSIGN_FORBIDDEN = "L24094"

    APPOINTMENT_NOT_FOUND = "L34041"
    APPOINTMENT_TIME_CONFLICT = "L34091"
    APPOINTMENT_SLOT_UNAVAILABLE = "L34092"
    APPOINTMENT_STATUS_INVALID = "L34093"

    REVIEW_ALREADY_SUBMITTED = "L44091"
    REVIEW_NOT_ALLOWED = "L44031"

    FIRM_NOT_FOUND = "L54041"
    FIRM_NOT_VERIFIED = "L54091"

    INVALID_PARAMETER = "L40001"
    INVALID_TOKEN = "L40101"
    TOKEN_EXPIRED = "L40102"

    SERVICE_UNAVAILABLE = "L50301"
    INTERNAL_ERROR = "L50001"


ERROR_MESSAGES: Dict[str, str] = {
    "L14041": "咨询不存在",
    "L14091": "咨询已关闭",
    "L14291": "咨询次数超限",
    "L14092": "咨询状态无效",

    "L24041": "律师不存在",
    "L24091": "律师当前不可用",
    "L24092": "律师已认证",
    "L24093": "律师未认证",
    "L24094": "不能分配给自己",

    "L34041": "预约不存在",
    "L34091": "预约时间冲突",
    "L34092": "该时段不可预约",
    "L34093": "预约状态无效",

    "L44091": "已提交过评价",
    "L44031": "无权评价此咨询",

    "L54041": "律所不存在",
    "L54091": "律所未认证",

    "L40001": "参数错误",
    "L40101": "Token无效",
    "L40102": "Token已过期",

    "L50301": "服务暂时不可用",
    "L50001": "内部错误",
}


class LegalException(Exception):
    def __init__(
        self,
        code: str,
        message: Optional[str] = None,
        detail: Optional[Any] = None,
        trace_id: Optional[str] = None,
    ):
        self.code = code
        self.message = message or ERROR_MESSAGES.get(code, "未知错误")
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