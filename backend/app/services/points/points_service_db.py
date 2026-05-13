"""Points service with database backend."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from app.services.points.points_service_base import PointsServiceBase, PointsAction, PointsAccount, PointsTransaction, POINTS_RULES, PointsRule


@dataclass
class PointsHistoryItem:
    id: int
    user_id: int
    action: str
    points: int
    balance_after: int = 0
    description: Optional[str] = None
    created_at: datetime = None
    extra_data: Optional[dict] = None

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

    async def _get_or_create_user(self, db, user_id: int):
        from sqlalchemy import select
        from app.models.points import PointsUser
        stmt = select(PointsUser).where(PointsUser.user_id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            user = PointsUser(
                user_id=user_id,
                balance=0,
                total_earned=0,
                total_spent=0,
                continuous_signin_days=0,
                last_signin_at=None,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    async def get_balance(self, db, user_id: int) -> int:
        user = await self._get_or_create_user(db, user_id)
        return user.balance

    async def _get_daily_count(self, db, user_id: int, action: str, date: str) -> int:
        from sqlalchemy import select
        from app.models.points import PointsDailyCount
        stmt = select(PointsDailyCount).where(
            PointsDailyCount.user_id == user_id,
            PointsDailyCount.action == action,
            PointsDailyCount.date == date,
        )
        result = await db.execute(stmt)
        daily = result.scalar_one_or_none()
        if daily is None:
            return 0
        return daily.count

    async def _update_daily_count(self, db, user_id: int, action: str, date: str, count: int) -> None:
        from sqlalchemy import select
        from app.models.points import PointsDailyCount
        stmt = select(PointsDailyCount).where(
            PointsDailyCount.user_id == user_id,
            PointsDailyCount.action == action,
            PointsDailyCount.date == date,
        )
        result = await db.execute(stmt)
        daily = result.scalar_one_or_none()
        if daily is None:
            daily = PointsDailyCount(user_id=user_id, action=action, date=date, count=count)
            db.add(daily)
        else:
            daily.count = count
        await db.commit()

    async def _get_balance_before(self, db, user_id: int) -> int:
        from sqlalchemy import select, func
        from app.models.points import PointsHistory
        stmt = select(func.coalesce(func.sum(PointsHistory.points), 0)).where(
            PointsHistory.user_id == user_id
        )
        result = await db.execute(stmt)
        balance = result.scalar_one_or_none()
        return balance if balance is not None else 0

    async def award_points(self, db, user_id: int, action: str, description: Optional[str] = None, **kwargs) -> tuple[int, Optional[str]]:
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

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_count = await self._get_daily_count(db, user_id, action, today)
        if daily_count >= rule.max_daily:
            return 0, f"今日{action}次数已达上限"

        points = rule.points
        user = await self._get_or_create_user(db, user_id)
        user.balance = getattr(user, 'balance', 0) + points
        user.total_earned = getattr(user, 'total_earned', 0) + points

        await self._update_daily_count(db, user_id, action, today, daily_count + 1)

        history = PointsHistoryItem(
            id=0,
            user_id=user_id,
            action=action,
            points=points,
            balance_after=user.balance,
            description=description,
        )
        db.add(history)
        await db.commit()

        return points, None

    async def record_transaction(self, db, user_id: int, amount: int, transaction_type: str = "deposit", source: str = "", remark: Optional[str] = None) -> PointsHistoryItem:
        user = await self._get_or_create_user(db, user_id)
        user.balance = getattr(user, 'balance', 0) + amount
        if amount > 0:
            user.total_earned = getattr(user, 'total_earned', 0) + amount
        else:
            user.total_spent = getattr(user, 'total_spent', 0) + abs(amount)

        history = PointsHistoryItem(
            id=0,
            user_id=user_id,
            action=transaction_type,
            points=amount,
            balance_after=user.balance,
            description=remark,
        )
        db.add(history)
        await db.commit()
        return history

    async def redeem_points(self, db, user_id: int, points: int, product_id: Optional[str] = None, description: Optional[str] = None) -> tuple[bool, Optional[str]]:
        user = await self._get_or_create_user(db, user_id)
        if user.balance < points:
            return False, "积分不足"

        user.balance = user.balance - points
        user.total_spent = getattr(user, 'total_spent', 0) + points

        history = PointsHistoryItem(
            id=0,
            user_id=user_id,
            action="redeem",
            points=-points,
            balance_after=user.balance,
            description=description,
        )
        db.add(history)
        await db.commit()

        return True, None

    async def get_history(self, db, user_id: int, limit: int = 20, offset: int = 0) -> list:
        from sqlalchemy import select
        from app.models.points import PointsHistory
        stmt = select(PointsHistory).where(PointsHistory.user_id == user_id).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_daily_stats(self, db, user_id: int) -> dict:
        from sqlalchemy import select
        from app.models.points import PointsDailyCount
        stmt = select(PointsDailyCount).where(PointsDailyCount.user_id == user_id)
        result = await db.execute(stmt)
        counts = result.scalars().all()
        stats = {}
        for c in counts:
            stats[c.action] = c.count
        return stats

    async def get_continuous_days(self, db, user_id: int) -> int:
        user = await self._get_or_create_user(db, user_id)
        return getattr(user, 'continuous_signin_days', 0)

    def get_rules(self) -> list[dict]:
        rules = []
        for action, rule in POINTS_RULES.items():
            rules.append({
                "action": action.value,
                "points": rule.points,
                "max_daily": rule.max_daily,
                "description": rule.description,
            })
        return rules

    async def get_leaderboard(self, db, top_k: int = 10) -> list[dict]:
        from sqlalchemy import select
        from app.models.points import PointsUser
        stmt = select(PointsUser).order_by(PointsUser.balance.desc()).limit(top_k)
        result = await db.execute(stmt)
        users = result.scalars().all()
        leaderboard = []
        for i, user in enumerate(users, 1):
            leaderboard.append({
                "rank": i,
                "user_id": user.user_id,
                "balance": user.balance,
            })
        return leaderboard

    async def reset_daily_counts(self, db) -> None:
        from sqlalchemy import select, update
        from app.models.points import PointsDailyCount
        stmt = select(PointsDailyCount)
        result = await db.execute(stmt)
        counts = result.scalars().all()
        for c in counts:
            c.count = 0
        await db.commit()

    async def _handle_signin_bonus(self, db, user, base_points: int, today: str) -> PointsHistoryItem:
        continuous_days = getattr(user, 'continuous_signin_days', 0)
        last_signin_at = getattr(user, 'last_signin_at', None)

        bonus_points = 0
        if last_signin_at is not None:
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
            last_date = last_signin_at.strftime("%Y-%m-%d") if hasattr(last_signin_at, 'strftime') else str(last_signin_at)[:10]
            if last_date == yesterday:
                continuous_days += 1
            else:
                continuous_days = 1
        else:
            continuous_days = 1

        if continuous_days >= 30:
            bonus_points = 50
        elif continuous_days >= 7:
            bonus_points = 20

        total_points = base_points + bonus_points
        user.balance = getattr(user, 'balance', 0) + total_points
        user.total_earned = getattr(user, 'total_earned', 0) + total_points
        user.continuous_signin_days = continuous_days
        user.last_signin_at = datetime.now(timezone.utc)

        history = PointsHistoryItem(
            id=0,
            user_id=user.user_id,
            action="daily_signin",
            points=total_points,
            balance_after=user.balance,
            description=f"每日签到(连续{continuous_days}天)",
        )
        db.add(history)
        await db.commit()
        await db.refresh(user)
        return history

    async def get_account_async(self, user_id: int) -> PointsAccount:
        return self.get_or_create_account(user_id)

    async def add_points_async(self, user_id: int, action: PointsAction, amount: Optional[int] = None, description: Optional[str] = None) -> PointsTransaction:
        return self.add_points(user_id, action, amount, description)

    async def deduct_points_async(self, user_id: int, amount: int, description: Optional[str] = None) -> PointsTransaction:
        return self.deduct_points(user_id, amount, description)


async def get_balance_db(db, user_id: int) -> int:
    svc = PointsServiceDB()
    return await svc.get_balance(db, user_id)


async def award_points_db(db, user_id: int, action: str, description: Optional[str] = None, **kwargs) -> tuple[int, Optional[str]]:
    svc = PointsServiceDB()
    return await svc.award_points(db, user_id, action, description, **kwargs)


async def redeem_points_db(db, user_id: int, points: int, product_id: Optional[str] = None, description: Optional[str] = None) -> tuple[bool, Optional[str]]:
    svc = PointsServiceDB()
    return await svc.redeem_points(db, user_id, points, product_id, description)
