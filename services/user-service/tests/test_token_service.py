"""Token服务测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestTokenManager:
    """Token管理器测试"""

    @pytest.mark.asyncio
    async def test_revoke_access_token(self):
        from app.services.token_service import TokenManager

        with patch('app.services.token_service.redis_service') as mock_redis:
            mock_redis.is_connected = True
            mock_redis.setex = AsyncMock(return_value=True)

            manager = TokenManager()
            result = await manager.revoke_access_token("test-jti-123", 3600)

            assert result is True
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_access_token_revoked(self):
        from app.services.token_service import TokenManager

        with patch('app.services.token_service.redis_service') as mock_redis:
            mock_redis.is_connected = True
            mock_redis.exists = AsyncMock(return_value=True)

            manager = TokenManager()
            result = await manager.is_access_token_revoked("test-jti-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_is_access_token_not_revoked(self):
        from app.services.token_service import TokenManager

        with patch('app.services.token_service.redis_service') as mock_redis:
            mock_redis.is_connected = True
            mock_redis.exists = AsyncMock(return_value=False)

            manager = TokenManager()
            result = await manager.is_access_token_revoked("test-jti-123")

            assert result is False

    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens(self):
        from app.services.token_service import TokenManager

        with patch('app.services.token_service.redis_service') as mock_redis:
            mock_redis.is_connected = True
            mock_redis.delete = AsyncMock(return_value=True)
            mock_redis.keys = AsyncMock(return_value=["token:blacklist:abc", "token:blacklist:def"])

            manager = TokenManager()
            result = await manager.revoke_all_user_tokens(123)

            assert result is True


class TestLoginRateLimiter:
    """登录频率限制测试"""

    @pytest.mark.asyncio
    async def test_is_not_locked_out(self):
        from app.services.token_service import LoginRateLimiter

        with patch('app.services.token_service.redis_service') as mock_redis:
            mock_redis.is_connected = True
            mock_redis.exists = AsyncMock(return_value=False)

            limiter = LoginRateLimiter()
            is_locked, remaining = await limiter.is_locked_out("13800138000")

            assert is_locked is False
            assert remaining == 0

    @pytest.mark.asyncio
    async def test_record_failed_attempt_first(self):
        from app.services.token_service import LoginRateLimiter

        with patch('app.services.token_service.redis_service') as mock_redis:
            mock_redis.is_connected = True
            mock_redis.incr = AsyncMock(return_value=1)
            mock_redis.expire = AsyncMock(return_value=True)
            mock_redis.exists = AsyncMock(return_value=False)

            limiter = LoginRateLimiter()
            attempts, lockout = await limiter.record_failed_attempt("13800138000")

            assert attempts == 1
            assert lockout == 0

    @pytest.mark.asyncio
    async def test_record_failed_attempt_lockout(self):
        from app.services.token_service import LoginRateLimiter

        with patch('app.services.token_service.redis_service') as mock_redis:
            mock_redis.is_connected = True
            mock_redis.incr = AsyncMock(return_value=5)
            mock_redis.expire = AsyncMock(return_value=True)
            mock_redis.setex = AsyncMock(return_value=True)

            limiter = LoginRateLimiter()
            attempts, lockout = await limiter.record_failed_attempt("13800138000")

            assert attempts == 5
            assert lockout > 0

    @pytest.mark.asyncio
    async def test_clear_failed_attempts(self):
        from app.services.token_service import LoginRateLimiter

        with patch('app.services.token_service.redis_service') as mock_redis:
            mock_redis.is_connected = True
            mock_redis.delete = AsyncMock(return_value=True)

            limiter = LoginRateLimiter()
            result = await limiter.clear_failed_attempts("13800138000")

            assert result is True


class TestJWTTokenGeneration:
    """JWT Token生成测试"""

    def test_access_token_contains_required_fields(self):
        from app.services.auth_service import AuthService
        from app.models import User
        from unittest.mock import MagicMock
        import uuid

        user = MagicMock(spec=User)
        user.id = 1
        user.role = "user"

        auth_service = AuthService(MagicMock())
        token, jti = auth_service._create_access_token(user)

        from jose import jwt
        from app.config.settings import get_settings
        settings = get_settings()

        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        assert payload["sub"] == "1"
        assert payload["role"] == "user"
        assert payload["type"] == "access"
        assert payload["jti"] == jti
        assert "exp" in payload
        assert "iat" in payload

    def test_refresh_token_contains_required_fields(self):
        from app.services.auth_service import AuthService
        from app.models import User
        from unittest.mock import MagicMock

        user = MagicMock(spec=User)
        user.id = 1
        user.role = "user"

        auth_service = AuthService(MagicMock())
        token, jti = auth_service._create_refresh_token(user)

        from jose import jwt
        from app.config.settings import get_settings
        settings = get_settings()

        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"
        assert payload["jti"] == jti
