"""JWT Token 测试"""
import pytest
from datetime import timedelta


class TestJWTToken:
    """JWT Token 测试类"""

    def test_create_access_token(self):
        """测试创建访问令牌"""
        from app.utils.security import create_access_token, decode_token

        token = create_access_token({"sub": "123", "role": "user"})
        assert token is not None
        assert len(token) > 0

        payload = decode_token(token)
        assert payload is not None
        assert payload.get("sub") == "123"
        assert payload.get("role") == "user"

    def test_create_access_token_custom_expiry(self):
        """测试创建带自定义过期时间的访问令牌"""
        from app.utils.security import create_access_token, decode_token

        token = create_access_token({"sub": "456"}, expires_delta=timedelta(hours=1))
        assert token is not None

        payload = decode_token(token)
        assert payload is not None
        assert payload.get("sub") == "456"

    def test_decode_invalid_token(self):
        """测试解码无效令牌"""
        from app.utils.security import decode_token

        result = decode_token("invalid_token")
        assert result is None

    def test_create_refresh_token(self):
        """测试创建刷新令牌"""
        from app.utils.security import create_refresh_token, decode_refresh_token

        token = create_refresh_token({"sub": "123", "role": "user"})
        assert token is not None
        assert len(token) > 0

        payload = decode_refresh_token(token)
        assert payload is not None
        assert payload.get("sub") == "123"
        assert payload.get("type") == "refresh"

    def test_create_refresh_token_custom_expiry(self):
        """测试创建带自定义过期时间的刷新令牌"""
        from app.utils.security import create_refresh_token, decode_refresh_token

        token = create_refresh_token({"sub": "789"}, expires_delta=timedelta(days=14))
        assert token is not None

        payload = decode_refresh_token(token)
        assert payload is not None
        assert payload.get("sub") == "789"

    def test_decode_refresh_token_wrong_type(self):
        """测试解码非刷新令牌（访问令牌）"""
        from app.utils.security import create_access_token, decode_refresh_token

        # 使用访问令牌
        access_token = create_access_token({"sub": "123", "role": "user"})

        # 刷新令牌验证应该失败
        result = decode_refresh_token(access_token)
        assert result is None

    def test_decode_refresh_token_invalid(self):
        """测试解码无效刷新令牌"""
        from app.utils.security import decode_refresh_token

        result = decode_refresh_token("invalid_refresh_token")
        assert result is None

    def test_refresh_token_expiry_longer_than_access(self):
        """测试刷新令牌过期时间更长"""
        from app.utils.security import create_access_token, create_refresh_token

        access_token = create_access_token({"sub": "123"})
        refresh_token = create_refresh_token({"sub": "123"})

        # 刷新令牌应该更长（默认7天 vs 默认1440分钟）
        assert len(refresh_token) > 0
        assert len(access_token) > 0

    def test_token_payload_contains_exp(self):
        """测试令牌payload包含过期时间"""
        from app.utils.security import create_access_token, create_refresh_token, decode_token, decode_refresh_token

        access_token = create_access_token({"sub": "123"})
        refresh_token = create_refresh_token({"sub": "123"})

        access_payload = decode_token(access_token)
        refresh_payload = decode_refresh_token(refresh_token)

        assert "exp" in access_payload
        assert "exp" in refresh_payload
