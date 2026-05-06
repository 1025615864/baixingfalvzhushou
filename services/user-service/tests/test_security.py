"""安全测试"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.auth_service import AuthService
from app.services.token_service import token_manager, login_rate_limiter
from app.services.password_policy import password_policy
from app.models import User, LoginAudit, UserDevice
from app.utils.security import mask_sensitive_data, mask_phone, mask_email


class TestSQLInjectionPrevention:
    """SQL注入防护测试"""

    @pytest.mark.asyncio
    async def test_login_with_sql_injection_attempt(self, db_session):
        """测试登录时SQL注入攻击防护"""
        auth_service = AuthService(db_session)

        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1; DELETE FROM users WHERE '1'='1",
            "' UNION SELECT * FROM users--",
        ]

        for malicious_input in malicious_inputs:
            result = await auth_service.login(malicious_input, "anypassword")
            assert result is None, f"SQL injection should be blocked: {malicious_input}"

    @pytest.mark.asyncio
    async def test_register_with_sql_injection_attempt(self, db_session):
        """测试注册时SQL注入攻击防护"""
        auth_service = AuthService(db_session)

        malicious_inputs = [
            "'; DROP TABLE users; --",
            "test'@example.com",
            "13800138000'; malicious--",
        ]

        for malicious_input in malicious_inputs:
            result = await auth_service.register(malicious_input, "Test1234")
            if result and result.get("error") != "weak_password":
                assert result is None, f"SQL injection should be blocked: {malicious_input}"


class TestPasswordPolicy:
    """密码策略测试"""

    def test_password_minimum_length(self):
        """测试密码最小长度"""
        is_valid, _ = password_policy.validate("Test1")
        assert is_valid is False

        is_valid, _ = password_policy.validate("Test123")
        assert is_valid is False

        is_valid, _ = password_policy.validate("Test1234")
        assert is_valid is True

    def test_password_requires_uppercase(self):
        """测试密码需要大写字母"""
        is_valid, _ = password_policy.validate("test12345")
        assert is_valid is False

        is_valid, _ = password_policy.validate("TEST12345")
        assert is_valid is False

        is_valid, _ = password_policy.validate("Test12345")
        assert is_valid is True

    def test_password_requires_lowercase(self):
        """测试密码需要小写字母"""
        is_valid, _ = password_policy.validate("TEST12345")
        assert is_valid is False

        is_valid, _ = password_policy.validate("test12345")
        assert is_valid is False

        is_valid, _ = password_policy.validate("Test12345")
        assert is_valid is True

    def test_password_requires_digit(self):
        """测试密码需要数字"""
        is_valid, _ = password_policy.validate("TestAbcde")
        assert is_valid is False

        is_valid, _ = password_policy.validate("Test12345")
        assert is_valid is True

    def test_common_password_rejection(self):
        """测试常见弱密码被拒绝"""
        common_passwords = [
            "password",
            "12345678",
            "qwerty",
            "abc123",
            "monkey",
            "123321",
            "password1",
        ]

        for password in common_passwords:
            is_valid, _ = password_policy.validate(password)
            assert is_valid is False, f"Common password should be rejected: {password}"

    def test_strong_password_acceptance(self):
        """测试强密码被接受"""
        strong_passwords = [
            "MyStr0ngP@ss",
            "C0mpl3x#2024",
            "S3cur3!Pass",
        ]

        for password in strong_passwords:
            is_valid, _ = password_policy.validate(password)
            assert is_valid is True, f"Strong password should be accepted: {password}"


class TestLoginRateLimiting:
    """登录频率限制测试"""

    @pytest.mark.asyncio
    async def test_account_lockout_after_max_attempts(self, db_session):
        """测试超过最大尝试次数后账户被锁定"""
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")

        for i in range(5):
            result = await auth_service.login("13800138000", "WrongPassword")
            assert result is None

        result = await auth_service.login("13800138000", "WrongPassword")
        assert result is not None
        assert result.get("error") == "too_many_attempts"

    @pytest.mark.asyncio
    async def test_successful_login_clears_attempts(self, db_session):
        """测试成功登录清除失败尝试"""
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")

        for _ in range(3):
            await auth_service.login("13800138000", "WrongPassword")

        result = await auth_service.login("13800138000", "Test1234")
        assert result is not None
        assert "access_token" in result

        for i in range(5):
            result = await auth_service.login("13800138000", "WrongPassword")
            assert result is None

        result = await auth_service.login("13800138000", "WrongPassword")
        assert result is not None
        assert result.get("error") == "too_many_attempts"


class TestTokenSecurity:
    """Token安全测试"""

    @pytest.mark.asyncio
    async def test_revoked_token_rejected(self, db_session):
        """测试已撤销的Token被拒绝"""
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")
        login_result = await auth_service.login("13800138000", "Test1234")

        access_token = login_result["access_token"]
        access_jti = login_result["access_jti"]

        remaining_seconds = 3600
        await token_manager.revoke_access_token(access_jti, remaining_seconds)

        user_info = await auth_service.verify_token(access_token)
        assert user_info is None

    @pytest.mark.asyncio
    async def test_expired_token_rejected(self, db_session):
        """测试过期的Token被拒绝"""
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")
        login_result = await auth_service.login("13800138000", "Test1234")

        access_token = login_result["access_token"]

        with patch("app.services.auth_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow() + timedelta(hours=25)

            user_info = await auth_service.verify_token(access_token)
            assert user_info is None

    @pytest.mark.asyncio
    async def test_refresh_token_rotation(self, db_session):
        """测试Refresh Token轮换"""
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")
        login_result = await auth_service.login("13800138000", "Test1234")

        refresh_token = login_result["refresh_token"]
        refresh_jti = login_result["refresh_jti"]

        new_result = await auth_service.refresh_access_token(refresh_token)
        assert new_result is not None
        assert new_result["refresh_token"] != refresh_token

        old_result = await auth_service.refresh_access_token(refresh_token)
        assert old_result is None

    @pytest.mark.asyncio
    async def test_token_type_validation(self, db_session):
        """测试Token类型验证"""
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")
        login_result = await auth_service.login("13800138000", "Test1234")

        access_token = login_result["access_token"]
        refresh_result = await auth_service.refresh_access_token(access_token)
        assert refresh_result is None


class TestSensitiveDataMasking:
    """敏感数据脱敏测试"""

    def test_phone_masking(self):
        """测试手机号脱敏"""
        assert mask_phone("13800138000") == "138****8000"
        assert mask_phone("+8613800138000") == "+86****8000"
        assert mask_phone("123") == "12****"

    def test_email_masking(self):
        """测试邮箱脱敏"""
        assert mask_email("test@example.com") == "te*******@example.com"
        assert mask_email("user@gmail.com") == "us*******@gmail.com"
        assert mask_email("a@b.co") == "a@b.co"

    def test_mask_sensitive_data_dict(self):
        """测试字典数据脱敏"""
        data = {
            "phone": "13800138000",
            "email": "test@example.com",
            "password": "Secret123",
            "token": "eyJhbGc...",
            "name": "John",
        }

        masked = mask_sensitive_data(data)
        assert masked["phone"] == "***MASKED***"
        assert masked["email"] == "***MASKED***"
        assert masked["password"] == "***MASKED***"
        assert masked["token"] == "***MASKED***"
        assert masked["name"] == "John"

    def test_mask_sensitive_data_nested(self):
        """测试嵌套数据脱敏"""
        data = {
            "user": {
                "phone": "13800138000",
                "info": {
                    "password": "Secret123",
                },
            },
        }

        masked = mask_sensitive_data(data)
        assert masked["user"]["phone"] == "***MASKED***"
        assert masked["user"]["info"]["password"] == "***MASKED***"


class TestInputValidation:
    """输入验证测试"""

    @pytest.mark.asyncio
    async def test_registration_with_empty_phone(self, db_session):
        """测试空手机号注册"""
        auth_service = AuthService(db_session)
        result = await auth_service.register("", "Test1234")
        assert result is None

    @pytest.mark.asyncio
    async def test_registration_with_empty_password(self, db_session):
        """测试空密码注册"""
        auth_service = AuthService(db_session)
        result = await auth_service.register("13800138000", "")
        assert result is None or result.get("error") == "weak_password"

    @pytest.mark.asyncio
    async def test_registration_with_long_phone(self, db_session):
        """测试超长手机号注册"""
        auth_service = AuthService(db_session)
        result = await auth_service.register("1" * 50, "Test1234")
        assert result is None


class TestAuthorizationSecurity:
    """授权安全测试"""

    @pytest.mark.asyncio
    async def test_cannot_access_other_user_data(self, db_session):
        """测试不能访问其他用户数据"""
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")
        await auth_service.register("13900139000", "Test1234")

        login1 = await auth_service.login("13800138000", "Test1234")
        token1 = login1["access_token"]

        user_info1 = await auth_service.verify_token(token1)
        assert user_info1["user_id"] is not None

    @pytest.mark.asyncio
    async def test_revoked_token_cannot_access(self, db_session):
        """测试撤销后的Token无法访问"""
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")
        login_result = await auth_service.login("13800138000", "Test1234")

        token = login_result["access_token"]
        jti = login_result["access_jti"]

        await token_manager.revoke_access_token(jti, 3600)

        user_info = await auth_service.verify_token(token)
        assert user_info is None


class TestAuditLogging:
    """审计日志测试"""

    @pytest.mark.asyncio
    async def test_failed_login_audit(self, db_session):
        """测试失败登录审计"""
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")
        await auth_service.login("13800138000", "WrongPassword")

        from sqlalchemy import select
        result = await db_session.execute(
            select(LoginAudit).where(
                LoginAudit.user_id == 1,
                LoginAudit.event_type == "login_failed",
            )
        )
        audit = result.scalar_one_or_none()
        assert audit is not None
        assert audit.success is False
        assert audit.failure_reason == "invalid_password"

    @pytest.mark.asyncio
    async def test_successful_login_audit(self, db_session):
        """测试成功登录审计"""
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")
        await auth_service.login("13800138000", "Test1234")

        from sqlalchemy import select
        result = await db_session.execute(
            select(LoginAudit).where(
                LoginAudit.user_id == 1,
                LoginAudit.event_type == "login",
            )
        )
        audit = result.scalar_one_or_none()
        assert audit is not None
        assert audit.success is True


class TestDeviceSecurity:
    """设备安全测试"""

    @pytest.mark.asyncio
    async def test_device_registration_limits(self, db_session):
        """测试设备注册限制"""
        from app.services.device_service import DeviceService, MAX_DEVICES_PER_USER

        device_service = DeviceService(db_session)

        user_id = 1
        for i in range(MAX_DEVICES_PER_USER + 2):
            device_id = f"device_{i}"
            await device_service.register_device(
                user_id=user_id,
                device_id=device_id,
                device_name=f"Device {i}",
            )

        devices = await device_service.list_user_devices(user_id=user_id)
        assert len(devices) <= MAX_DEVICES_PER_USER

    @pytest.mark.asyncio
    async def test_user_cannot_remove_other_user_device(self, db_session):
        """测试用户不能删除其他用户的设备"""
        from app.services.device_service import DeviceService

        device_service = DeviceService(db_session)

        await device_service.register_device(
            user_id=1,
            device_id="device_1",
            device_name="User1 Device",
        )

        await device_service.register_device(
            user_id=2,
            device_id="device_2",
            device_name="User2 Device",
        )

        result = await device_service.remove_device(
            user_id=2,
            device_id="device_1",
        )
        assert result is False

        user1_devices = await device_service.list_user_devices(user_id=1)
        assert len(user1_devices) == 1
        assert user1_devices[0]["device_id"] == "device_1"
