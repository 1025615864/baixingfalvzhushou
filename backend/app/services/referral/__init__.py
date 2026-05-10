"""Referral service."""
from __future__ import annotations
import enum
import time
import uuid
from typing import Optional
from dataclasses import dataclass, field


class ReferralStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    EXPIRED = "expired"
    REWARDED = "rewarded"


@dataclass
class Referral:
    id: str
    referrer_id: int
    referee_id: int
    code: str
    status: ReferralStatus = ReferralStatus.PENDING
    reward_points: int = 0
    created_at: float = field(default_factory=time.time)


class ReferralRewardConfig:
    def __init__(self):
        self._rewards: dict[str, dict] = {
            "referrer": {"points": 100},
            "invitee": {"points": 50},
        }

    def get_reward(self, role: str) -> dict:
        return self._rewards.get(role, {"points": 0})

    def set_reward(self, role: str, points: int | None = None) -> None:
        if role not in self._rewards:
            self._rewards[role] = {"points": 0}
        if points is not None:
            self._rewards[role]["points"] = points


class ShareService:
    def __init__(self):
        self._share_records: dict[str, dict] = {}
        self._next_id = 1

    async def create_share_link(self, user_id: int, content_type: str, content_id: str) -> dict:
        share_id = f"SHARE-{self._next_id:04d}"
        self._next_id += 1
        record = {
            "share_id": share_id,
            "user_id": user_id,
            "content_type": content_type,
            "content_id": content_id,
            "share_link": f"https://baixing-law.com/share/{share_id}",
            "clicks": 0,
            "conversions": 0,
        }
        self._share_records[share_id] = record
        return record

    async def track_click(self, share_id: str) -> bool:
        record = self._share_records.get(share_id)
        if not record:
            return False
        record["clicks"] += 1
        return True

    async def track_conversion(self, share_id: str, converted_user_id: int) -> dict:
        record = self._share_records.get(share_id)
        if not record:
            return {"success": False, "error": "分享记录不存在"}
        record["conversions"] += 1
        return {"success": True}

    def get_share_stats(self, user_id: int) -> dict:
        user_records = [r for r in self._share_records.values() if r["user_id"] == user_id]
        total_shares = len(user_records)
        total_clicks = sum(r["clicks"] for r in user_records)
        total_conversions = sum(r["conversions"] for r in user_records)
        conversion_rate = f"{total_conversions / total_clicks * 100:.1f}%" if total_clicks > 0 else "0.0%"
        return {
            "total_shares": total_shares,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "conversion_rate": conversion_rate,
        }


class ReferralService:
    def __init__(self):
        self._referrals: dict[str, dict] = {}
        self._codes: dict[str, int] = {}
        self._next_id = 1
        self._reward_config = ReferralRewardConfig()

    def generate_referral_code(self, user_id: int) -> str:
        code = f"REF-{uuid.uuid4().hex[:8].upper()}"
        self._codes[code] = user_id
        return code

    async def create_referral_code(self, user_id: int, expires_in_hours: int = 24) -> dict:
        code = self.generate_referral_code(user_id)
        expires_at = time.time() + expires_in_hours * 3600
        self._referrals[code] = {
            "code": code,
            "user_id": user_id,
            "status": ReferralStatus.PENDING,
            "expires_at": expires_at,
            "invitee_id": None,
            "reward_claimed": False,
        }
        return {
            "code": code,
            "share_url": f"https://baixing-law.com/ref/{code}",
            "expires_at": expires_at,
        }

    async def accept_referral(self, code: str, invitee_id: int) -> dict:
        ref = self._referrals.get(code)
        if not ref:
            return {"success": False, "error": "邀请码不存在"}
        if ref["expires_at"] and time.time() > ref["expires_at"]:
            return {"success": False, "error": "邀请码已过期"}
        if ref["status"] != ReferralStatus.PENDING:
            return {"success": False, "error": "邀请码已使用"}
        ref["status"] = ReferralStatus.ACCEPTED
        ref["invitee_id"] = invitee_id
        return {"success": True, "referrer_id": ref["user_id"]}

    async def claim_reward(self, user_id: int, code: str) -> dict:
        ref = self._referrals.get(code)
        if not ref:
            return {"success": False, "error": "邀请码不存在"}
        if ref["status"] != ReferralStatus.ACCEPTED:
            return {"success": False, "error": "邀请码未被接受"}
        if ref["reward_claimed"]:
            return {"success": False, "error": "奖励已领取"}
        ref["reward_claimed"] = True
        ref["status"] = ReferralStatus.REWARDED
        reward = self._reward_config.get_reward("referrer")
        return {"success": True, "reward": reward}

    async def create_referral(self, referrer_id: int, referee_id: int, code: Optional[str] = None) -> Referral:
        referral_id = f"ref_{self._next_id}"
        self._next_id += 1
        if code is None:
            code = self.generate_referral_code(referrer_id)
        referral = Referral(id=referral_id, referrer_id=referrer_id, referee_id=referee_id, code=code)
        self._referrals[referral_id] = {
            "id": referral_id,
            "user_id": referrer_id,
            "code": code,
            "status": ReferralStatus.PENDING,
        }
        return referral

    async def get_referral(self, referral_id: str) -> Optional[Referral]:
        return self._referrals.get(referral_id)

    async def get_user_referrals(self, user_id: int) -> list[Referral]:
        return [r for r in self._referrals.values() if r.get("user_id") == user_id or r.get("referrer_id") == user_id]

    async def complete_referral(self, referral_id: str, reward_points: int = 50) -> dict:
        referral = self._referrals.get(referral_id)
        if not referral:
            return {"success": False, "error": "推荐不存在"}
        referral["status"] = ReferralStatus.COMPLETED
        return {"success": True, "referral_id": referral_id, "reward_points": reward_points}

    def validate_code(self, code: str) -> Optional[int]:
        return self._codes.get(code)

    def get_referral_stats(self, user_id: int) -> dict:
        user_refs = {k: v for k, v in self._referrals.items() if v.get("user_id") == user_id}
        total = len(user_refs)
        accepted = sum(1 for r in user_refs.values() if r.get("status") == ReferralStatus.ACCEPTED)
        pending = sum(1 for r in user_refs.values() if r.get("status") == ReferralStatus.PENDING)
        success_rate = f"{accepted / total * 100:.1f}%" if total > 0 else "0.0%"
        return {
            "total_codes": total,
            "accepted": accepted,
            "pending": pending,
            "success_rate": success_rate,
        }


referral_service = ReferralService()
