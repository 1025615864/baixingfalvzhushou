"""Withdrawal service."""
from __future__ import annotations
import enum
import time
from typing import Optional
from dataclasses import dataclass, field


class WithdrawalStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass
class WithdrawalRequest:
    id: str
    user_id: int
    amount: float
    status: WithdrawalStatus = WithdrawalStatus.PENDING
    bank_account: Optional[str] = None
    reason: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    processed_at: Optional[float] = None


class WithdrawalService:
    MIN_WITHDRAWAL = 10.0
    MAX_WITHDRAWAL = 50000.0

    def __init__(self):
        self._requests: dict[str, WithdrawalRequest] = {}
        self._next_id = 1

    async def create_withdrawal(self, user_id: int, amount: float, bank_account: Optional[str] = None) -> WithdrawalRequest:
        if amount < self.MIN_WITHDRAWAL:
            raise ValueError(f"最低提现金额为{self.MIN_WITHDRAWAL}元")
        if amount > self.MAX_WITHDRAWAL:
            raise ValueError(f"单次提现金额不能超过{self.MAX_WITHDRAWAL}元")
        req_id = f"wd_{self._next_id}"
        self._next_id += 1
        request = WithdrawalRequest(id=req_id, user_id=user_id, amount=amount, bank_account=bank_account)
        self._requests[req_id] = request
        return request

    async def get_withdrawal(self, withdrawal_id: str) -> Optional[WithdrawalRequest]:
        return self._requests.get(withdrawal_id)

    async def approve_withdrawal(self, withdrawal_id: str) -> dict:
        request = self._requests.get(withdrawal_id)
        if not request:
            return {"success": False, "error": "提现请求不存在"}
        if request.status != WithdrawalStatus.PENDING:
            return {"success": False, "error": "提现请求状态不正确"}
        request.status = WithdrawalStatus.APPROVED
        return {"success": True, "withdrawal_id": withdrawal_id, "status": request.status.value}

    async def reject_withdrawal(self, withdrawal_id: str, reason: Optional[str] = None) -> dict:
        request = self._requests.get(withdrawal_id)
        if not request:
            return {"success": False, "error": "提现请求不存在"}
        request.status = WithdrawalStatus.REJECTED
        request.reason = reason
        return {"success": True, "withdrawal_id": withdrawal_id, "status": request.status.value}

    async def complete_withdrawal(self, withdrawal_id: str) -> dict:
        request = self._requests.get(withdrawal_id)
        if not request:
            return {"success": False, "error": "提现请求不存在"}
        request.status = WithdrawalStatus.COMPLETED
        request.processed_at = time.time()
        return {"success": True, "withdrawal_id": withdrawal_id, "status": request.status.value}

    async def get_user_withdrawals(self, user_id: int) -> list[WithdrawalRequest]:
        return [r for r in self._requests.values() if r.user_id == user_id]
