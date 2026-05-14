"""安全模块单元测试（密码策略、JWT 管理）"""
import pytest
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from services.common.security.password_policy import (
    validate_password,
    check_password_strength,
    PasswordPolicyError,
    COMMON_WEAK_PASSWORDS,
)
from services.common.security.jwt_manager import (
    JWTKeyManager,
    JWTKey,
)


class TestValidatePassword:
    """密码验证测试"""

    def test_valid_strong_password(self):
        """测试合法的强密码"""
        assert validate_password("MyStr0ng!Pass") is True

    def test_empty_password_raises_error(self):
        """测试空密码抛出异常"""
        with pytest.raises(PasswordPolicyError, match="密码不能为空"):
            validate_password("")

    def test_none_password_raises_error(self):
        """测试 None 密码抛出异常"""
        with pytest.raises(PasswordPolicyError, match="密码不能为空"):
            validate_password(None)

    def test_too_short_password(self):
        """测试太短的密码"""
        with pytest.raises(PasswordPolicyError, match="至少为 8 个字符"):
            validate_password("Short1!")

    def test_too_long_password(self):
        """测试太长的密码"""
        long_password = "A" * 129 + "1!"
        with pytest.raises(PasswordPolicyError, match="不能超过 128 个字符"):
            validate_password(long_password)

    def test_missing_uppercase(self):
        """测试缺少大写字母"""
        with pytest.raises(PasswordPolicyError, match="大写字母"):
            validate_password("mystr0ng!pass")

    def test_missing_lowercase(self):
        """测试缺少小写字母"""
        with pytest.raises(PasswordPolicyError, match="小写字母"):
            validate_password("MYSTR0NG!PASS")

    def test_missing_digit(self):
        """测试缺少数字"""
        with pytest.raises(PasswordPolicyError, match="数字"):
            validate_password("MyStrong!Pass")

    def test_missing_special_character(self):
        """测试缺少特殊字符"""
        with pytest.raises(PasswordPolicyError, match="特殊字符"):
            validate_password("MyStrong1Pass")

    def test_common_weak_password(self):
        """测试常见弱密码"""
        for pwd in ["password", "123456", "qwerty", "admin123"]:
            with pytest.raises(PasswordPolicyError, match="过于常见"):
                validate_password("Abc" + pwd[3:] + "!1")

    def test_password_contains_username(self):
        """测试密码包含用户名"""
        with pytest.raises(PasswordPolicyError, match="不能包含用户名"):
            validate_password("John1234!", username="John")

    def test_password_contains_email_prefix(self):
        """测试密码包含邮箱前缀"""
        with pytest.raises(PasswordPolicyError, match="不能包含邮箱前缀"):
            validate_password("John1234!", email="john@example.com")

    def test_password_reuse(self):
        """测试密码重用检测"""
        current = "OldPwd1234!"
        new = "OldPwd1234!"
        with pytest.raises(PasswordPolicyError, match="最近使用过的密码"):
            validate_password(new, previous_passwords=[current])

    def test_custom_min_length(self):
        """测试自定义最小长度"""
        with pytest.raises(PasswordPolicyError, match="至少为 12 个字符"):
            validate_password("Short1!@#", min_length=12)

    def test_optional_uppercase_disabled(self):
        """测试禁用大写字母要求"""
        assert validate_password(
            "mystr0ng!pass",
            require_uppercase=False,
        ) is True

    def test_optional_special_disabled(self):
        """测试禁用特殊字符要求"""
        assert validate_password(
            "MyStr0ngPass",
            require_special=False,
        ) is True

    def test_weak_password_check_disabled(self):
        """测试禁用弱密码检测"""
        assert validate_password(
            "Abcpassword1",
            check_common=False,
        ) is True


class TestCheckPasswordStrength:
    """密码强度检查测试"""

    def test_very_weak_password(self):
        """测试极弱密码"""
        result = check_password_strength("a")
        assert result["score"] <= 1
        assert result["level"] == "极弱"
        assert not result["is_strong"]

    def test_weak_password(self):
        """测试弱密码"""
        result = check_password_strength("abc")
        assert result["score"] == 1
        assert result["level"] == "弱"
        assert not result["is_strong"]

    def test_moderate_password(self):
        """测试一般密码"""
        result = check_password_strength("abcd1234")
        assert result["score"] == 2
        assert result["level"] == "一般"
        assert not result["is_strong"]

    def test_strong_password(self):
        """测试强密码"""
        result = check_password_strength("Abcd1234!")
        assert result["score"] == 4
        assert result["level"] == "很强"
        assert result["is_strong"]

    def test_very_strong_password(self):
        """测试极强密码"""
        result = check_password_strength("Abcd1234!@#$LongPass")
        assert result["score"] >= 5
        assert result["is_strong"]

    def test_max_score(self):
        """测试满分密码"""
        result = check_password_strength("Aa1!Abcdefghijklmnop")
        assert result["score"] == 7
        assert result["max_score"] == 7
        assert result["level"] == "极强"

    def test_issues_list(self):
        """测试问题列表"""
        result = check_password_strength("short")
        assert len(result["issues"]) > 0
        assert isinstance(result["issues"], list)

    def test_result_structure(self):
        """测试结果结构"""
        result = check_password_strength("Test123!")
        assert "score" in result
        assert "max_score" in result
        assert "level" in result
        assert "issues" in result
        assert "is_strong" in result


class TestJWTKeyManager:
    """JWT 密钥管理器测试"""

    class MockDBSession:
        """模拟数据库会话"""

        def __init__(self, initial_keys=None):
            self.keys = initial_keys or []
            self.committed = False
            self.closed = False

        def query(self, model):
            return MockQuery(self.keys)

        def add(self, obj):
            self.keys.append(obj)

        def commit(self):
            self.committed = True

        def close(self):
            self.closed = True

        def refresh(self, obj):
            pass

    class MockQuery:
        """模拟查询"""

        def __init__(self, data):
            self._data = data
            self._filters = []
            self._order_desc = False
            self._limit = None

        def filter(self, *conditions):
            self._filters.extend(conditions)
            return self

        def order_by(self, order):
            if hasattr(order, 'desc'):
                self._order_desc = True
            return self

        def limit(self, limit):
            self._limit = limit
            return self

        def first(self):
            data = self._data[:]
            if self._order_desc:
                data.sort(key=lambda x: getattr(x, 'version', 0), reverse=True)
            if self._limit:
                data = data[:self._limit]
            return data[0] if data else None

        def all(self):
            return self._data[:]

        def count(self):
            return len(self._data)

        def delete(self, synchronize_session=False):
            count = len(self._data)
            self._data.clear()
            return count

    @pytest.fixture
    def mock_db_factory(self):
        """创建模拟数据库工厂"""
        sessions = []

        def factory():
            session = self.MockDBSession()
            sessions.append(session)
            return session

        return factory, sessions

    def test_initial_key_creation(self, mock_db_factory):
        """测试初始密钥创建"""
        factory, sessions = mock_db_factory
        manager = JWTKeyManager(
            db_session_factory=factory,
            rotation_days=90,
            grace_period_days=7,
        )

        version, secret = manager.get_active_key()

        assert version == 1
        assert len(secret) == 64  # 32 bytes hex = 64 chars
        assert sessions[0].committed

    def test_key_rotation(self, mock_db_factory):
        """测试密钥轮换"""
        factory, sessions = mock_db_factory
        manager = JWTKeyManager(
            db_session_factory=factory,
            rotation_days=90,
            grace_period_days=7,
        )

        version1, secret1 = manager.get_active_key()
        assert version1 == 1

        old_key = sessions[0].keys[0]
        old_key.expires_at = datetime.now(timezone.utc) - timedelta(days=1)

        version2, secret2 = manager.get_active_key()
        assert version2 == 2
        assert secret1 != secret2

    def test_force_rotate(self, mock_db_factory):
        """测试强制轮换"""
        factory, sessions = mock_db_factory
        manager = JWTKeyManager(
            db_session_factory=factory,
            rotation_days=90,
            grace_period_days=7,
        )

        version1, _ = manager.get_active_key()
        version2, _ = manager.force_rotate()

        assert version2 == version1 + 1

    def test_force_rotate_empty_db(self, mock_db_factory):
        """测试空数据库时强制轮换"""
        factory, sessions = mock_db_factory
        manager = JWTKeyManager(
            db_session_factory=factory,
            rotation_days=90,
            grace_period_days=7,
        )

        version, secret = manager.force_rotate()
        assert version == 1
        assert len(secret) == 64

    def test_cleanup_expired_keys(self, mock_db_factory):
        """测试清理过期密钥"""
        factory, sessions = mock_db_factory

        old_key = JWTKey(
            version=1,
            secret="expired-secret",
            is_active=False,
            rotated_at=datetime.now(timezone.utc) - timedelta(days=120),
        )
        factory_instance = factory()
        factory_instance.keys.append(old_key)

        manager = JWTKeyManager(
            db_session_factory=factory,
            rotation_days=90,
            grace_period_days=7,
        )

        deleted = manager.cleanup_expired_keys()
        assert deleted == 1

    def test_get_key_stats(self, mock_db_factory):
        """测试获取密钥统计"""
        factory, sessions = mock_db_factory
        manager = JWTKeyManager(
            db_session_factory=factory,
            rotation_days=90,
            grace_period_days=7,
        )

        manager.get_active_key()
        stats = manager.get_key_stats()

        assert stats["total_keys"] == 1
        assert stats["active_keys"] == 1
        assert stats["current_version"] == 1
        assert stats["next_rotation"] is not None

    def test_cache_hit(self, mock_db_factory):
        """测试缓存命中"""
        factory, sessions = mock_db_factory
        manager = JWTKeyManager(
            db_session_factory=factory,
            rotation_days=90,
            grace_period_days=7,
        )

        version1, secret1 = manager.get_active_key()
        version2, secret2 = manager.get_active_key()

        assert version1 == version2
        assert secret1 == secret2
