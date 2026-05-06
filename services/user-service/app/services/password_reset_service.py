"""密码重置服务"""
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import User
from ..services.redis_service import redis_service
from .password_policy import password_policy

logger = logging.getLogger(__name__)

RESET_TOKEN_PREFIX = "password_reset:"
RESET_TOKEN_EXPIRE_MINUTES = 30


class PasswordResetService:
    """密码重置服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reset_token(self, phone: str) -> Optional[str]:
        """创建密码重置令牌

        Args:
            phone: 用户手机号

        Returns:
            重置令牌，如果用户不存在则返回None
        """
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Password reset requested for non-existent phone: {phone}")
            return None

        token = secrets.token_urlsafe(32)
        token_key = f"{RESET_TOKEN_PREFIX}{token}"

        try:
            if redis_service.is_connected:
                await redis_service.setex(
                    token_key,
                    user.id,
                    RESET_TOKEN_EXPIRE_MINUTES * 60
                )
            logger.info(f"Password reset token created for user {user.id}")
            return token
        except Exception as e:
            logger.error(f"Failed to create reset token: {e}")
            return None

    async def verify_reset_token(self, token: str) -> Optional[int]:
        """验证密码重置令牌

        Args:
            token: 重置令牌

        Returns:
            用户ID，如果令牌无效则返回None
        """
        token_key = f"{RESET_TOKEN_PREFIX}{token}"

        try:
            if redis_service.is_connected:
                user_id = await redis_service.get(token_key)
                if user_id:
                    return int(user_id)
            return None
        except Exception as e:
            logger.error(f"Failed to verify reset token: {e}")
            return None

    async def reset_password(self, token: str, new_password: str) -> tuple[bool, str]:
        """使用令牌重置密码

        Args:
            token: 重置令牌
            new_password: 新密码

        Returns:
            (success, error_message)
        """
        is_valid, error_msg = password_policy.validate(new_password)
        if not is_valid:
            return False, error_msg

        user_id = await self.verify_reset_token(token)
        if not user_id:
            return False, "Invalid or expired reset token"

        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False, "User not found"

        from .auth_service import pwd_context
        user.hashed_password = pwd_context.hash(new_password)
        await self.db.commit()

        token_key = f"{RESET_TOKEN_PREFIX}{token}"
        try:
            if redis_service.is_connected:
                await redis_service.delete(token_key)
        except Exception as e:
            logger.warning(f"Failed to delete reset token: {e}")

        logger.info(f"Password reset completed for user {user_id}")
        return True, ""


password_reset_service = PasswordResetService
