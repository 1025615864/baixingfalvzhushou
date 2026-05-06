"""账号注销服务 - 冷静期机制"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import User, AccountStatus
from ..services.redis_service import redis_service
from ..services.token_service import token_manager
from .audit_service import AuditService

logger = logging.getLogger(__name__)

DELETION_GRACE_PERIOD_DAYS = 7
DELETION_CANCEL_KEY_PREFIX = "account_deletion:"


class AccountDeletionService:
    """账号注销服务 - 支持冷静期"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def request_deletion(
        self,
        user_id: int,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> tuple[bool, str]:
        """请求账号注销（进入冷静期）

        Args:
            user_id: 用户ID
            reason: 注销原因
            ip_address: IP地址

        Returns:
            (success, message)
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False, "用户不存在"

        if user.status == AccountStatus.DELETION_PENDING:
            return False, "账号已在注销冷静期内"

        if user.status == AccountStatus.DELETED:
            return False, "账号已注销"

        grace_end = datetime.utcnow() + timedelta(days=DELETION_GRACE_PERIOD_DAYS)
        user.status = AccountStatus.DELETION_PENDING
        user.deletion_requested_at = datetime.utcnow()
        await self.db.commit()

        try:
            cancel_key = f"{DELETION_CANCEL_KEY_PREFIX}{user_id}"
            if redis_service.is_connected:
                await redis_service.setex(
                    cancel_key,
                    str(grace_end.timestamp()),
                    DELETION_GRACE_PERIOD_DAYS * 24 * 3600
                )
        except Exception as e:
            logger.warning(f"Failed to set deletion cancel key: {e}")

        audit_service = AuditService(self.db)
        await audit_service.log(
            action="deletion_requested",
            user_id=user_id,
            ip_address=ip_address,
            details={"reason": reason, "grace_end": grace_end.isoformat()},
        )

        logger.info(f"User {user_id} requested account deletion, grace period ends at {grace_end}")
        return True, f"注销请求已提交，{DELETION_GRACE_PERIOD_DAYS}天内可取消"

    async def cancel_deletion(self, user_id: int, ip_address: Optional[str] = None) -> tuple[bool, str]:
        """取消账号注销

        Args:
            user_id: 用户ID
            ip_address: IP地址

        Returns:
            (success, message)
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False, "用户不存在"

        if user.status != AccountStatus.DELETION_PENDING:
            return False, "账号不在注销冷静期"

        user.status = AccountStatus.ACTIVE
        user.deletion_requested_at = None
        await self.db.commit()

        try:
            cancel_key = f"{DELETION_CANCEL_KEY_PREFIX}{user_id}"
            if redis_service.is_connected:
                await redis_service.delete(cancel_key)
        except Exception as e:
            logger.warning(f"Failed to delete cancellation key: {e}")

        audit_service = AuditService(self.db)
        await audit_service.log(
            action="deletion_cancelled",
            user_id=user_id,
            ip_address=ip_address,
        )

        logger.info(f"User {user_id} cancelled account deletion")
        return True, "注销请求已取消，账号已恢复"

    async def confirm_deletion(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
    ) -> tuple[bool, str]:
        """确认立即注销（跳过冷静期）

        Args:
            user_id: 用户ID
            ip_address: IP地址

        Returns:
            (success, message)
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False, "用户不存在"

        await self._perform_deletion(user, ip_address)
        return True, "账号已永久注销"

    async def process_expired_deletions(self) -> dict:
        """处理过冷静期的注销（定时任务调用）

        Returns:
            处理结果 {"count": 处理数量, "deleted_user_ids": 已删除用户ID列表}
        """
        result = await self.db.execute(
            select(User).where(User.status == AccountStatus.DELETION_PENDING)
        )
        pending_users = result.scalars().all()

        count = 0
        deleted_ids = []
        for user in pending_users:
            if user.deletion_requested_at:
                grace_end = user.deletion_requested_at + timedelta(days=DELETION_GRACE_PERIOD_DAYS)
                if datetime.utcnow() >= grace_end:
                    user_id = user.id
                    await self._perform_deletion(user)
                    count += 1
                    deleted_ids.append(user_id)

        return {"count": count, "deleted_user_ids": deleted_ids}

    async def _perform_deletion(self, user: User, ip_address: Optional[str] = None):
        """执行账号注销"""
        user.status = AccountStatus.DELETED
        user.deleted_at = datetime.utcnow()
        user.is_active = False
        user.hashed_password = "[DELETED]"
        user.phone = None
        user.email = None
        await self.db.commit()

        await token_manager.revoke_all_user_tokens(user.id)

        audit_service = AuditService(self.db)
        await audit_service.log(
            action="deletion_completed",
            user_id=user.id,
            ip_address=ip_address,
        )

        try:
            from ..events.kafka_producer import publish_account_deleted
            await publish_account_deleted(
                user_id=str(user.id),
                deleted_by=str(user.id),
            )
        except Exception as e:
            logger.warning(f"Failed to publish deletion event: {e}")

        logger.info(f"User {user.id} account permanently deleted")

    async def get_deletion_status(self, user_id: int) -> Optional[dict]:
        """获取注销状态"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        if user.status != AccountStatus.DELETION_PENDING:
            return {"status": user.status, "in_grace_period": False}

        grace_end = None
        if user.deletion_requested_at:
            grace_end = user.deletion_requested_at + timedelta(days=DELETION_GRACE_PERIOD_DAYS)

        remaining_days = 0
        if grace_end:
            remaining = grace_end - datetime.utcnow()
            remaining_days = max(0, remaining.days)

        return {
            "status": user.status,
            "in_grace_period": True,
            "requested_at": user.deletion_requested_at.isoformat() if user.deletion_requested_at else None,
            "grace_end_at": grace_end.isoformat() if grace_end else None,
            "remaining_days": remaining_days,
        }


account_deletion_service = AccountDeletionService
