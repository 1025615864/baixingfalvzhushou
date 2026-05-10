"""Points service package."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from app.services.points.points_service_base import (
    PointsServiceBase,
    PointsAction,
    PointsRule,
    PointsAccount,
    PointsTransaction,
    POINTS_RULES,
    get_vip_multiplier,
    get_points_rule,
)
from app.services.points.points_service_db import PointsServiceDB
from app.services.points.points_service_v2 import PointsServiceV2


class PointsService(PointsServiceBase):
    pass


def get_points_service() -> PointsService:
    return PointsService()


async def award_points(user_id: int, action: PointsAction, amount: Optional[int] = None, description: Optional[str] = None) -> PointsTransaction:
    svc = get_points_service()
    return svc.add_points(user_id, action, amount, description)


async def redeem_points(user_id: int, amount: int, description: Optional[str] = None) -> PointsTransaction:
    svc = get_points_service()
    return svc.deduct_points(user_id, amount, description)


async def get_balance(user_id: int) -> int:
    svc = get_points_service()
    return svc.get_balance(user_id)


@dataclass
class PointsHistoryItem:
    id: str
    user_id: int
    action: PointsAction
    amount: int
    description: Optional[str] = None
    balance_after: int = 0
    created_at: str = ""
