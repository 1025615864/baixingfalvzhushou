"""敏感数据脱敏工具"""
import re
import logging
from typing import Any


SENSITIVE_FIELDS = {
    "password",
    "hashed_password",
    "old_password",
    "new_password",
    "confirm_password",
    "access_token",
    "refresh_token",
    "token",
    "jwt_secret",
    "jwt_secret_key",
    "api_key",
    "secret",
    "secret_key",
    "authorization",
    "credential",
    "private_key",
    "credit_card",
    "card_number",
    "cvv",
    "ssn",
    "id_card",
    "phone",
    "email",
}


MASKED_VALUE = "***MASKED***"


def mask_dict(data: dict, fields: set[str] | None = None) -> dict:
    """递归脱敏字典中的敏感字段

    Args:
        data: 待脱敏字典
        fields: 自定义敏感字段集合，None时使用默认

    Returns:
        脱敏后的字典
    """
    if fields is None:
        fields = SENSITIVE_FIELDS

    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if key.lower() in fields or any(f in key.lower() for f in fields):
            result[key] = MASKED_VALUE
        elif isinstance(value, dict):
            result[key] = mask_dict(value, fields)
        elif isinstance(value, list):
            result[key] = [
                mask_dict(v, fields) if isinstance(v, dict) else v
                for v in value
            ]
        else:
            result[key] = value

    return result


def mask_string(s: str, field_name: str = "") -> str:
    """对字符串进行部分脱敏（保留首尾字符）"""
    if not s or len(s) <= 4:
        return MASKED_VALUE

    field_lower = field_name.lower()
    if any(f in field_lower for f in ["phone", "mobile", "tel"]):
        if len(s) >= 7:
            return s[:3] + "****" + s[-4:]
        return s[:2] + "****"

    if any(f in field_lower for f in ["email"]):
        if "@" in s:
            parts = s.split("@")
            if len(parts[0]) >= 3:
                return parts[0][:2] + "***@" + parts[1]
        return MASKED_VALUE

    if len(s) >= 8:
        return s[:3] + "****" + s[-4:]

    return s[:2] + "****"


def mask_phone(phone: str) -> str:
    """脱敏手机号"""
    if not phone:
        return phone
    if len(phone) >= 7:
        return phone[:3] + "****" + phone[-4:]
    return phone[:2] + "****"


def mask_email(email: str) -> str:
    """脱敏邮箱"""
    if not email or "@" not in email:
        return email
    parts = email.split("@")
    if len(parts[0]) >= 3:
        return parts[0][:2] + "*******@" + parts[1]
    elif len(parts[0]) >= 2:
        return parts[0][0] + "****@" + parts[1]
    return email


def mask_sensitive_data(data: dict) -> dict:
    """脱敏敏感数据（兼容性别名）"""
    return mask_dict(data)


class SensitiveFilter(logging.Filter):
    """日志敏感字段过滤"""

    FIELD_PATTERN = re.compile(
        r'(password|token|secret|key|authorization|credential|jwt)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)',
        re.IGNORECASE
    )

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.mask_string(record.msg)

        if record.args:
            try:
                record.args = tuple(
                    self.mask_string(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
            except (TypeError, ValueError):
                pass

        return True

    def mask_string(self, s: str) -> str:
        def replacer(match):
            return f'{match.group(1)}***MASKED***'

        return self.FIELD_PATTERN.sub(replacer, s)


def setup_secure_logging():
    """配置安全日志"""
    sensitive_filter = SensitiveFilter()

    for handler in logging.root.handlers:
        handler.addFilter(sensitive_filter)

    return sensitive_filter
