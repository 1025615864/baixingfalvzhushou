"""Referral service (standalone module)."""
from __future__ import annotations
import time
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ReferralRecord:
    id: str
    referrer_id: int
    referee_id: int
    code: str
    status: str = "pending"
    reward: int = 0
    created_at: float = field(default_factory=time.time)


class ReferralService:
    def __init__(self):
        self._records: dict[str, ReferralRecord] = {}
        self._user_codes: dict[int, str] = {}
        self._next_id = 1

    def get_or_create_code(self, user_id: int) -> str:
        if user_id in self._user_codes:
            return self._user_codes[user_id]
        code = f"REF{user_id:06d}"
        self._user_codes[user_id] = code
        return code

    async def create_referral(self, referrer_id: int, referee_id: int) -> ReferralRecord:
        record_id = f"ref_{self._next_id}"
        self._next_id += 1
        code = self.get_or_create_code(referrer_id)
        record = ReferralRecord(id=record_id, referrer_id=referrer_id, referee_id=referee_id, code=code)
        self._records[record_id] = record
        return record

    async def get_referral(self, referral_id: str) -> Optional[ReferralRecord]:
        return self._records.get(referral_id)

    async def get_user_referrals(self, user_id: int) -> list[ReferralRecord]:
        return [r for r in self._records.values() if r.referrer_id == user_id]

    async def complete_referral(self, referral_id: str) -> dict:
        record = self._records.get(referral_id)
        if not record:
            return {"success": False, "error": "推荐记录不存在"}
        record.status = "completed"
        record.reward = 50
        return {"success": True, "referral_id": referral_id, "reward": record.reward}

    async def get_referral_stats(self, user_id: int) -> dict:
        user_records = [r for r in self._records.values() if r.referrer_id == user_id]
        total = len(user_records)
        completed = sum(1 for r in user_records if r.status == "completed")
        return {"total_referrals": total, "completed_referrals": completed, "total_reward": sum(r.reward for r in user_records)}


referral_service = ReferralService()
