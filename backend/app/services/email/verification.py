"""邮箱验证服务

提供邮箱验证令牌的生成、验证和失效功能
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone

from .storage import _email_verification_tokens as _email_verification_tokens_dict, EmailVerificationTokenData
from .password_reset import password_reset_service

logger = logging.getLogger(__name__)

# ============================================================================
# 常量定义
# ============================================================================

_EMAIL_VERIFY_TOKEN_PREFIX = "email_verify_token:"
_EMAIL_VERIFY_TOKEN_TTL_SECONDS = 60 * 60 * 24  # 24小时


# ============================================================================
# 邮箱验证服务类
# ============================================================================

class EmailVerificationService:
    """邮箱验证服务类"""

    async def generate_token(self, user_id: int, email: str) -> str:
        """生成邮箱验证令牌

        Args:
            user_id: 用户ID
            email: 邮箱地址

        Returns:
            生成的令牌
        """
        # 延迟导入以支持 monkeypatch 测试
        from ...services import email_service as es
        cache_service = es.cache_service

        token = secrets.token_urlsafe(32)
        # 使用 es.datetime 以支持测试中的 monkeypatch
        expires_at = es.datetime.now(
            timezone.utc) + timedelta(seconds=_EMAIL_VERIFY_TOKEN_TTL_SECONDS)

        token_data: EmailVerificationTokenData = {
            "user_id": int(user_id),
            "email": str(email),
            "expires_at": expires_at.isoformat(),
            "used": False,
        }

        cache_key = f"{_EMAIL_VERIFY_TOKEN_PREFIX}{token}"
        try:
            _ = await cache_service.set_json(cache_key, dict(token_data), expire=_EMAIL_VERIFY_TOKEN_TTL_SECONDS)
        except (ConnectionError, TimeoutError, RuntimeError) as e:
            logger.warning(
                f"Cache unavailable, falling back to memory storage: {e}")
            _email_verification_tokens_dict[token] = token_data
            # 同时清理密码重置令牌的无效条目
            self._cleanup_expired_tokens()
            password_reset_service._cleanup_expired_tokens()

        return token

    async def verify_token(
            self, token: str) -> EmailVerificationTokenData | None:
        """验证邮箱验证令牌

        Args:
            token: 待验证的令牌

        Returns:
            令牌数据（验证成功）或 None（验证失败）
        """
        # 延迟导入以支持 monkeypatch 测试
        from ...services import email_service as es
        cache_service = es.cache_service

        cache_key = f"{_EMAIL_VERIFY_TOKEN_PREFIX}{token}"
        try:
            token_data = await cache_service.get_json(cache_key)
            if isinstance(token_data, dict):
                used = token_data.get("used")
                if used:
                    return None
                user_id = token_data.get("user_id")
                email = token_data.get("email")
                expires_at = token_data.get("expires_at")
                if isinstance(user_id, int) and isinstance(
                        email, str) and isinstance(expires_at, str):
                    return {
                        "user_id": user_id,
                        "email": email,
                        "expires_at": expires_at,
                        "used": bool(used),
                    }
        except (ConnectionError, TimeoutError, RuntimeError) as e:
            logger.warning(f"Cache unavailable, checking memory storage: {e}")
        except Exception as e:
            logger.error(f"Unexpected error reading from cache: {e}")

        if token not in _email_verification_tokens_dict:
            return None

        token_data = _email_verification_tokens_dict[token]
        if token_data["used"]:
            return None

        try:
            expires_at_dt = datetime.fromisoformat(token_data["expires_at"])
        except ValueError:
            del _email_verification_tokens_dict[token]
            return None

        # 使用 es.datetime 以支持测试中的 monkeypatch
        if es.datetime.now(timezone.utc) > expires_at_dt:
            del _email_verification_tokens_dict[token]
            return None

        return token_data

    async def invalidate_token(self, token: str) -> None:
        """使邮箱验证令牌失效

        Args:
            token: 要失效的令牌
        """
        # 延迟导入以支持 monkeypatch 测试
        from ...services import email_service as es
        cache_service = es.cache_service

        cache_key = f"{_EMAIL_VERIFY_TOKEN_PREFIX}{token}"
        try:
            token_data = await cache_service.get_json(cache_key)
            if isinstance(token_data, dict):
                token_data["used"] = True
                _ = await cache_service.set_json(cache_key, token_data, expire=_EMAIL_VERIFY_TOKEN_TTL_SECONDS)
                return
        except (ConnectionError, TimeoutError, RuntimeError) as e:
            logger.warning(f"Cache unavailable, checking memory storage: {e}")
        except Exception as e:
            logger.error(f"Unexpected error invalidating token in cache: {e}")

        if token in _email_verification_tokens_dict:
            _email_verification_tokens_dict[token]["used"] = True

    def _cleanup_expired_tokens(self) -> None:
        """清理过期的邮箱验证令牌"""
        # 延迟导入以支持 monkeypatch 测试
        from ...services import email_service as es

        now = es.datetime.now(timezone.utc)
        expired: list[str] = []
        for token, data in list(_email_verification_tokens_dict.items()):
            try:
                expires_at_str = data.get("expires_at", "")
                # 尝试解析 datetime，处理 naive 和 aware 两种情况
                try:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    # 如果是 naive datetime，添加 timezone 信息
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    # 如果过期，添加到清理列表
                    if now > expires_at:
                        expired.append(token)
                except ValueError:
                    # 无法解析的 datetime 视为无效，添加到清理列表
                    expired.append(token)
            except (KeyError, TypeError):
                continue
        for token in expired:
            del _email_verification_tokens_dict[token]


# 单例实例
email_verification_service = EmailVerificationService()
