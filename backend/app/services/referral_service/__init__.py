"""Referral service."""
from __future__ import annotations
import secrets
import time
from typing import Optional, Any
from dataclasses import dataclass, field


@dataclass
class ReferralCode:
    code: str
    user_id: int = 0
    created_at: float = field(default_factory=time.time)
    usage_count: int = 0
    max_uses: int = 100
    is_active: bool = True


@dataclass
class ReferralRecord:
    id: int
    referrer_id: int = 0
    referee_id: int = 0
    referral_code: str = ""
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    reward_points: int = 0


class ReferralService:
    def __init__(self):
        self._codes: dict[int, ReferralCode] = {}
        self._records: dict[int, ReferralRecord] = {}
        self._next_record_id = 1
        self._reward_points = 100
        self._referee_reward_points = 50
        self._invite_history: dict[int, list[dict]] = {}

    async def generate_invite_code(self, db, user_id: int) -> str:
        token = secrets.token_urlsafe(8)
        code = f"REF-{token.upper()[:8]}"
        self._codes[user_id] = ReferralCode(code=code, user_id=user_id)
        return code

    async def generate_referral_code(self, user_id: int) -> str:
        if user_id in self._codes:
            return self._codes[user_id].code
        token = secrets.token_urlsafe(8)
        code = f"REF-{token.upper()[:8]}"
        self._codes[user_id] = ReferralCode(code=code, user_id=user_id)
        return code

    async def get_referral_code(self, user_id: int) -> Optional[ReferralCode]:
        return self._codes.get(user_id)

    async def get_invite_stats(self, db, user_id: int) -> dict:
        records = [r for r in self._records.values() if r.referrer_id == user_id]
        successful = [r for r in records if r.status == "completed"]
        total = len(records)
        rate = len(successful) / total if total > 0 else 0.0
        return {
            "total_invites": total,
            "successful_invites": len(successful),
            "conversion_rate": rate,
        }

    async def get_referral_stats(self, user_id: int) -> dict:
        code = self._codes.get(user_id)
        if code is None:
            return {"total_referrals": 0, "successful_referrals": 0, "pending_referrals": 0, "earned_points": 0}
        records = [r for r in self._records.values() if r.referrer_id == user_id]
        successful = [r for r in records if r.status == "completed"]
        pending = [r for r in records if r.status == "pending"]
        earned = sum(r.reward_points for r in successful)
        return {
            "total_referrals": len(records),
            "successful_referrals": len(successful),
            "pending_referrals": len(pending),
            "earned_points": earned,
        }

    async def get_invite_history(self, db, user_id: int, page: int = 1, page_size: int = 20) -> dict:
        records = self._invite_history.get(user_id, [])
        start = (page - 1) * page_size
        items = records[start:start + page_size]
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": len(records),
        }

    async def claim_reward(self, db, user_id: int, invite_code: str) -> dict:
        record = ReferralRecord(
            id=self._next_record_id,
            referrer_id=user_id,
            referral_code=invite_code,
            status="completed",
            reward_points=self._reward_points,
        )
        self._next_record_id += 1
        self._records[record.id] = record
        if user_id not in self._invite_history:
            self._invite_history[user_id] = []
        self._invite_history[user_id].append({
            "id": record.id,
            "invite_code": invite_code,
            "status": "completed",
            "reward_points": self._reward_points,
        })
        return {
            "success": True,
            "reward_points": self._reward_points,
            "message": f"成功领取{self._reward_points}积分奖励",
        }

    async def process_referral(self, referral_code: str, referee_id: int) -> dict:
        referrer = None
        for uid, code_obj in self._codes.items():
            if code_obj.code == referral_code:
                referrer = code_obj
                break
        if referrer is None:
            return {"success": False, "error": "无效的邀请码"}
        if referrer.user_id == referee_id:
            return {"success": False, "error": "不能使用自己的邀请码"}
        if not referrer.is_active:
            return {"success": False, "error": "邀请码已失效"}
        if referrer.usage_count >= referrer.max_uses:
            return {"success": False, "error": "邀请码已达到使用上限"}
        record = ReferralRecord(
            id=self._next_record_id,
            referrer_id=referrer.user_id,
            referee_id=referee_id,
            referral_code=referral_code,
            status="completed",
            reward_points=self._reward_points,
        )
        self._next_record_id += 1
        self._records[record.id] = record
        referrer.usage_count += 1
        return {"success": True, "reward_points": self._reward_points, "referee_reward_points": self._referee_reward_points}

    async def get_referral_history(self, user_id: int) -> list[dict]:
        records = [r for r in self._records.values() if r.referrer_id == user_id]
        return [{"id": r.id, "referee_id": r.referee_id, "status": r.status, "created_at": r.created_at, "reward_points": r.reward_points} for r in records]

    async def validate_referral_code(self, code: str) -> dict:
        for uid, code_obj in self._codes.items():
            if code_obj.code == code:
                if not code_obj.is_active:
                    return {"valid": False, "error": "邀请码已失效"}
                if code_obj.usage_count >= code_obj.max_uses:
                    return {"valid": False, "error": "邀请码已达到使用上限"}
                return {"valid": True, "user_id": code_obj.user_id}
        return {"valid": False, "error": "无效的邀请码"}

    async def get_analytics(self, db, user_id: int) -> dict:
        return {
            "daily_invites": {},
            "conversion_trend": [],
            "top_channels": [],
        }

    async def get_ranking(self, db, limit: int = 10) -> dict:
        return {
            "ranking": [],
            "total_participants": 0,
        }


referral_service = ReferralService()
