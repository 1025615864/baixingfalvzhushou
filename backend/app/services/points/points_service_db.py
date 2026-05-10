"""Points service with database backend."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from app.services.points.points_service_base import PointsServiceBase, PointsAction, PointsAccount, PointsTransaction


@dataclass
class PointsHistoryItem:
    id: int
    user_id: int
    action: PointsAction
    amount: int
    description: Optional[str] = None
    balance_after: int = 0
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class PointsServiceDB(PointsServiceBase):
    def __init__(self):
        super().__init__()
        self._db_connected = False

    async def connect(self) -> None:
        self._db_connected = True

    async def disconnect(self) -> None:
        self._db_connected = False

    async def get_account_async(self, user_id: int) -> PointsAccount:
        return self.get_or_create_account(user_id)

    async def add_points_async(self, user_id: int, action: PointsAction, amount: Optional[int] = None, description: Optional[str] = None) -> PointsTransaction:
        return self.add_points(user_id, action, amount, description)

    async def deduct_points_async(self, user_id: int, amount: int, description: Optional[str] = None) -> PointsTransaction:
        return self.deduct_points(user_id, amount, description)


async def get_balance_db(user_id: int) -> int:
    svc = PointsServiceDB()
    account = svc.get_or_create_account(user_id)
    return account.balance


async def award_points_db(user_id: int, action: PointsAction, amount: Optional[int] = None, description: Optional[str] = None) -> PointsTransaction:
    svc = PointsServiceDB()
    return svc.add_points(user_id, action, amount, description)


async def redeem_points_db(user_id: int, amount: int, description: Optional[str] = None) -> PointsTransaction:
    svc = PointsServiceDB()
    return svc.deduct_points(user_id, amount, description)
