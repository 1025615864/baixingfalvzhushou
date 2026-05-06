"""认证服务测试"""
import pytest
from datetime import datetime, timedelta

from app.services.auth_service import AuthService
from app.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TestPasswordPolicy:
    """密码策略测试"""

    def test_valid_password(self):
        from app.services.password_policy import password_policy
        is_valid, _ = password_policy.validate("Test1234")
        assert is_valid is True

    def test_password_too_short(self):
        from app.services.password_policy import password_policy
        is_valid, msg = password_policy.validate("Test1")
        assert is_valid is False
        assert "8位" in msg

    def test_password_no_uppercase(self):
        from app.services.password_policy import password_policy
        is_valid, msg = password_policy.validate("test1234")
        assert is_valid is False
        assert "大写字母" in msg

    def test_password_no_digit(self):
        from app.services.password_policy import password_policy
        is_valid, msg = password_policy.validate("Testabcd")
        assert is_valid is False
        assert "数字" in msg

    def test_common_password_rejected(self):
        from app.services.password_policy import password_policy
        is_valid, msg = password_policy.validate("Password123")
        assert is_valid is False
        assert "太简单" in msg


class TestPasswordHashing:
    """密码哈希测试"""

    def test_hash_password(self):
        password = "TestPassword123"
        hashed = pwd_context.hash(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_correct_password(self):
        password = "TestPassword123"
        hashed = pwd_context.hash(password)
        assert pwd_context.verify(password, hashed) is True

    def test_verify_wrong_password(self):
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = pwd_context.hash(password)
        assert pwd_context.verify(wrong_password, hashed) is False


class TestAuthService:
    """认证服务测试"""

    @pytest.mark.asyncio
    async def test_register_success(self, db_session):
        auth_service = AuthService(db_session)
        result = await auth_service.register("13800138000", "Test1234")

        assert result is not None
        assert result.get("error") is None
        assert "access_token" in result
        assert "refresh_token" in result

    @pytest.mark.asyncio
    async def test_register_weak_password(self, db_session):
        auth_service = AuthService(db_session)
        result = await auth_service.register("13800138000", "123")

        assert result is not None
        assert result.get("error") == "weak_password"

    @pytest.mark.asyncio
    async def test_register_duplicate_phone(self, db_session):
        auth_service = AuthService(db_session)

        result1 = await auth_service.register("13800138000", "Test1234")
        assert result1 is not None

        result2 = await auth_service.register("13800138000", "Test1234")
        assert result2 is None

    @pytest.mark.asyncio
    async def test_login_success(self, db_session):
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")
        result = await auth_service.login("13800138000", "Test1234")

        assert result is not None
        assert "access_token" in result
        assert "refresh_token" in result

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, db_session):
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")
        result = await auth_service.login("13800138000", "WrongPassword")

        assert result is None

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, db_session):
        auth_service = AuthService(db_session)
        result = await auth_service.login("13900139000", "Test1234")

        assert result is None

    @pytest.mark.asyncio
    async def test_refresh_token(self, db_session):
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")
        login_result = await auth_service.login("13800138000", "Test1234")
        refresh_token = login_result["refresh_token"]

        refresh_result = await auth_service.refresh_access_token(refresh_token)

        assert refresh_result is not None
        assert "access_token" in refresh_result
        assert "refresh_token" in refresh_result
        assert refresh_result["access_token"] != login_result["access_token"]

    @pytest.mark.asyncio
    async def test_verify_token(self, db_session):
        auth_service = AuthService(db_session)

        await auth_service.register("13800138000", "Test1234")
        login_result = await auth_service.login("13800138000", "Test1234")
        access_token = login_result["access_token"]

        user_info = await auth_service.verify_token(access_token)

        assert user_info is not None
        assert user_info["role"] == "user"
        assert user_info["status"] == "active"

    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, db_session):
        auth_service = AuthService(db_session)
        user_info = await auth_service.verify_token("invalid_token")

        assert user_info is None
