"""账号注销定时任务

用于处理冷静期结束后的自动注销
建议使用 APScheduler 或系统 cron 定期调用
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import AsyncSessionLocal
from ..models import User, AccountStatus
from ..services.account_deletion_service import AccountDeletionService

logger = logging.getLogger(__name__)


async def process_expired_deletions() -> dict:
    """处理过期的账号注销请求

    冷静期（7天）结束后自动执行永久注销

    Returns:
        {
            "processed": int,  # 处理的数量
            "deleted": list,   # 已删除的用户ID列表
            "errors": list,    # 错误信息列表
        }
    """
    result = {
        "processed": 0,
        "deleted": [],
        "errors": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Starting expired deletion processing...")

    try:
        async with AsyncSessionLocal() as db:
            service = AccountDeletionService(db)

            result_detail = await service.process_expired_deletions()
            result["processed"] = result_detail["count"]
            result["deleted"] = result_detail["deleted_user_ids"]
            result["ended_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(
                f"Expired deletion processing completed: "
                f"{result['processed']} users processed, "
                f"{len(result['deleted'])} deleted"
            )
    except Exception as e:
        logger.error(f"Expired deletion processing failed: {e}")
        result["errors"].append(str(e))
        result["ended_at"] = datetime.now(timezone.utc).isoformat()

    return result


async def get_pending_deletions() -> list[dict]:
    """获取待执行的注销请求列表

    Returns:
        待注销用户列表，包含冷静期剩余天数
    """
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.status == AccountStatus.DELETION_PENDING)
            )
            users = result.scalars().all()

            pending_list = []
            for user in users:
                if user.deletion_requested_at:
                    grace_end = user.deletion_requested_at + timedelta(days=7)
                    remaining = grace_end - datetime.now(timezone.utc)
                    pending_list.append({
                        "user_id": user.id,
                        "requested_at": user.deletion_requested_at.isoformat(),
                        "grace_end_at": grace_end.isoformat(),
                        "remaining_seconds": max(0, remaining.total_seconds()),
                    })

            return pending_list
    except Exception as e:
        logger.error(f"Failed to get pending deletions: {e}")
        return []


async def cleanup_deleted_users(days: int = 90) -> int:
    """清理已删除账号（物理删除）

    警告：这是不可逆操作！

    Args:
        days: 只清理 deleted_at 早于指定天数的账号

    Returns:
        清理的账号数量
    """
    try:
        async with AsyncSessionLocal() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            result = await db.execute(
                select(User).where(
                    User.status == AccountStatus.DELETED,
                    User.deleted_at < cutoff
                )
            )
            users_to_delete = result.scalars().all()

            count = 0
            for user in users_to_delete:
                await db.delete(user)
                count += 1

            await db.commit()
            logger.info(f"Cleaned up {count} deleted users older than {days} days")
            return count
    except Exception as e:
        logger.error(f"Failed to cleanup deleted users: {e}")
        return 0
