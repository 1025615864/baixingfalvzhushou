"""敏感信息脱敏工具

提供日志敏感信息脱敏功能，支持多种数据格式和脱敏策略。
"""
from __future__ import annotations

import json
import logging
import re
import urllib.parse
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MaskLevel(str, Enum):
    """脱敏级别"""
    NONE = "none"           # 不脱敏（仅开发环境）
    MINIMAL = "minimal"     # 最小脱敏（保留更多上下文）
    STANDARD = "standard"   # 标准脱敏（默认）
    STRICT = "strict"       # 严格脱敏（完全脱敏敏感信息）


class DataSanitizer:
    """增强型数据脱敏器

    支持多种敏感字段类型和脱敏策略：
    - 身份证号（18位和15位）
    - 手机号（中国大陆）
    - 银行卡号（16-19位）
    - 信用卡CVV/CVC
    - 密码/密钥/token
    - 邮箱地址
    - IP地址
    - 地址信息

    支持多种数据格式：
    - JSON
    - Query String
    - Headers
    - URL路径
    """

    # 更完善的敏感字段名匹配（支持多种命名风格）
    SENSITIVE_FIELDS = {
        # 密码相关
        "password", "passwd", "pwd", "user_password", "login_password",
        "old_password", "new_password", "confirm_password", "user_pwd",
        # Token相关
        "token", "access_token", "refresh_token", "auth_token", "jwt",
        "bearer_token", "id_token", "api_token", "csrf_token",
        # 密钥相关
        "secret", "secret_key", "private_key", "api_key", "apikey",
        "app_secret", "client_secret", "app_key", "signature",
        "encryption_key", "decryption_key", "sign_key",
        # 银行卡相关
        "card_number", "card_no", "bank_card", "credit_card",
        "debit_card", "card_num", "bank_card_no", "bank_account",
        "account_number", "account_no", "iban", "swift_code",
        # 身份证相关
        "id_card", "id_number", "id_no", "citizen_id", "identity_card",
        "identity_number", "national_id", "resident_id",
        # 手机号相关
        "phone", "mobile", "tel", "telephone", "phone_number",
        "mobile_phone", "cell_phone", "contact_phone",
        # 邮箱相关
        "email", "mail", "e_mail", "email_address", "mail_address",
        # CVV/CVC
        "cvv", "cvc", "cvv2", "cvc2", "security_code", "card_code",
        # 其他敏感信息
        "ssn", "social_security_number", "passport", "passport_no",
        "birth_date", "birthday", "address", "home_address",
        "work_address", "postal_code", "zip_code",
        # OAuth相关
        "oauth_code", "authorization_code", "auth_code", "code_verifier",
        "oauth_token", "oauth_secret",
        # 会话相关
        "session_id", "session_token", "cookie", "set_cookie",
        # 生物识别
        "fingerprint", "face_data", "biometric",
    }

    # 正则表达式模式 - 用于内容检测
    PATTERNS = {
        # 身份证号（18位或15位）
        "id_card_18": r"(?<!\d)(\d{17}[\dXx])(?!\d)",
        "id_card_15": r"(?<!\d)(\d{15})(?!\d)",
        # 手机号（中国大陆）
        "phone": r"(?<!\d)(1[3-9]\d{9})(?!\d)",
        # 银行卡号（16-19位，避免与手机号、身份证号混淆）
        # 使用负向前瞻/后顾避免误匹配手机号和身份证号
        "bank_card": r"(?<!\d)(?<![1-9]\d{15})(?<![1-9]\d{16})(?<![1-9]\d{17})(\d{16}|\d{17}|\d{18}|\d{19})(?!\d)(?!\d{2})(?![\dXx])",
        # CVV（3-4位数字，通常在特定上下文中）
        "cvv": r"\b(\d{3,4})\b",
        # 邮箱
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        # IP地址
        "ipv4": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
        # 密码字段值（key=value格式）
        "password_value": r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"&\'\s,;]+)',
        # Token字段值
        "token_value": r'(?i)(token|access_token|refresh_token)\s*[:=]\s*["\']?([^"&\'\s,;]+)',
        # API Key字段值
        "api_key_value": r'(?i)(api_key|apikey|api-key)\s*[:=]\s*["\']?([^"&\'\s,;]+)',
        # Secret字段值
        "secret_value": r'(?i)(secret|secret_key|private_key)\s*[:=]\s*["\']?([^"&\'\s,;]+)',
        # Authorization头
        "authorization": r"(?i)(authorization\s*:\s*bearer\s+)([a-zA-Z0-9\-_]+)",
        # JWT Token
        "jwt": r"eyJ[a-zA-Z0-9\-_]*\.eyJ[a-zA-Z0-9\-_]*\.[a-zA-Z0-9\-_]*",
    }

    # URL路径中的敏感模式
    URL_SENSITIVE_PATTERNS = [
        (re.compile(r"(/users?/\d+)", re.IGNORECASE), r"/user/***"),
        (re.compile(r"(/accounts?/\d+)", re.IGNORECASE), r"/account/***"),
        (re.compile(r"(/cards?/\d+)", re.IGNORECASE), r"/card/***"),
        (re.compile(r"(/orders?/\d+)", re.IGNORECASE), r"/order/***"),
        (re.compile(r"(/payments?/\d+)", re.IGNORECASE), r"/payment/***"),
    ]

    def __init__(self, mask_char: str = "*", mask_level: MaskLevel = MaskLevel.STANDARD):
        """初始化脱敏器

        Args:
            mask_char: 掩码字符
            mask_level: 脱敏级别
        """
        self.mask_char = mask_char
        self.mask_level = mask_level
        self._custom_sensitive_fields: set[str] = set()
        self._compile_patterns()

    def add_sensitive_field(self, field: str) -> None:
        """添加自定义敏感字段

        Args:
            field: 字段名
        """
        self._custom_sensitive_fields.add(field.lower().replace("-", "_"))

    def _compile_patterns(self) -> None:
        """编译正则表达式模式"""
        self._compiled_patterns = {
            name: re.compile(pattern) for name, pattern in self.PATTERNS.items()
        }

    def set_mask_level(self, level: MaskLevel | str) -> None:
        """设置脱敏级别

        Args:
            level: 脱敏级别
        """
        if isinstance(level, str):
            level = MaskLevel(level.lower())
        self.mask_level = level

    def _is_sensitive_field(self, field_name: str) -> bool:
        """检查字段名是否为敏感字段

        Args:
            field_name: 字段名

        Returns:
            是否为敏感字段
        """
        if not field_name:
            return False

        # 转换为小写和下划线格式进行匹配
        normalized = field_name.lower().replace("-", "_")
        return normalized in self.SENSITIVE_FIELDS or normalized in self._custom_sensitive_fields

    def _mask_string(self, value: str, pattern_type: str = "default") -> str:
        """脱敏字符串

        Args:
            value: 原始值
            pattern_type: 模式类型

        Returns:
            脱敏后的值
        """
        if not value or self.mask_level == MaskLevel.NONE:
            return value

        if self.mask_level == MaskLevel.STRICT:
            return self.mask_char * min(len(value), 8)

        # 根据类型选择脱敏策略
        handlers = {
            "email": self._mask_email,
            "phone": self._mask_phone,
            "id_card": self._mask_id_card,
            "bank_card": self._mask_bank_card,
            "cvv": self._mask_cvv,
            "ip": self._mask_ip,
            "default": self._mask_default,
        }

        handler = handlers.get(pattern_type, handlers["default"])
        return handler(value)

    def _mask_email(self, email: str) -> str:
        """脱敏邮箱"""
        if "@" not in email:
            return self._mask_default(email)

        username, domain = email.split("@", 1)
        if self.mask_level == MaskLevel.MINIMAL:
            # 保留更多字符
            if len(username) > 3:
                masked_username = username[:2] + self.mask_char * (len(username) - 2)
            else:
                masked_username = self.mask_char * len(username)
        else:
            # 标准脱敏
            if len(username) > 6:
                masked_username = username[:3] + self.mask_char * (len(username) - 6) + username[-3:]
            else:
                masked_username = username[0] + self.mask_char * (len(username) - 1)

        return f"{masked_username}@{domain}"

    def _mask_phone(self, phone: str) -> str:
        """脱敏手机号"""
        digits = re.sub(r"\D", "", phone)
        if len(digits) != 11:
            # 对于非11位数字，如果不是其他模式，保持原样或简单脱敏
            return phone

        if self.mask_level == MaskLevel.MINIMAL:
            # 最小模式：保留前3后4
            return digits[:3] + self.mask_char * 4 + digits[-4:]
        else:
            # 标准/严格模式：保留前3后4
            return digits[:3] + self.mask_char * 4 + digits[-4:]

    def _mask_id_card(self, id_card: str) -> str:
        """脱敏身份证号"""
        if len(id_card) == 18:
            if self.mask_level == MaskLevel.MINIMAL:
                return id_card[:6] + self.mask_char * 8 + id_card[-4:]
            else:
                return id_card[:4] + self.mask_char * 10 + id_card[-4:]
        elif len(id_card) == 15:
            if self.mask_level == MaskLevel.MINIMAL:
                return id_card[:4] + self.mask_char * 7 + id_card[-4:]
            else:
                return id_card[:2] + self.mask_char * 9 + id_card[-4:]

        return self._mask_default(id_card)

    def _mask_bank_card(self, card: str) -> str:
        """脱敏银行卡号"""
        digits = re.sub(r"\D", "", card)
        if len(digits) < 16 or len(digits) > 19:
            return self._mask_default(card)

        if self.mask_level == MaskLevel.MINIMAL:
            # 保留前6后4
            return digits[:6] + self.mask_char * (len(digits) - 10) + digits[-4:]
        else:
            # 标准脱敏：保留前4后4
            return digits[:4] + self.mask_char * (len(digits) - 8) + digits[-4:]

    def _mask_cvv(self, cvv: str) -> str:
        """脱敏CVV"""
        return self.mask_char * len(cvv)

    def _mask_ip(self, ip: str) -> str:
        """脱敏IP地址"""
        if "." in ip:  # IPv4
            parts = ip.split(".")
            if len(parts) == 4:
                if self.mask_level == MaskLevel.MINIMAL:
                    return f"{parts[0]}.{parts[1]}.{parts[2]}.*"
                else:
                    return f"{parts[0]}.{parts[1]}.*.*"
        elif ":" in ip:  # IPv6
            parts = ip.split(":")
            if len(parts) >= 4:
                return f"{':'.join(parts[:2])}::***"

        return self._mask_default(ip)

    def _mask_default(self, value: str) -> str:
        """默认脱敏策略"""
        if len(value) <= 4:
            return self.mask_char * len(value)
        elif len(value) <= 8:
            return value[:2] + self.mask_char * (len(value) - 4) + value[-2:]
        else:
            return value[:3] + self.mask_char * (len(value) - 6) + value[-3:]

    def sanitize_dict(self, data: dict[str, Any], depth: int = 0, max_depth: int = 10) -> dict[str, Any]:
        """脱敏字典数据

        Args:
            data: 原始字典
            depth: 当前深度
            max_depth: 最大递归深度

        Returns:
            脱敏后的字典
        """
        if depth > max_depth:
            return {"__truncated__": "Max recursion depth reached"}

        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            # 检查是否为敏感字段
            if self._is_sensitive_field(key):
                sanitized[key] = self._mask_sensitive_value(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value, depth + 1, max_depth)
            elif isinstance(value, list):
                sanitized[key] = self._sanitize_list(value, depth + 1, max_depth)
            elif isinstance(value, str):
                # 检查字符串内容是否包含敏感信息
                sanitized[key] = self.sanitize_string_content(value)
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_list(self, data: list[Any], depth: int, max_depth: int) -> list[Any]:
        """脱敏列表数据"""
        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(self.sanitize_dict(item, depth, max_depth))
            elif isinstance(item, list):
                result.append(self._sanitize_list(item, depth, max_depth))
            elif isinstance(item, str):
                result.append(self.sanitize_string_content(item))
            else:
                result.append(item)
        return result

    def _mask_sensitive_value(self, value: Any) -> str:
        """脱敏敏感值（敏感字段完全脱敏）"""
        if value is None:
            return "***"

        if isinstance(value, bool):
            return str(value)

        if isinstance(value, (int, float)):
            return self.mask_char * min(len(str(value)), 6)

        if isinstance(value, str):
            if not value:
                return ""
            if self.mask_level == MaskLevel.STRICT:
                return "***REDACTED***"
            # 对于明确标记的敏感字段，使用完全脱敏
            return "***"

        return "***"

    def sanitize_string_content(self, text: str) -> str:
        """脱敏字符串中的敏感内容

        检测并脱敏文本中可能包含的敏感信息
        """
        if not text or self.mask_level == MaskLevel.NONE:
            return text

        result = text

        # 脱敏JWT token
        result = self._compiled_patterns["jwt"].sub("***JWT_TOKEN***", result)

        # 脱敏身份证号
        result = self._compiled_patterns["id_card_18"].sub(
            lambda m: self._mask_id_card(m.group(0)), result
        )
        result = self._compiled_patterns["id_card_15"].sub(
            lambda m: self._mask_id_card(m.group(0)), result
        )

        # 脱敏手机号
        result = self._compiled_patterns["phone"].sub(
            lambda m: self._mask_phone(m.group(0)), result
        )

        # 脱敏邮箱
        result = self._compiled_patterns["email"].sub(
            lambda m: self._mask_email(m.group(0)), result
        )

        # 脱敏银行卡号（需要更谨慎，避免误伤）
        def mask_bank_card_match(match: re.Match[str]) -> str:
            digits = match.group(0)
            # 排除手机号和身份证号
            if len(digits) == 11 and digits.startswith("1"):
                return digits
            if len(digits) in (15, 18):
                return digits
            return self._mask_bank_card(digits)

        result = self._compiled_patterns["bank_card"].sub(mask_bank_card_match, result)

        # 脱敏Authorization头
        result = self._compiled_patterns["authorization"].sub(r"\1***TOKEN***", result)

        return result

    def sanitize_json(self, json_str: str) -> str:
        """脱敏JSON字符串

        Args:
            json_str: JSON字符串

        Returns:
            脱敏后的JSON字符串
        """
        try:
            data = json.loads(json_str)
            sanitized = self.sanitize_dict(data)
            return json.dumps(sanitized, ensure_ascii=False)
        except json.JSONDecodeError as e:
            # 如果不是有效JSON，作为普通字符串处理
            logger.debug(f"JSON parse error during sanitization: {e}")
            return self.sanitize_string_content(json_str)
        except (TypeError, ValueError) as e:
            # JSON序列化/反序列化错误
            logger.warning(f"JSON processing error during sanitization: {e}")
            return self.sanitize_string_content(json_str)

    def sanitize_query_string(self, query_string: str) -> str:
        """脱敏Query String

        Args:
            query_string: URL查询字符串

        Returns:
            脱敏后的查询字符串
        """
        if not query_string:
            return query_string

        try:
            params = urllib.parse.parse_qs(query_string)
            sanitized_params = {}

            for key, values in params.items():
                if self._is_sensitive_field(key):
                    sanitized_params[key] = [self._mask_sensitive_value(v) for v in values]
                else:
                    # 检查值中是否包含敏感信息
                    sanitized_values = []
                    for value in values:
                        sanitized_values.append(self.sanitize_string_content(value))
                    sanitized_params[key] = sanitized_values

            return urllib.parse.urlencode(sanitized_params, doseq=True)
        except Exception as parse_err:
            # 解析失败，返回原始字符串的脱敏版本
            logger.debug(f"Query string parse error during sanitization: {parse_err}")
            return self.sanitize_string_content(query_string)

    def sanitize_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """脱敏HTTP Headers

        Args:
            headers: HTTP头字典

        Returns:
            脱敏后的头字典
        """
        sensitive_headers = {
            "authorization", "cookie", "set-cookie", "x-api-key",
            "x-auth-token", "x-csrf-token", "x-requested-with",
        }

        sanitized = {}
        for key, value in headers.items():
            lower_key = key.lower()
            if lower_key in sensitive_headers:
                if lower_key == "authorization":
                    # 保留认证类型，脱敏token
                    parts = value.split(" ", 1)
                    if len(parts) == 2:
                        auth_type = parts[0]
                        sanitized[key] = f"{auth_type} ***TOKEN***"
                    else:
                        sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = self.sanitize_string_content(value)

        return sanitized

    def sanitize_url(self, url: str) -> str:
        """脱敏URL

        Args:
            url: 完整URL

        Returns:
            脱敏后的URL
        """
        try:
            parsed = urllib.parse.urlparse(url)

            # 脱敏路径
            path = self.sanitize_url_path(parsed.path)

            # 脱敏查询参数
            query = self.sanitize_query_string(parsed.query)

            # 重新构建URL
            sanitized = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                path,
                parsed.params,
                query,
                parsed.fragment,
            ))

            return sanitized
        except Exception as url_err:
            logger.debug(f"URL parse error during sanitization: {url_err}")
            return self.sanitize_string_content(url)

    def sanitize_url_path(self, path: str) -> str:
        """脱敏URL路径中的敏感信息

        Args:
            path: URL路径

        Returns:
            脱敏后的路径
        """
        if not path:
            return path

        result = path

        # 应用URL敏感模式
        for pattern, replacement in self.URL_SENSITIVE_PATTERNS:
            result = pattern.sub(replacement, result)

        # 脱敏路径中可能包含的数字ID（如果看起来像敏感信息）
        # 但保留正常的API版本号等
        result = re.sub(r"(/v\d+/)(\d{15,})", r"\1***ID***", result)

        return result

    def sanitize_log_message(self, message: str) -> str:
        """脱敏日志消息

        Args:
            message: 原始消息

        Returns:
            脱敏后的消息
        """
        if self.mask_level == MaskLevel.NONE:
            return message

        result = message

        # 应用所有内容检测模式
        result = self.sanitize_string_content(result)

        # 脱敏特定格式的敏感值
        for pattern_name in ["password_value", "token_value", "api_key_value", "secret_value"]:
            pattern = self._compiled_patterns[pattern_name]
            result = pattern.sub(r'\1***', result)

        return result


# 全局脱敏器实例
sanitizer = DataSanitizer()


def sanitize_log_data(data: Any, mask_level: MaskLevel | None = None) -> Any:
    """脱敏日志数据（便捷函数）

    Args:
        data: 原始数据
        mask_level: 可选的脱敏级别覆盖

    Returns:
        脱敏后的数据
    """
    if mask_level:
        original_level = sanitizer.mask_level
        sanitizer.set_mask_level(mask_level)
        try:
            return _sanitize_data_internal(data)
        finally:
            sanitizer.set_mask_level(original_level)
    return _sanitize_data_internal(data)


def _sanitize_data_internal(data: Any) -> Any:
    """内部脱敏逻辑"""
    if isinstance(data, dict):
        return sanitizer.sanitize_dict(data)
    elif isinstance(data, str):
        return sanitizer.sanitize_log_message(data)
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    else:
        return data


def get_sanitized_logger(logger_instance: logging.Logger) -> logging.Logger:
    """获取脱敏日志记录器

    Args:
        logger_instance: 原始日志记录器

    Returns:
        脱敏日志记录器
    """
    class SanitizedLogger(logging.Logger):
        """脱敏日志记录器"""

        def _log(self, level, msg, *args, **kwargs):
            # 脱敏消息
            sanitized_msg = sanitize_log_data(msg)

            # 脱敏参数
            sanitized_args = [sanitize_log_data(arg) for arg in args]
            sanitized_kwargs = {k: sanitize_log_data(v) for k, v in kwargs.items()}

            # 调用原始日志方法
            super()._log(level, sanitized_msg, *sanitized_args, **sanitized_kwargs)

    # 创建脱敏日志记录器
    return SanitizedLogger(logger_instance.name)


# 便捷函数
sanitize_dict = sanitizer.sanitize_dict
sanitize_json = sanitizer.sanitize_json
sanitize_query_string = sanitizer.sanitize_query_string
sanitize_headers = sanitizer.sanitize_headers
sanitize_url = sanitizer.sanitize_url
sanitize_string = sanitizer.sanitize_string_content
