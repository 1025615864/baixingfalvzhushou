"""日志脱敏中间件

提供日志内容脱敏功能，过滤敏感信息。

敏感字段检测:
    - 密码: password, pwd, passwd
    - 令牌: token, access_token, refresh_token
    - 银行卡: card_number, bank_card, card_no
    - 身份证: id_card, id_number, citizen_id
    - 手机号: phone, mobile, tel
    - 邮箱: email (部分脱敏)
    - 密钥: secret, api_key, private_key
    - CVV: cvv, cvc, security_code

使用示例:
    ```python
    from app.core.middleware import LogSanitizerMiddleware

    app.add_middleware(LogSanitizerMiddleware)
    ```

自定义规则:
    ```python
    from app.core.middleware.log_sanitizer import LogSanitizer

    sanitizer = LogSanitizer()
    sanitizer.add_pattern(r"custom_\\w+", "***")
    ```
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.utils.security.data_sanitizer import DataSanitizer, MaskLevel

_default_data_sanitizer = DataSanitizer()

logger = logging.getLogger(__name__)


class LogSanitizer:
    """日志内容脱敏器

    提供敏感信息检测和脱敏功能。

    Attributes:
        patterns: 正则表达式模式列表
        field_names: 需要检测的字段名集合
        replacements: 脱敏替换规则
    """

    # 保留向后兼容的默认模式
    DEFAULT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r'"(password|pwd|passwd|secret|api_key|private_key)"\s*:\s*"[^"]*"', re.IGNORECASE), r'"\1":"***"'),
        (re.compile(r'"(access_token|refresh_token|token)"\s*:\s*"[^"]*"', re.IGNORECASE), r'"\1":"***"'),
        (re.compile(r'"(card_number|card_no|bank_card)"\s*:\s*"\d{16,19}"', re.IGNORECASE), r'"\1":"****"'),
        (re.compile(r'"(id_card|id_number|citizen_id)"\s*:\s*"\d{15,18}"', re.IGNORECASE), r'"\1":"********"'),
        (re.compile(r'"(phone|mobile|tel)"\s*:\s*"\d{11}"', re.IGNORECASE), r'"\1":"***"'),
        (re.compile(r'"email"\s*:\s*"[^"]+@[^"]+\.[^"]+"', re.IGNORECASE), r'"email":"***"'),
    ]

    # 保留向后兼容的敏感字段集合
    SENSITIVE_FIELDS = {
        "password", "pwd", "passwd", "secret", "api_key", "private_key",
        "access_token", "refresh_token", "token", "jwt",
        "card_number", "card_no", "bank_card", "credit_card",
        "id_card", "id_number", "citizen_id", "ssn",
        "phone", "mobile", "tel", "phone_number",
        "cvv", "cvc", "security_code",
        "oauth_code", "authorization_code",
        "email",
    }

    def __init__(self) -> None:
        self.patterns: list[tuple[re.Pattern[str], str]] = list(self.DEFAULT_PATTERNS)
        self.custom_replacements: dict[str, str] = {}
        self._data_sanitizer = _default_data_sanitizer

    def set_mask_level(self, level: MaskLevel | str) -> None:
        """设置脱敏级别

        Args:
            level: 脱敏级别
        """
        self._data_sanitizer.set_mask_level(level)

    def add_pattern(self, pattern: str | re.Pattern[str], replacement: str) -> None:
        """添加自定义脱敏规则

        Args:
            pattern: 正则表达式模式
            replacement: 替换字符串
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern, re.IGNORECASE)
        self.patterns.append((pattern, replacement))

    def sanitize_value(self, value: Any) -> Any:
        """脱敏单个值

        Args:
            value: 原始值

        Returns:
            脱敏后的值
        """
        if value is None:
            return None

        if isinstance(value, str):
            return self._sanitize_string(value)

        if isinstance(value, dict):
            return {k: self.sanitize_value(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self.sanitize_value(item) for item in value]

        return value

    def _sanitize_string(self, text: str) -> str:
        """脱敏字符串内容

        Args:
            text: 原始字符串

        Returns:
            脱敏后的字符串
        """
        # 优先使用增强型脱敏器
        result = self._data_sanitizer.sanitize_log_message(text)

        # 应用自定义模式
        for pattern, replacement in self.patterns:
            result = pattern.sub(replacement, result)

        return result

    def sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """脱敏字典数据

        Args:
            data: 原始字典

        Returns:
            脱敏后的字典
        """
        # 优先使用增强型脱敏器
        result = self._data_sanitizer.sanitize_dict(data)

        # 应用额外的自定义处理
        for key, value in list(result.items()):
            lower_key = key.lower().replace("-", "_")
            if lower_key in self.SENSITIVE_FIELDS and not isinstance(value, str):
                result[key] = "***REDACTED***"

        return result

    def sanitize_message(self, message: str) -> str:
        """脱敏日志消息

        Args:
            message: 原始消息

        Returns:
            脱敏后的消息
        """
        return self._sanitize_string(message)

    def sanitize_json(self, json_str: str) -> str:
        """脱敏JSON字符串

        Args:
            json_str: JSON字符串

        Returns:
            脱敏后的JSON字符串
        """
        return self._data_sanitizer.sanitize_json(json_str)

    def sanitize_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """脱敏HTTP Headers

        Args:
            headers: HTTP头字典

        Returns:
            脱敏后的头字典
        """
        return self._data_sanitizer.sanitize_headers(headers)

    def sanitize_url(self, url: str) -> str:
        """脱敏URL

        Args:
            url: 完整URL

        Returns:
            脱敏后的URL
        """
        return self._data_sanitizer.sanitize_url(url)

    def sanitize_query_string(self, query_string: str) -> str:
        """脱敏Query String

        Args:
            query_string: URL查询字符串

        Returns:
            脱敏后的查询字符串
        """
        return self._data_sanitizer.sanitize_query_string(query_string)


# 全局脱敏器实例
_sanitizer = LogSanitizer()


def sanitize_log_message(message: str) -> str:
    """便捷的日志消息脱敏函数

    Args:
        message: 原始日志消息

    Returns:
        脱敏后的消息
    """
    return _sanitizer.sanitize_message(message)


def sanitize_dict_data(data: dict[str, Any]) -> dict[str, Any]:
    """便捷的字典数据脱敏函数

    Args:
        data: 原始字典

    Returns:
        脱敏后的字典
    """
    return _sanitizer.sanitize_dict(data)


def sanitize_json_data(json_str: str) -> str:
    """便捷的JSON数据脱敏函数

    Args:
        json_str: JSON字符串

    Returns:
        脱敏后的JSON字符串
    """
    return _sanitizer.sanitize_json(json_str)


def sanitize_url_data(url: str) -> str:
    """便捷的URL脱敏函数

    Args:
        url: URL字符串

    Returns:
        脱敏后的URL
    """
    return _sanitizer.sanitize_url(url)


def set_mask_level(level: MaskLevel | str) -> None:
    """设置全局脱敏级别

    Args:
        level: 脱敏级别
    """
    _sanitizer.set_mask_level(level)
