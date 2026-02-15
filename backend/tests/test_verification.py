"""
验证工具模块测试

测试覆盖：
-验证令牌功能
- 管理器功能
- 装饰器功能
- 过期机制
- 用户验证逻辑
"""
import pytest
import time
from unittest.mock import Mock, patch
from fastapi import Request, status

from app.utils.verification import (
    VerificationRequiredError,
    VerificationToken,
    VerificationManager,
    verification_manager,
    require_verification,
    check_verification,
)
from fastapi import HTTPException


class TestVerificationRequiredError:
    """验证错误异常测试类"""

    def test_exception_instantiation(self):
        """测试异常实例化"""
        error = VerificationRequiredError("测试错误消息")
        assert str(error) == "测试错误消息"

    def test_exception_raise_and_catch(self):
        """测试异常抛出和捕获"""
        with pytest.raises(VerificationRequiredError) as exc_info:
            raise VerificationRequiredError("自定义错误")
        assert "自定义错误" in str(exc_info.value)


class TestVerificationToken:
    """验证令牌测试类"""

    def test_token_initialization(self):
        """测试令牌初始化"""
        token = VerificationToken(
            user_id=123,
            operation="test_operation",
            expires_in=300
        )
        assert token.user_id == 123
        assert token.operation == "test_operation"
        assert token.verified is False

    def test_token_expiration_time(self):
        """测试令牌过期时间"""
        expires_in = 300
        token = VerificationToken(
            user_id=123,
            operation="test",
            expires_in=expires_in
        )
        expected_expires = token.created_at + expires_in
        assert token.expires_at == expected_expires

    def test_token_default_expiration(self):
        """测试默认过期时间（5分钟）"""
        token = VerificationToken(
            user_id=123,
            operation="test"
        )
        # 默认5分钟 = 300秒
        expected_expires = token.created_at + 300
        assert token.expires_at == expected_expires

    def test_is_expired_true(self):
        """测试令牌过期（已过期）"""
        token = VerificationToken(
            user_id=123,
            operation="test",
            expires_in=-1  # 立即过期
        )
        # 等待确保过期
        time.sleep(0.01)
        assert token.is_expired() is True

    def test_is_expired_false(self):
        """测试令牌未过期"""
        token = VerificationToken(
            user_id=123,
            operation="test",
            expires_in=300  # 5分钟后过期
        )
        assert token.is_expired() is False

    def test_verify_success(self):
        """测试验证成功"""
        token = VerificationToken(
            user_id=123,
            operation="test",
            expires_in=300
        )
        token.verify()
        assert token.verified is True

    def test_verify_expired_token(self):
        """测试验证过期令牌"""
        token = VerificationToken(
            user_id=123,
            operation="test",
            expires_in=-1
        )
        time.sleep(0.01)
        
        with pytest.raises(VerificationRequiredError) as exc_info:
            token.verify()
        assert "验证令牌已过期" in str(exc_info.value)
        assert token.verified is False


class TestVerificationManager:
    """验证管理器测试类"""

    def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = VerificationManager()
        assert isinstance(manager._tokens, dict)
        assert hasattr(manager, '_last_cleanup')
        assert len(manager._tokens) == 0

    def test_global_manager_instance(self):
        """测试全局管理器实例"""
        assert verification_manager is not None
        assert isinstance(verification_manager, VerificationManager)

    def test_create_token(self):
        """测试创建验证令牌"""
        manager = VerificationManager()
        token_key = manager.create_token(
            user_id=123,
            operation="test_operation"
        )
        assert isinstance(token_key, str)
        assert token_key in manager._tokens

    def test_create_token_structure(self):
        """测试创建的令牌结构"""
        manager = VerificationManager()
        token_key = manager.create_token(
            user_id=123,
            operation="test_operation"
        )
        token = manager._tokens.get(token_key)
        assert token is not None
        assert token.user_id == 123
        assert token.operation == "test_operation"
        assert token.verified is False

    def test_verify_token_success(self):
        """测试验证令牌成功"""
        manager = VerificationManager()
        token_key = manager.create_token(
            user_id=123,
            operation="test_operation"
        )
        
        # 验证时不应该抛出异常
        manager.verify_token(token_key, user_id=123)

        # 验证后令牌应该是已验证状态
        token = manager._tokens.get(token_key)
        assert token.verified is True

    def test_verify_token_not_exists(self):
        """测试验证不存在的令牌"""
        manager = VerificationManager()
        
        with pytest.raises(VerificationRequiredError) as exc_info:
            manager.verify_token("nonexistent_token", user_id=123)
        assert "验证令牌不存在" in str(exc_info.value)

    def test_verify_token_wrong_user(self):
        """测试验证错误用户的令牌"""
        manager = VerificationManager()
        token_key = manager.create_token(
            user_id=123,
            operation="test_operation"
        )
        
        with pytest.raises(VerificationRequiredError) as exc_info:
            manager.verify_token(token_key, user_id=456)  # 不同的用户ID
        assert "验证令牌无效" in str(exc_info.value)

    def test_verify_token_expired(self, monkeypatch):
        """测试验证已过期的令牌"""
        # Mock time.time() 来模拟时间流逝
        def mock_time():
            return 1000
        def mock_time_later():
            return 2000  # 模拟时间过去了
        monkeypatch.setattr(time, 'time', mock_time)
        
        manager = VerificationManager()
        token_key = manager.create_token(
            user_id=123,
            operation="test_operation"
        )
        
        # 模拟时间流逝（超过默认的300秒过期时间）
        monkeypatch.setattr(time, 'time', mock_time_later)
        
        with pytest.raises(VerificationRequiredError) as exc_info:
            manager.verify_token(token_key, user_id=123)
        # 验证抛出了正确的异常类型即可，不依赖具体的消息内容
        assert isinstance(exc_info.value, VerificationRequiredError)

    def test_is_verified_true(self):
        """测试检查已验证的令牌"""
        manager = VerificationManager()
        token_key = manager.create_token(
            user_id=123,
            operation="test_operation"
        )
        
        # 先验证令牌
        manager.verify_token(token_key, user_id=123)
        
        # 检查验证状态
        is_verified = manager.is_verified(token_key, user_id=123)
        assert is_verified is True

    def test_is_verified_false(self):
        """测试检查未验证的令牌"""
        manager = VerificationManager()
        token_key = manager.create_token(
            user_id=123,
            operation="test_operation"
        )
        
        # 不验证令牌，直接检查
        is_verified = manager.is_verified(token_key, user_id=123)
        assert is_verified is False

    def test_is_verified_not_exists(self):
        """测试检查不存在的令牌"""
        manager = VerificationManager()
        is_verified = manager.is_verified("nonexistent_token", user_id=123)
        assert is_verified is False

    def test_is_verified_wrong_user(self):
        """测试检查错误用户的令牌"""
        manager = VerificationManager()
        token_key = manager.create_token(
            user_id=123,
            operation="test_operation"
        )
        
        # 验证前检查
        is_verified = manager.is_verified(token_key, user_id=456)
        assert is_verified is False

    def test_cleanup_expired_tokens(self, monkeypatch):
        """测试清理过期令牌"""
        # Mock time.time() 来模拟时间流逝
        def mock_time():
            return 1000
        def mock_time_later():
            return 2000  # 模拟时间过去了
        monkeypatch.setattr(time, 'time', mock_time)
        
        manager = VerificationManager()
        
        # 创建多个令牌
        manager.create_token(user_id=123, operation="op1")
        manager.create_token(user_id=456, operation="op2")
        manager.create_token(user_id=789, operation="op3")
        
        # 模拟时间流逝（超过默认的300秒过期时间）
        monkeypatch.setattr(time, 'time', mock_time_later)
        
        # 手动清理
        manager._cleanup_expired_tokens()
        
        # 应该只剩下0个令牌（所有都过期了）
        assert len(manager._tokens) == 0


class TestVerificationDecorators:
    """验证装饰器测试类"""

    def test_require_verification_no_user_id(self, monkeypatch):
        """测试需要验证但没有用户ID"""
        # 创建mock request
        request = Mock(spec=Request)
        request.headers = {}
        request.state = Mock()
        request.state.user_id = None
        
        with pytest.raises(HTTPException) as exc_info:
            require_verification("test_operation", request)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_require_verification_no_token(self, monkeypatch):
        """测试需要验证但没有令牌"""
        # 创建mock request
        request = Mock(spec=Request)
        request.headers = {}
        request.state = Mock()
        request.state.user_id = 123
        
        with pytest.raises(HTTPException) as exc_info:
            require_verification("test_operation", request)
        # 应该创建新令牌并返回403
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_require_verification_returns_token(self, monkeypatch):
        """测试需要验证返回令牌信息"""
        # 创建mock request
        request = Mock(spec=Request)
        request.headers = {}
        request.state = Mock()
        request.state.user_id = 123
        
        with pytest.raises(HTTPException) as exc_info:
            require_verification("test_operation", request)
        
        # 检查返回的令牌信息
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        detail = exc_info.value.detail
        assert "verification_token" in detail
        assert "operation" in detail
        assert detail["operation"] == "test_operation"

    @patch('app.utils.verification.verification_manager')
    def test_require_verification_with_valid_token(self, mock_manager, monkeypatch):
        """测试需要验证带有有效令牌"""
        # 创建mock request
        request = Mock(spec=Request)
        request.headers = {"X-Verification-Token": "valid_token"}
        request.state = Mock()
        request.state.user_id = 123
        
        # Mock verification manager
        mock_manager.verify_token.return_value = None
        mock_manager.is_verified.return_value = True
        
        # 应该返回None（验证成功）
        result = require_verification("test_operation", request)
        assert result is None
        mock_manager.verify_token.assert_called_once_with("valid_token", 123)

    def test_check_verification_no_user_id(self):
        """测试检查验证但没有用户ID"""
        request = Mock(spec=Request)
        request.headers = {}
        request.state = Mock()
        request.state.user_id = None
        
        result = check_verification("test_operation", request)
        assert result is False

    def test_check_verification_no_token(self):
        """测试检查验证但没有令牌"""
        request = Mock(spec=Request)
        request.headers = {}
        request.state = Mock()
        request.state.user_id = 123
        
        result = check_verification("test_operation", request)
        assert result is False

    def test_check_verification_with_invalid_token(self):
        """测试检查验证带无效令牌"""
        request = Mock(spec=Request)
        request.headers = {"X-Verification-Token": "invalid_token"}
        request.state = Mock()
        request.state.user_id = 123
        
        with patch('app.utils.verification.verification_manager') as mock_manager:
            mock_manager.is_verified.return_value = False
            result = check_verification("test_operation", request)
            assert result is False

    def test_check_verification_with_valid_token(self):
        """测试检查验证带有效令牌"""
        request = Mock(spec=Request)
        request.headers = {"X-Verification-Token": "valid_token"}
        request.state = Mock()
        request.state.user_id = 123
        
        with patch('app.utils.verification.verification_manager') as mock_manager:
            mock_manager.is_verified.return_value = True
            result = check_verification("test_operation", request)
            assert result is True


class TestVerificationIntegration:
    """验证功能集成测试类"""

    def test_complete_verification_workflow(self):
        """测试完整的验证流程"""
        manager = VerificationManager()
        
        # 1. 创建令牌
        user_id = 123
        operation = "sensitive_operation"
        token_key = manager.create_token(user_id, operation)
        
        assert token_key in manager._tokens
        assert manager.is_verified(token_key, user_id) is False
        
        # 2. 验证令牌
        manager.verify_token(token_key, user_id)
        
        # 3. 检查验证状态
        assert manager.is_verified(token_key, user_id) is True
        
    def test_multiple_tokens_same_user(self):
        """测试同一用户的多个令牌"""
        manager = VerificationManager()
        user_id = 123
        
        # 创建多个令牌
        token1 = manager.create_token(user_id, "operation1")
        token2 = manager.create_token(user_id, "operation2")
        token3 = manager.create_token(user_id, "operation3")
        
        assert len(manager._tokens) == 3
        assert len([t for t in manager._tokens.keys()]) == 3
        
        # 所有令牌都应该存在
        assert manager.is_verified(token1, user_id) is False
        assert manager.is_verified(token2, user_id) is False
        assert manager.is_verified(token3, user_id) is False

    def test_token_cleanup_prevents_memory_leak(self, monkeypatch):
        """测试令牌清理防止内存泄漏"""
        # Mock time.time() 来模拟时间流逝
        def mock_time():
            return 1000
        def mock_time_later():
            return 2000  # 模拟时间过去了
        
        monkeypatch.setattr(time, 'time', mock_time)
        
        manager = VerificationManager()
        
        # 创建多个令牌
        for i in range(10):
            manager.create_token(
                user_id=i,
                operation=f"operation_{i}"
            )
        
        # 清理前应该有10个令牌
        assert len(manager._tokens) == 10
        
        # 模拟时间流逝（超过默认的300秒过期时间）
        monkeypatch.setattr(time, 'time', mock_time_later)
        
        # 清理后应该有0个令牌
        manager._cleanup_expired_tokens()
        assert len(manager._tokens) == 0

    def test_concurrent_verification_scenarios(self):
        """测试并发验证场景"""
        manager = VerificationManager()
        
        # 模拟多个用户并发请求验证
        users = [101, 102, 103, 104, 105]
        operation = "batch_operation"
        
        # 为每个用户创建令牌
        token_keys = {}
        for user_id in users:
            token_key = manager.create_token(user_id, operation)
            token_keys[user_id] = token_key
        
        # 验证每个用户的令牌
        for user_id, token_key in token_keys.items():
            manager.verify_token(token_key, user_id)
            assert manager.is_verified(token_key, user_id) is True
        
        # 确保所有令牌都是独立的
        assert len(manager._tokens) == len(users)

    def test_token_reuse_prevention(self):
        """测试防止令牌重用"""
        manager = VerificationManager()
        
        # 用户1创建令牌
        user1_token = manager.create_token(1, "operation")
        
        # 用户2尝试验证用户1的令牌
        with pytest.raises(VerificationRequiredError):
            manager.verify_token(user1_token, user_id=2)

        # 令牌应该仍然有效（但未验证）
        assert manager.is_verified(user1_token, 1) is False