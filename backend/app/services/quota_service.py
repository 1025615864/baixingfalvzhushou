from __future__ import annotations

from datetime import date, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_quota import UserQuotaDaily, UserQuotaPackBalance

FREE_AI_CHAT_DAILY_LIMIT: int = 10
FREE_DOCUMENT_GENERATE_DAILY_LIMIT: int = 5


class QuotaService:
    async def get_daily(self, db: AsyncSession, user_id: int, day: date | None = None) -> UserQuotaDaily:
        if day is None:
            day = date.today()
        stmt = select(UserQuotaDaily).where(
            UserQuotaDaily.user_id == user_id,
            UserQuotaDaily.day == day,
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            row = UserQuotaDaily(user_id=user_id, day=day, ai_chat_count=0, document_generate_count=0)
            db.add(row)
            await db.commit()
            await db.refresh(row)
        return row

    async def get_pack_balance(self, db: AsyncSession, user_id: int) -> UserQuotaPackBalance:
        stmt = select(UserQuotaPackBalance).where(UserQuotaPackBalance.user_id == user_id)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            row = UserQuotaPackBalance(user_id=user_id, ai_chat_credits=0, document_generate_credits=0)
            db.add(row)
            await db.commit()
            await db.refresh(row)
        return row

    async def can_ai_chat(self, db: AsyncSession, user_id: int) -> bool:
        daily = await self.get_daily(db, user_id)
        if daily.ai_chat_count < FREE_AI_CHAT_DAILY_LIMIT:
            return True
        pack = await self.get_pack_balance(db, user_id)
        return pack.ai_chat_credits > 0

    async def consume_ai_chat(self, db: AsyncSession, user_id: int) -> bool:
        daily = await self.get_daily(db, user_id)
        if daily.ai_chat_count < FREE_AI_CHAT_DAILY_LIMIT:
            daily.ai_chat_count += 1
            await db.commit()
            return True
        pack = await self.get_pack_balance(db, user_id)
        if pack.ai_chat_credits > 0:
            pack.ai_chat_credits -= 1
            await db.commit()
            return True
        return False

    async def can_document_generate(self, db: AsyncSession, user_id: int) -> bool:
        daily = await self.get_daily(db, user_id)
        if daily.document_generate_count < FREE_DOCUMENT_GENERATE_DAILY_LIMIT:
            return True
        pack = await self.get_pack_balance(db, user_id)
        return pack.document_generate_credits > 0

    async def consume_document_generate(self, db: AsyncSession, user_id: int) -> bool:
        daily = await self.get_daily(db, user_id)
        if daily.document_generate_count < FREE_DOCUMENT_GENERATE_DAILY_LIMIT:
            daily.document_generate_count += 1
            await db.commit()
            return True
        pack = await self.get_pack_balance(db, user_id)
        if pack.document_generate_credits > 0:
            pack.document_generate_credits -= 1
            await db.commit()
            return True
        return False

    async def get_quota(self, db: AsyncSession, user_id: int) -> dict:
        daily = await self.get_daily(db, user_id)
        pack = await self.get_pack_balance(db, user_id)
        return {
            "ai_chat_remaining": max(0, FREE_AI_CHAT_DAILY_LIMIT - daily.ai_chat_count),
            "document_generate_remaining": max(0, FREE_DOCUMENT_GENERATE_DAILY_LIMIT - daily.document_generate_count),
            "ai_chat_pack_credits": pack.ai_chat_credits,
            "document_generate_pack_credits": pack.document_generate_credits,
        }

    async def restore_quota(self, db: AsyncSession, user_id: int, related_id: int, quota_type: str = "ai_chat", amount: int = 1) -> bool:
        pack = await self.get_pack_balance(db, user_id)
        if quota_type == "ai_chat":
            pack.ai_chat_credits += amount
        elif quota_type == "document_generate":
            pack.document_generate_credits += amount
        else:
            return False
        await db.commit()
        return True


quota_service = QuotaService()
