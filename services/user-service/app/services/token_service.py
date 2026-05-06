"""Token 管理服务 - Token 黑名单和撤销"""
import logging
from typing import Optional
from datetime import datetime, timedelta

from ..services.redis_service import redis_service
from ..config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

TOKEN_BLACKLIST_PREFIX = "token:blacklist:"
REFRESH_TOKEN_BLACKLIST_PREFIX = "refresh_token:blacklist:"
REFRESH_TOKEN_USED_PREFIX = "refresh_token:used:"
TOKEN_FAMILY_PREFIX = "token_family:"


class TokenManager:
    """Token 管理器 - 支持 Token 撤销"""

    def __init__(self):
        self.redis = redis_service

    def _blacklist_key(self, jti: str) -> str:
        return f"{TOKEN_BLACKLIST_PREFIX}{jti}"

    def _refresh_blacklist_key(self, jti: str) -> str:
        return f"{REFRESH_TOKEN_BLACKLIST_PREFIX}{jti}"

    def _refresh_used_key(self, jti: str) -> str:
        return f"{REFRESH_TOKEN_USED_PREFIX}{jti}"

    def _token_family_key(self, family: str) -> str:
        return f"{TOKEN_FAMILY_PREFIX}{family}"

    async def revoke_access_token(self, jti: str, expires_in_seconds: int) -> bool:
        """将访问 token 加入黑名单

        Args:
            jti: Token 的唯一标识
            expires_in_seconds: Token 剩余有效期

        Returns:
            是否成功加入黑名单
        """
        if not self.redis.is_connected:
            logger.warning("Redis not connected, cannot revoke token")
            return False

        key = self._blacklist_key(jti)
        try:
            await self.redis.set(key, "revoked", expire_seconds=expires_in_seconds)
            logger.info(f"Access token revoked: {jti}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke access token: {e}")
            return False

    async def revoke_refresh_token(self, jti: str, expires_in_seconds: int) -> bool:
        """将刷新 token 加入黑名单"""
        if not self.redis.is_connected:
            return False

        key = self._refresh_blacklist_key(jti)
        try:
            await self.redis.set(key, "revoked", expire_seconds=expires_in_seconds)
            logger.info(f"Refresh token revoked: {jti}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke refresh token: {e}")
            return False

    async def is_access_token_revoked(self, jti: str) -> bool:
        """检查访问 token 是否已被撤销"""
        if not self.redis.is_connected:
            return False

        key = self._blacklist_key(jti)
        return await self.redis.exists(key)

    async def is_refresh_token_revoked(self, jti: str) -> bool:
        """检查刷新 token 是否已被撤销"""
        if not self.redis.is_connected:
            return False

        key = self._refresh_blacklist_key(jti)
        return await self.redis.exists(key)

    async def is_refresh_token_used(self, jti: str) -> bool:
        """检查刷新 token 是否已被使用过（用于重放攻击检测）"""
        if not self.redis.is_connected:
            return False

        key = self._refresh_used_key(jti)
        return await self.redis.exists(key)

    async def mark_refresh_token_used(self, jti: str) -> bool:
        """标记刷新 token 已被使用"""
        if not self.redis.is_connected:
            return False

        key = self._refresh_used_key(jti)
        try:
            await self.redis.set(key, "used", expire_seconds=settings.refresh_token_expire_days * 24 * 3600)
            return True
        except Exception as e:
            logger.error(f"Failed to mark refresh token as used: {e}")
            return False

    async def revoke_token_family(self, family: str) -> bool:
        """吊销整个 Token 家族"""
        if not self.redis.is_connected:
            logger.warning("Redis not connected, cannot revoke token family")
            return False

        key = self._token_family_key(family)
        try:
            await self.redis.set(key, "revoked", expire_seconds=settings.refresh_token_expire_days * 24 * 3600)
            logger.warning(f"Token family revoked: {family}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token family: {e}")
            return False

    async def revoke_all_user_tokens(self, user_id: int, refresh_token_jti: Optional[str] = None) -> bool:
        """撤销用户的所有 token（用于密码修改等场景）"""
        if not self.redis.is_connected:
            return False

        prefix = f"user_tokens:{user_id}:"
        try:
            if refresh_token_jti:
                await self.revoke_refresh_token(refresh_token_jti, settings.refresh_token_expire_days * 24 * 3600)
            logger.info(f"All tokens revoked for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke all user tokens: {e}")
            return False


class LoginRateLimiter:
    """登录频率限制器"""

    def __init__(self):
        self.redis = redis_service
        self.window_seconds = 300
        self.max_attempts = 5
        self.lockout_seconds = 900

    def _attempt_key(self, identifier: str) -> str:
        return f"login_attempt:{identifier}"

    def _lockout_key(self, identifier: str) -> str:
        return f"login_lockout:{identifier}"

    async def is_locked_out(self, identifier: str) -> tuple[bool, int]:
        """检查是否被锁定

        Returns:
            (is_locked, remaining_seconds)
        """
        if not self.redis.is_connected:
            return False, 0

        key = self._lockout_key(identifier)
        ttl = await self.redis.ttl(key)

        if ttl > 0:
            return True, ttl
        return False, 0

    async def record_failed_attempt(self, identifier: str) -> tuple[int, int]:
        """记录失败登录尝试

        Returns:
            (attempts_count, lockout_remaining_seconds)
        """
        if not self.redis.is_connected:
            return 0, 0

        attempt_key = self._attempt_key(identifier)
        lockout_key = self._lockout_key(identifier)

        try:
            attempts = await self.redis.incr(attempt_key)
            if attempts == 1:
                await self.redis.expire(attempt_key, self.window_seconds)

            if attempts >= self.max_attempts:
                await self.redis.set(lockout_key, "locked", expire_seconds=self.lockout_seconds)
                await self.redis.delete(attempt_key)
                return attempts, self.lockout_seconds

            remaining = self.max_attempts - attempts
            return attempts, 0
        except Exception as e:
            logger.error(f"Failed to record failed attempt: {e}")
            return 0, 0

    async def clear_failed_attempts(self, identifier: str) -> bool:
        """清除失败登录尝试记录（登录成功时调用）"""
        if not self.redis.is_connected:
            return True

        attempt_key = self._attempt_key(identifier)
        lockout_key = self._lockout_key(identifier)

        try:
            await self.redis.delete(attempt_key)
            await self.redis.delete(lockout_key)
            return True
        except Exception as e:
            logger.error(f"Failed to clear failed attempts: {e}")
            return False


token_manager = TokenManager()
login_rate_limiter = LoginRateLimiter()
