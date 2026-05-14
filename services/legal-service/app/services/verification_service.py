"""认证增强服务 - 年检提醒与自动降权"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models.lawyer import Lawyer
from ..models.verification import LawyerVerification

logger = logging.getLogger(__name__)


class VerificationService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_annual_inspection(self, lawyer_id: int) -> dict:
        """检查律师执业证年检状态"""
        result = await self.db.execute(
            select(LawyerVerification).where(
                LawyerVerification.lawyer_id == lawyer_id,
                LawyerVerification.status == "approved",
            ).order_by(LawyerVerification.verified_at.desc())
        )
        verification = result.scalars().first()

        if not verification or not verification.expires_at:
            return {"status": "ok", "days_until_expiry": None, "needs_reminder": False}

        days_left = (verification.expires_at - datetime.utcnow()).days

        needs_reminder = days_left <= 30

        return {
            "status": "expired" if days_left <= 0 else "ok",
            "days_until_expiry": days_left,
            "needs_reminder": needs_reminder,
            "expires_at": verification.expires_at.isoformat() if verification.expires_at else None,
        }

    async def run_annual_check_batch(self) -> dict:
        """批量运行年检检查（由定时任务调用）"""
        now = datetime.utcnow()
        thirty_days = now + timedelta(days=30)
        seven_days = now + timedelta(days=7)
        one_day = now + timedelta(days=1)

        result = await self.db.execute(
            select(LawyerVerification).where(
                and_(
                    LawyerVerification.status == "approved",
                    LawyerVerification.expires_at.isnot(None),
                )
            )
        )
        verifications = result.scalars().all()

        expired_count = 0
        reminder_30 = 0
        reminder_7 = 0
        reminder_1 = 0

        for v in verifications:
            if v.expires_at <= now:
                # 自动降权
                v.status = "expired"
                expired_count += 1

                lawyer = await self.db.get(Lawyer, v.lawyer_id)
                if lawyer and lawyer.is_verified:
                    lawyer.is_verified = False
            elif v.expires_at <= one_day:
                reminder_1 += 1
            elif v.expires_at <= seven_days:
                reminder_7 += 1
            elif v.expires_at <= thirty_days:
                reminder_30 += 1

        await self.db.commit()

        total_reminders = reminder_30 + reminder_7 + reminder_1

        logger.info(f"年检检查完成: {expired_count} 已过期降权, {total_reminders} 需提醒")

        return {
            "expired_downgraded": expired_count,
            "reminder_30_days": reminder_30,
            "reminder_7_days": reminder_7,
            "reminder_1_day": reminder_1,
            "total_reminders": total_reminders,
        }