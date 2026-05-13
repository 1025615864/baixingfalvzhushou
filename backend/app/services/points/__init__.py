"""Points service package."""
from __future__ import annotations
import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any
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


@dataclass
class PointsHistoryItem:
    id: int
    user_id: int
    action: str
    points: int
    balance_after: int = 0
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    extra_data: Optional[dict] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class PointsService(PointsServiceBase):
    def __init__(self):
        super().__init__()
        self._user_points: dict[int, int] = {}
        self._user_history: dict[int, list[PointsHistoryItem]] = {}
        self._daily_counts: dict[int, dict[str, int]] = {}
        self._next_history_id = 1

    def get_balance(self, user_id: int) -> int:
        return self._user_points.get(user_id, 0)

    async def award_points(self, user_id: int, action: str, description: Optional[str] = None, **kwargs) -> tuple[int, Optional[str]]:
        rule = POINTS_RULES.get(PointsAction(action) if isinstance(action, str) else action)
        if rule is None:
            try:
                action_enum = PointsAction(action)
                rule = POINTS_RULES.get(action_enum)
            except (ValueError, KeyError):
                pass
        if rule is None:
            return 0, f"未知的积分动作: {action}"

        if rule.requires_auth and user_id <= 0:
            return 0, "需要登录才能执行此操作"

        user_daily = self._daily_counts.setdefault(user_id, {})
        count = user_daily.get(action, 0)
        if count >= rule.max_daily:
            return 0, f"今日{action}次数已达上限"

        points = rule.points
        vip_mult = rule.vip_multiplier
        if vip_mult and vip_mult != 1.0:
            points = int(points * vip_mult)

        self._user_points[user_id] = self._user_points.get(user_id, 0) + points
        user_daily[action] = count + 1

        item = PointsHistoryItem(
            id=self._next_history_id,
            user_id=user_id,
            action=action,
            points=points,
            balance_after=self._user_points[user_id],
            description=description,
        )
        self._next_history_id += 1
        self._user_history.setdefault(user_id, []).append(item)

        return points, None

    async def redeem_points(self, user_id: int, points: int, product_id: Optional[str] = None, description: Optional[str] = None, **kwargs) -> tuple[bool, Optional[str]]:
        balance = self._user_points.get(user_id, 0)
        if balance < points:
            return False, "积分不足"

        self._user_points[user_id] = balance - points

        item = PointsHistoryItem(
            id=self._next_history_id,
            user_id=user_id,
            action="redeem",
            points=-points,
            balance_after=self._user_points[user_id],
            description=description,
        )
        self._next_history_id += 1
        self._user_history.setdefault(user_id, []).append(item)

        return True, None

    def get_history(self, user_id: int, limit: int = 20, offset: int = 0) -> list[PointsHistoryItem]:
        history = self._user_history.get(user_id, [])
        return history[offset:offset + limit]


_points_service_instance: Optional[PointsService] = None


def get_points_service() -> PointsService:
    global _points_service_instance
    if _points_service_instance is None:
        _points_service_instance = PointsService()
    return _points_service_instance


async def award_points(user_id: int, action: PointsAction, amount: Optional[int] = None, description: Optional[str] = None) -> PointsTransaction:
    svc = get_points_service()
    return svc.add_points(user_id, action, amount, description)


async def redeem_points(user_id: int, amount: int, description: Optional[str] = None) -> PointsTransaction:
    svc = get_points_service()
    return svc.deduct_points(user_id, amount, description)


async def get_balance(user_id: int, db: Any = None) -> int:
    svc = get_points_service()
    return svc.get_balance(user_id)
