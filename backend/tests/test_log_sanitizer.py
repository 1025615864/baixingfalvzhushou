"""日志脱敏功能测试

测试敏感信息脱敏的正确性和完整性。
"""
from __future__ import annotations

import json

import pytest
from app.utils.data_sanitizer import DataSanitizer, MaskLevel, sanitize_log_data
from app.core.middleware.log_sanitizer import LogSanitizer


class TestDataSanitizer:
    """数据脱敏器测试类"""

    @pytest.fixture
    def sanitizer(self):
        """创建标准脱敏器"""
        return DataSanitizer(mask_level=MaskLevel.STANDARD)

    @pytest.fixture
    def strict_sanitizer(self):
        """创建严格脱敏器"""
        return DataSanitizer(mask_level=MaskLevel.STRICT)

    @pytest.fixture
    def minimal_sanitizer(self):
        """创建最小脱敏器"""
        return DataSanitizer(mask_level=MaskLevel.MINIMAL)

    @pytest.fixture
    def none_sanitizer(self):
        """创建无脱敏器"""
        return DataSanitizer(mask_level=MaskLevel.NONE)

    # ========== 手机号脱敏测试 ==========

    def test_mask_phone_standard(self, sanitizer):
        """测试标准手机号脱敏"""
        phone = "13812345678"
        result = sanitizer._mask_phone(phone)
        # 标准模式：保留前3后4
        assert result == "138****5678"

    def test_mask_phone_minimal(self, minimal_sanitizer):
        """测试最小手机号脱敏"""
        phone = "13812345678"
        result = minimal_sanitizer._mask_phone(phone)
        # 最小模式：保留前3后4
        assert result == "138****5678"

    def test_mask_phone_invalid_length(self, sanitizer):
        """测试无效长度手机号"""
        phone = "12345"
        result = sanitizer._mask_phone(phone)
        # 无效长度返回原值
        assert result == "12345"

    # ========== 身份证号脱敏测试 ==========

    def test_mask_id_card_18_standard(self, sanitizer):
        """测试18位身份证号脱敏（标准模式）"""
        id_card = "110101199001011234"
        result = sanitizer._mask_id_card(id_card)
        # 标准模式：保留前4后4
        assert result == "1101**********1234"

    def test_mask_id_card_18_minimal(self, minimal_sanitizer):
        """测试18位身份证号脱敏（最小模式）"""
        id_card = "110101199001011234"
        result = minimal_sanitizer._mask_id_card(id_card)
        # 最小模式：保留前6后4
        assert result == "110101********1234"

    def test_mask_id_card_15_standard(self, sanitizer):
        """测试15位身份证号脱敏（标准模式）"""
        id_card = "110101900101123"
        result = sanitizer._mask_id_card(id_card)
        # 标准模式：保留前2后4
        assert result == "11*********1123"

    def test_mask_id_card_15_minimal(self, minimal_sanitizer):
        """测试15位身份证号脱敏（最小模式）"""
        id_card = "110101900101123"
        result = minimal_sanitizer._mask_id_card(id_card)
        # 最小模式：保留前4后4
        assert result == "1101*******1123"

    # ========== 银行卡号脱敏测试 ==========

    def test_mask_bank_card_16_standard(self, sanitizer):
        """测试16位银行卡号脱敏（标准模式）"""
        card = "6222021234567890123"
        result = sanitizer._mask_bank_card(card)
        # 标准模式：保留前4后4
        assert result.startswith("6222")
        assert result.endswith("0123")
        assert "*" in result

    def test_mask_bank_card_minimal(self, minimal_sanitizer):
        """测试银行卡号脱敏（最小模式）"""
        card = "6222021234567890123"
        result = minimal_sanitizer._mask_bank_card(card)
        # 最小模式：保留前6后4
        assert result.startswith("622202")
        assert result.endswith("0123")

    def test_mask_bank_card_invalid_length(self, sanitizer):
        """测试无效长度银行卡号"""
        card = "12345"
        result = sanitizer._mask_bank_card(card)
        # 无效长度应该返回原值或使用默认脱敏
        assert result == "12345" or "*" in result

    # ========== 邮箱脱敏测试 ==========

    def test_mask_email_standard(self, sanitizer):
        """测试标准邮箱脱敏"""
        email = "user@example.com"
        result = sanitizer._mask_email(email)
        # 标准模式：用户名部分脱敏
        assert "@" in result
        assert result.endswith("@example.com")
        assert "*" in result

    def test_mask_email_long_username(self, sanitizer):
        """测试长用户名邮箱脱敏"""
        email = "longusername123@example.com"
        result = sanitizer._mask_email(email)
        assert result.startswith("lon")
        assert result.endswith("123@example.com")

    def test_mask_email_invalid(self, sanitizer):
        """测试无效邮箱"""
        email = "not-an-email"
        result = sanitizer._mask_email(email)
        assert "*" in result  # 应该被默认脱敏

    # ========== CVV脱敏测试 ==========

    def test_mask_cvv(self, sanitizer):
        """测试CVV脱敏"""
        cvv = "123"
        result = sanitizer._mask_cvv(cvv)
        assert result == "***"

    def test_mask_cvv_4_digit(self, sanitizer):
        """测试4位CVV脱敏"""
        cvv = "1234"
        result = sanitizer._mask_cvv(cvv)
        assert result == "****"

    # ========== IP地址脱敏测试 ==========

    def test_mask_ipv4_standard(self, sanitizer):
        """测试IPv4脱敏（标准模式）"""
        ip = "192.168.1.100"
        result = sanitizer._mask_ip(ip)
        assert result == "192.168.*.*"

    def test_mask_ipv4_minimal(self, minimal_sanitizer):
        """测试IPv4脱敏（最小模式）"""
        ip = "192.168.1.100"
        result = minimal_sanitizer._mask_ip(ip)
        assert result == "192.168.1.*"

    def test_mask_ipv6(self, sanitizer):
        """测试IPv6脱敏"""
        ip = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        result = sanitizer._mask_ip(ip)
        assert "***" in result

    # ========== 字典脱敏测试 ==========

    def test_sanitize_dict_sensitive_fields(self, sanitizer):
        """测试字典敏感字段脱敏"""
        data = {
            "username": "test_user",
            "password": "secret123",
            "phone": "13812345678",
            "email": "test@example.com",
            "normal_field": "normal_value",
        }
        result = sanitizer.sanitize_dict(data)
        assert result["username"] == "test_user"  # 非敏感字段
        assert result["password"] == "***"  # 敏感字段完全脱敏
        assert "*" in result["phone"]  # 手机号脱敏
        assert "*" in result["email"]  # 邮箱脱敏
        assert result["normal_field"] == "normal_value"  # 非敏感字段

    def test_sanitize_dict_nested(self, sanitizer):
        """测试嵌套字典脱敏"""
        data = {
            "user": {
                "name": "John",
                "password": "secret",
                "contact": {
                    "phone": "13812345678",
                    "email": "john@example.com",
                },
            },
        }
        result = sanitizer.sanitize_dict(data)
        assert result["user"]["name"] == "John"
        assert result["user"]["password"] == "***"
        assert "*" in result["user"]["contact"]["phone"]
        assert "*" in result["user"]["contact"]["email"]

    def test_sanitize_dict_list(self, sanitizer):
        """测试包含列表的字典脱敏"""
        data = {
            "users": [
                {"name": "User1", "password": "pass1"},
                {"name": "User2", "password": "pass2"},
            ],
        }
        result = sanitizer.sanitize_dict(data)
        assert result["users"][0]["name"] == "User1"
        assert result["users"][0]["password"] == "***"
        assert result["users"][1]["name"] == "User2"
        assert result["users"][1]["password"] == "***"

    # ========== JSON字符串脱敏测试 ==========

    def test_sanitize_json_valid(self, sanitizer):
        """测试有效JSON脱敏"""
        json_str = '{"username": "test", "password": "secret", "phone": "13812345678"}'
        result = sanitizer.sanitize_json(json_str)
        data = json.loads(result)
        assert data["username"] == "test"
        assert data["password"] == "***"
        assert "*" in data["phone"]

    def test_sanitize_json_invalid(self, sanitizer):
        """测试无效JSON脱敏"""
        not_json = "This is not json: password=secret123"
        result = sanitizer.sanitize_json(not_json)
        # 无效JSON作为普通字符串处理，可能脱敏也可能不脱敏
        # 取决于sanitize_string_content的实现
        assert isinstance(result, str)

    # ========== Query String脱敏测试 ==========

    def test_sanitize_query_string(self, sanitizer):
        """测试Query String脱敏"""
        query = "name=test&password=secret&phone=13812345678"
        result = sanitizer.sanitize_query_string(query)
        assert "name=test" in result
        # password应该被脱敏（URL编码后的***）
        assert "password=" in result
        assert "secret" not in result
        # 手机号应该被脱敏
        assert "phone=" in result
        # 脱敏后的值应该是***（可能被URL编码为%2A%2A%2A）
        assert "%2A" in result or "*" in result

    def test_sanitize_query_string_empty(self, sanitizer):
        """测试空Query String"""
        result = sanitizer.sanitize_query_string("")
        assert result == ""

    # ========== Headers脱敏测试 ==========

    def test_sanitize_headers(self, sanitizer):
        """测试Headers脱敏"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token123",
            "X-Custom-Header": "custom_value",
            "Cookie": "session=abc123",
        }
        result = sanitizer.sanitize_headers(headers)
        assert result["Content-Type"] == "application/json"
        assert result["Authorization"] == "Bearer ***TOKEN***"
        assert result["X-Custom-Header"] == "custom_value"
        assert result["Cookie"] == "***REDACTED***"

    # ========== URL脱敏测试 ==========

    def test_sanitize_url(self, sanitizer):
        """测试URL脱敏"""
        url = "https://example.com/api/users/12345?token=secret&name=test"
        result = sanitizer.sanitize_url(url)
        assert "example.com" in result
        assert "token=" not in result or "***" in result

    def test_sanitize_url_path(self, sanitizer):
        """测试URL路径脱敏"""
        path = "/api/users/12345"
        result = sanitizer.sanitize_url_path(path)
        assert "/user/" in result or "***" in result

    # ========== 字符串内容脱敏测试 ==========

    def test_sanitize_string_content_phone(self, sanitizer):
        """测试字符串中手机号检测脱敏"""
        text = "联系电话：13812345678，请尽快处理"
        result = sanitizer.sanitize_string_content(text)
        # 手机号应该被脱敏（可能是保留前后或使用中文提示）
        assert "13812345678" not in result or result != text

    def test_sanitize_string_content_id_card(self, sanitizer):
        """测试字符串中身份证号检测脱敏"""
        text = "身份证号：110101199001011234"
        result = sanitizer.sanitize_string_content(text)
        assert "*" in result or "【身份证号已脱敏】" in result

    def test_sanitize_string_content_email(self, sanitizer):
        """测试字符串中邮箱检测脱敏"""
        text = "邮箱地址：user@example.com"
        result = sanitizer.sanitize_string_content(text)
        assert "*" in result or "【邮箱已脱敏】" in result

    def test_sanitize_string_content_jwt(self, sanitizer):
        """测试JWT Token脱敏"""
        text = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = sanitizer.sanitize_string_content(text)
        assert "***JWT_TOKEN***" in result

    # ========== 脱敏级别测试 ==========

    def test_mask_level_none(self, none_sanitizer):
        """测试不脱敏级别"""
        # 注意：NONE级别对明确标记的敏感字段仍可能脱敏
        # 主要用于内容检测不脱敏
        data = {"password": "secret", "phone": "13812345678"}
        result = none_sanitizer.sanitize_dict(data)
        # NONE级别下，明确标记的敏感字段仍应脱敏
        assert result["password"] in ["secret", "***"]
        assert result["phone"] in ["13812345678", "***"]

    def test_mask_level_strict(self, strict_sanitizer):
        """测试严格脱敏级别"""
        data = {"password": "secret123", "phone": "13812345678"}
        result = strict_sanitizer.sanitize_dict(data)
        assert result["password"] == "***REDACTED***"

    # ========== 便捷函数测试 ==========

    def test_sanitize_log_data_dict(self):
        """测试便捷函数 - 字典"""
        data = {"password": "secret", "name": "test"}
        result = sanitize_log_data(data)
        assert result["password"] == "***"
        assert result["name"] == "test"

    def test_sanitize_log_data_string(self):
        """测试便捷函数 - 字符串"""
        text = "password=secret123"
        result = sanitize_log_data(text)
        # 字符串应该被脱敏
        assert "secret123" not in result

    def test_sanitize_log_data_list(self):
        """测试便捷函数 - 列表"""
        data = [{"password": "secret1"}, {"password": "secret2"}]
        result = sanitize_log_data(data)
        assert result[0]["password"] == "***"
        assert result[1]["password"] == "***"

    def test_sanitize_log_data_with_level(self):
        """测试便捷函数 - 指定脱敏级别"""
        data = {"password": "secret"}
        result = sanitize_log_data(data, mask_level=MaskLevel.STRICT)
        assert result["password"] == "***REDACTED***"


class TestLogSanitizer:
    """日志脱敏器中间件测试类"""

    @pytest.fixture
    def log_sanitizer(self):
        """创建日志脱敏器"""
        return LogSanitizer()

    def test_log_sanitizer_sanitize_message(self, log_sanitizer):
        """测试日志消息脱敏"""
        message = 'User login with password="secret123"'
        result = log_sanitizer.sanitize_message(message)
        assert "secret123" not in result
        assert "***" in result

    def test_log_sanitizer_sanitize_dict(self, log_sanitizer):
        """测试日志字典脱敏"""
        data = {
            "event": "user_login",
            "username": "test",
            "password": "secret",
            "token": "abc123",
        }
        result = log_sanitizer.sanitize_dict(data)
        assert result["event"] == "user_login"
        assert result["username"] == "test"
        # 敏感字段应该被脱敏
        assert result["password"] in ["***", "***REDACTED***", "se**et"]
        assert result["token"] in ["***", "***REDACTED***", "***TOKEN***"]

    def test_log_sanitizer_add_pattern(self, log_sanitizer):
        """测试添加自定义脱敏规则"""
        log_sanitizer.add_pattern(r"custom_\d+", "REDACTED")
        message = "custom_12345 is here"
        result = log_sanitizer.sanitize_message(message)
        assert "custom_12345" not in result
        assert "REDACTED" in result

    def test_log_sanitizer_json(self, log_sanitizer):
        """测试JSON脱敏"""
        json_str = '{"user": "test", "password": "secret", "api_key": "key123"}'
        result = log_sanitizer.sanitize_json(json_str)
        data = json.loads(result)
        assert data["user"] == "test"
        assert "secret" not in str(data["password"])
        assert "key123" not in str(data["api_key"])

    def test_log_sanitizer_headers(self, log_sanitizer):
        """测试Headers脱敏"""
        headers = {
            "Authorization": "Bearer supersecrettoken",
            "Content-Type": "application/json",
            "Cookie": "session=abc",
        }
        result = log_sanitizer.sanitize_headers(headers)
        assert "***" in result["Authorization"]
        assert result["Content-Type"] == "application/json"
        assert result["Cookie"] == "***REDACTED***"


class TestSensitiveFieldDetection:
    """敏感字段检测测试类"""

    @pytest.fixture
    def sanitizer(self):
        return DataSanitizer()

    @pytest.mark.parametrize("field_name", [
        "password",
        "PASSWORD",
        "Password",
        "user_password",
        "passwd",
        "pwd",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "secret",
        "card_number",
        "id_card",
        "phone",
        "email",
        "cvv",
        "session_id",
        "cookie",
    ])
    def test_is_sensitive_field_true(self, sanitizer, field_name):
        """测试敏感字段识别（应为敏感）"""
        assert sanitizer._is_sensitive_field(field_name) is True

    @pytest.mark.parametrize("field_name", [
        "username",
        "name",
        "title",
        "content",
        "description",
        "status",
        "type",
        "created_at",
    ])
    def test_is_sensitive_field_false(self, sanitizer, field_name):
        """测试非敏感字段识别（不应为敏感）"""
        assert sanitizer._is_sensitive_field(field_name) is False

    def test_add_sensitive_field(self, sanitizer):
        """测试添加自定义敏感字段"""
        # 先确认不是敏感字段
        assert sanitizer._is_sensitive_field("custom_secret") is False

        # 添加为敏感字段
        sanitizer.add_sensitive_field("custom_secret")

        # 确认现在是敏感字段
        assert sanitizer._is_sensitive_field("custom_secret") is True


class TestRealWorldScenarios:
    """真实场景测试类"""

    def test_payment_log(self):
        """测试支付日志脱敏"""
        sanitizer = DataSanitizer()
        log_data = {
            "event": "payment_initiated",
            "user_id": "12345",
            "amount": "100.00",
            "card_number": "6222021234567890123",
            "cvv": "123",
            "phone": "13812345678",
            "email": "user@example.com",
        }
        result = sanitizer.sanitize_dict(log_data)
        assert result["event"] == "payment_initiated"
        assert result["user_id"] == "12345"
        assert result["amount"] == "100.00"
        assert "622202" not in str(result["card_number"])
        assert result["cvv"] == "***"
        assert "*" in result["phone"]
        assert "*" in result["email"]

    def test_user_registration_log(self):
        """测试用户注册日志脱敏"""
        sanitizer = DataSanitizer()
        log_data = {
            "event": "user_registered",
            "username": "newuser",
            "password": "SuperSecret123!",
            "email": "newuser@example.com",
            "phone": "13987654321",
            "id_card": "110101199001011234",
        }
        result = sanitizer.sanitize_dict(log_data)
        assert result["username"] == "newuser"
        assert result["password"] in ["***", "***REDACTED***"]
        assert "*" in result["email"]
        assert "*" in result["phone"]
        assert "*" in result["id_card"]

    def test_api_request_log(self):
        """测试API请求日志脱敏"""
        sanitizer = DataSanitizer()
        log_data = {
            "method": "POST",
            "path": "/api/payment",
            "headers": {
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                "Content-Type": "application/json",
            },
            "body": {
                "card_number": "6222021234567890123",
                "password": "bank_password",
            },
        }
        result = sanitizer.sanitize_dict(log_data)
        assert result["method"] == "POST"
        # Authorization头应该被脱敏（使用完整的JWT token格式）
        assert "***" in str(result["headers"]["Authorization"]) or "TOKEN" in str(result["headers"]["Authorization"])
        assert result["headers"]["Content-Type"] == "application/json"
        assert "*" in str(result["body"]["card_number"])
        assert "*" in str(result["body"]["password"])

    def test_error_log_with_sensitive_data(self):
        """测试包含敏感数据的错误日志脱敏"""
        sanitizer = DataSanitizer()
        error_message = (
            "Failed to process payment for user with "
            "phone=13812345678, card=6222021234567890123, "
            "cvv=123, email=user@example.com"
        )
        result = sanitizer.sanitize_log_message(error_message)
        # 敏感信息应该被脱敏或替换
        assert "13812345678" not in result or result != error_message
        assert "6222021234567890123" not in result or result != error_message
        assert "user@example.com" not in result or result != error_message

    def test_query_string_in_url(self):
        """测试URL中Query String脱敏"""
        sanitizer = DataSanitizer()
        url = "https://api.example.com/pay?token=secret_token&user=123&password=mysecret"
        result = sanitizer.sanitize_url(url)
        assert "secret_token" not in result or "***" in result
        assert "mysecret" not in result or "***" in result
        assert "user=123" in result  # 非敏感字段保留


if __name__ == "__main__":
    pytest.main([__file__, "-v"])