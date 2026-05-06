"""邮箱验证服务"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import User
from ..services.redis_service import redis_service

logger = logging.getLogger(__name__)

EMAIL_VERIFY_PREFIX = "email_verify:"
EMAIL_VERIFY_EXPIRE_HOURS = 24


class EmailVerificationService:
    """邮箱验证服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_verification_token(self, user_id: int, email: str) -> Optional[str]:
        """创建邮箱验证令牌

        Args:
            user_id: 用户ID
            email: 邮箱地址

        Returns:
            验证令牌
        """
        token = secrets.token_urlsafe(32)
        token_key = f"{EMAIL_VERIFY_PREFIX}{token}"

        try:
            if redis_service.is_connected:
                data = f"{user_id}:{email}"
                await redis_service.setex(
                    token_key,
                    data,
                    EMAIL_VERIFY_EXPIRE_HOURS * 3600
                )
            logger.info(f"Email verification token created for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to create verification token: {e}")
            return None

    async def verify_token(self, token: str) -> tuple[bool, Optional[dict]]:
        """验证邮箱验证令牌

        Args:
            token: 验证令牌

        Returns:
            (success, user_info_dict)
        """
        token_key = f"{EMAIL_VERIFY_PREFIX}{token}"

        try:
            if redis_service.is_connected:
                data = await redis_service.get(token_key)
                if not data:
                    return False, None

                parts = data.split(":", 1)
                if len(parts) != 2:
                    return False, None

                user_id = int(parts[0])
                email = parts[1]

                result = await self.db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user or user.email != email:
                    return False, None

                user.email_verified = True
                user.email_verified_at = datetime.utcnow()
                await self.db.commit()

                await redis_service.delete(token_key)

                logger.info(f"Email verified for user {user_id}")
                return True, {"user_id": user_id, "email": email}

            return False, None
        except Exception as e:
            logger.error(f"Failed to verify token: {e}")
            return False, None

    async def resend_verification(self, email: str) -> tuple[bool, str]:
        """重新发送验证邮件

        Args:
            email: 邮箱地址

        Returns:
            (success, message)
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False, "如果该邮箱已注册，验证邮件已发送"

        if user.email_verified:
            return False, "该邮箱已验证"

        token = await self.create_verification_token(user.id, email)
        if not token:
            return False, "创建验证令牌失败"

        logger.info(f"Verification email resent to {email}")
        return True, "验证邮件已发送"

    async def is_email_verified(self, user_id: int) -> bool:
        """检查邮箱是否已验证"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False

        return user.email_verified


email_verification_service = EmailVerificationService
