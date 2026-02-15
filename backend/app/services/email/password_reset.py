"""密码重置服务

提供密码重置令牌的生成、验证和失效功能
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone

from .storage import _reset_tokens as _reset_tokens_dict, ResetTokenData

logger = logging.getLogger(__name__)

# ============================================================================
# 常量定义
# ============================================================================

_RESET_TOKEN_PREFIX = "password_reset_token:"
_RESET_TOKEN_TTL_SECONDS = 3600  # 1小时


# ============================================================================
# 密码重置服务类
# ============================================================================

class PasswordResetService:
    """密码重置服务类"""

    async def generate_reset_token(self, user_id: int, email: str) -> str:
        """生成密码重置令牌

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
        expires_at = es.datetime.now(timezone.utc) + timedelta(hours=1)

        token_data: ResetTokenData = {
            "user_id": user_id,
            "email": email,
            "expires_at": expires_at.isoformat(),
            "used": False,
        }

        cache_key = f"{_RESET_TOKEN_PREFIX}{token}"
        try:
            _ = await cache_service.set_json(cache_key, dict(token_data), expire=_RESET_TOKEN_TTL_SECONDS)
        except (ConnectionError, TimeoutError, RuntimeError) as e:
            logger.warning(
                f"Cache unavailable, falling back to memory storage: {e}")
            _reset_tokens_dict[token] = token_data
            self._cleanup_expired_tokens()

        return token

    async def verify_reset_token(self, token: str) -> ResetTokenData | None:
        """验证密码重置令牌

        Args:
            token: 待验证的令牌

        Returns:
            令牌数据（验证成功）或 None（验证失败）
        """
        # 延迟导入以支持 monkeypatch 测试
        from ...services import email_service as es
        cache_service = es.cache_service

        cache_key = f"{_RESET_TOKEN_PREFIX}{token}"
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

        if token not in _reset_tokens_dict:
            return None

        token_data = _reset_tokens_dict[token]

        if token_data["used"]:
            return None

        try:
            # datetime.fromisoformat 保持标准调用，因为它是类方法，通常不被 monkeypatch
            expires_at = datetime.fromisoformat(token_data["expires_at"])
        except ValueError:
            del _reset_tokens_dict[token]
            return None

        # 使用 es.datetime 以支持测试中的 monkeypatch
        if es.datetime.now(timezone.utc) > expires_at:
            del _reset_tokens_dict[token]
            return None

        return token_data

    async def invalidate_token(self, token: str) -> None:
        """使密码重置令牌失效

        Args:
            token: 要失效的令牌
        """
        # 延迟导入以支持 monkeypatch 测试
        from ...services import email_service as es
        cache_service = es.cache_service

        cache_key = f"{_RESET_TOKEN_PREFIX}{token}"
        try:
            token_data = await cache_service.get_json(cache_key)
            if isinstance(token_data, dict):
                token_data["used"] = True
                _ = await cache_service.set_json(cache_key, token_data, expire=_RESET_TOKEN_TTL_SECONDS)
                return
        except (ConnectionError, TimeoutError, RuntimeError) as e:
            logger.warning(f"Cache unavailable, checking memory storage: {e}")
        except Exception as e:
            logger.error(f"Unexpected error invalidating token in cache: {e}")

        if token in _reset_tokens_dict:
            _reset_tokens_dict[token]["used"] = True

    def _cleanup_expired_tokens(self) -> None:
        """清理过期的密码重置令牌"""
        # 延迟导入以支持 monkeypatch 测试
        from ...services import email_service as es
        
        now = es.datetime.now(timezone.utc)
        expired: list[str] = []
        for token, data in list(_reset_tokens_dict.items()):
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
            del _reset_tokens_dict[token]


# 单例实例
password_reset_service = PasswordResetService()
