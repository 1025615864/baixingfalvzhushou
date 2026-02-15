"""积分服务（数据库持久化版）

提供积分获取、消耗、查询等功能，使用数据库存储。
"""

import logging
from typing import Any, Dict, List, Optional, cast
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...database import AsyncSessionLocal
from ...models import PointsUser, PointsHistory, PointsDailyCount
from .points_service_base import (
    PointsAction,
    PointsRule,
    POINTS_RULES,
    get_vip_multiplier,
)

logger = logging.getLogger(__name__)


@dataclass
class PointsHistoryItem:
    """积分历史记录"""
    id: int
    user_id: int
    action: str
    points: int
    balance_after: int
    description: str
    created_at: datetime
    extra_data: Optional[Dict] = None


class PointsServiceDB:
    """积分服务（数据库版）"""

    def __init__(self):
        pass

    async def _get_or_create_user(
            self, db: AsyncSession, user_id: int) -> PointsUser:
        """获取或创建用户积分账户"""
        result = await db.execute(
            select(PointsUser).where(PointsUser.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = PointsUser(
                user_id=user_id,
                balance=0,
                total_earned=0,
                total_spent=0,
                continuous_signin_days=0,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return user

    async def get_balance(self, db: AsyncSession, user_id: int) -> int:
        """获取用户积分余额"""
        user = await self._get_or_create_user(db, user_id)
        return int(getattr(user, "balance", 0) or 0)

    async def award_points(
        self,
        db: AsyncSession,
        user_id: int,
        action: str,
        description: Optional[str] = None,
        extra_data: Optional[Dict] = None,
    ) -> tuple[int, Optional[str]]:
        """奖励积分

        Returns:
            (获得积分, 错误信息)
        """
        rule = POINTS_RULES.get(action)
        if not rule:
            return 0, f"未知的积分动作: {action}"

        if rule.requires_auth and user_id <= 0:
            return 0, "需要登录后才能获得积分"

        user = await self._get_or_create_user(db, user_id)
        user_any = cast(Any, user)
        today = datetime.now().strftime("%Y-%m-%d")

        # 检查每日限制
        daily_count = await self._get_daily_count(db, user_id, action, today)
        if daily_count >= rule.max_daily:
            return 0, f"今日 {rule.description} 次数已达上限"

        # 计算积分
        points = rule.points

        # VIP 加成
        vip_multiplier = await get_vip_multiplier(user_id, db)
        if vip_multiplier > 1.0:
            points = int(points * vip_multiplier)

        # 连续签到加成
        if action == "daily_signin":
            user = await self._handle_signin_bonus(db, user, points, today)
            points = int(getattr(user, "balance", 0) or 0) - (await self._get_balance_before(db, user_id)) if False else points

        # 更新每日计数
        await self._update_daily_count(db, user_id, action, today, daily_count + 1)

        # 更新用户积分
        balance_before = int(getattr(user_any, "balance", 0) or 0)
        setattr(user_any, "balance", balance_before + points)
        setattr(
            user_any,
            "total_earned",
            int(getattr(user_any, "total_earned", 0) or 0) + points,
        )
        setattr(user_any, "updated_at", datetime.now())

        # 记录历史
        history = PointsHistory(
            user_id=user_id,
            action=action,
            points=points,
            balance_before=balance_before,
            balance_after=int(getattr(user_any, "balance", 0) or 0),
            description=description or f"奖励: {rule.description}",
            metadata_json=extra_data,
        )
        db.add(history)
        await db.commit()

        logger.info(f"用户 {user_id} 获得 {points} 积分 (动作: {action})")

        return points, None

    async def record_transaction(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        amount: int,
        transaction_type: str,
        source: str | None = None,
        remark: str | None = None,
    ) -> PointsHistoryItem | None:
        user = await self._get_or_create_user(db, int(user_id))
        user_any = cast(Any, user)
        balance_before = int(getattr(user_any, "balance", 0) or 0)
        setattr(user_any, "balance", balance_before + int(amount))
        if amount > 0:
            setattr(
                user_any, "total_earned", int(
                    getattr(
                        user_any, "total_earned", 0) or 0) + int(amount))
        else:
            setattr(user_any, "total_spent", int(
                getattr(user_any, "total_spent", 0) or 0) + abs(int(amount)))

        history = PointsHistory(
            user_id=int(user_id),
            action=str(transaction_type),
            points=int(amount),
            balance_before=balance_before,
            balance_after=int(getattr(user_any, "balance", 0) or 0),
            description=remark,
            metadata_json={"source": source} if source else None,
        )
        db.add(history)
        await db.commit()
        await db.refresh(history)
        return PointsHistoryItem(
            id=int(getattr(history, "id", 0) or 0),
            user_id=int(user_id),
            action=str(transaction_type),
            points=int(amount),
            balance_after=int(getattr(user_any, "balance", 0) or 0),
            description=remark or "",
            created_at=getattr(history, "created_at", datetime.now()),
            extra_data={"source": source} if source else None,
        )

    async def _handle_signin_bonus(
        self,
        db: AsyncSession,
        user: PointsUser,
        points: int,
        today: str,
    ) -> PointsUser:
        """处理签到奖励"""
        user_any = cast(Any, user)
        continuous_days = int(
            getattr(
                user_any,
                "continuous_signin_days",
                0) or 0)
        last_signin = getattr(user_any, "last_signin_at", None)

        if last_signin:
            last_date = last_signin.strftime("%Y-%m-%d")
            if last_date == today:
                return user

            if last_date == (datetime.strptime(today, "%Y-%m-%d") -
                             timedelta(days=1)).strftime("%Y-%m-%d"):
                continuous_days += 1
            else:
                continuous_days = 1
        else:
            continuous_days = 1

        setattr(user_any, "continuous_signin_days", continuous_days)
        setattr(user_any, "last_signin_at", datetime.now())

        # 连续签到奖励
        bonus = 0
        if continuous_days >= 30 and continuous_days % 30 == 1:
            bonus = 50
        elif continuous_days >= 7 and continuous_days % 7 == 1:
            bonus = 10

        if bonus > 0:
            current_balance = int(getattr(user_any, "balance", 0) or 0)
            setattr(user_any, "balance", current_balance + int(bonus))
            setattr(
                user_any,
                "total_earned",
                int(getattr(user_any, "total_earned", 0) or 0) + int(bonus),
            )

            history = PointsHistory(
                user_id=int(getattr(user_any, "user_id", 0) or 0),
                action="continuous_bonus",
                points=bonus,
                balance_before=current_balance,
                balance_after=current_balance + int(bonus),
                description=f"连续签到 {continuous_days} 天奖励",
            )
            db.add(history)

        await db.commit()
        await db.refresh(user)
        return user

    async def _get_daily_count(
        self,
        db: AsyncSession,
        user_id: int,
        action: str,
        date: str,
    ) -> int:
        """获取当日动作计数"""
        result = await db.execute(
            select(PointsDailyCount).where(
                PointsDailyCount.user_id == user_id,
                PointsDailyCount.action == action,
                PointsDailyCount.date == date,
            )
        )
        daily = result.scalar_one_or_none()
        return int(getattr(daily, "count", 0) or 0)

    async def _update_daily_count(
        self,
        db: AsyncSession,
        user_id: int,
        action: str,
        date: str,
        count: int,
    ):
        """更新当日动作计数"""
        result = await db.execute(
            select(PointsDailyCount).where(
                PointsDailyCount.user_id == user_id,
                PointsDailyCount.action == action,
                PointsDailyCount.date == date,
            )
        )
        daily = result.scalar_one_or_none()

        if daily:
            setattr(daily, "count", int(count))
            setattr(daily, "updated_at", datetime.now())
        else:
            daily = PointsDailyCount(
                user_id=user_id,
                action=action,
                count=count,
                date=date,
            )
            db.add(daily)

        await db.commit()

    async def _get_balance_before(self, db: AsyncSession, user_id: int) -> int:
        """获取操作前的余额"""
        result = await db.execute(
            select(PointsHistory.balance_after)
            .where(PointsHistory.user_id == user_id)
            .order_by(PointsHistory.created_at.desc())
            .limit(1)
        )
        balance = result.scalar_one_or_none()
        return int(balance or 0)

    async def redeem_points(
        self,
        db: AsyncSession,
        user_id: int,
        points: int,
        product_id: str,
        description: str,
    ) -> tuple[bool, Optional[str]]:
        """消耗积分"""
        user = await self._get_or_create_user(db, user_id)
        user_any = cast(Any, user)
        current_balance = int(getattr(user_any, "balance", 0) or 0)
        if current_balance < points:
            return False, f"积分不足，需要 {points} 积分，当前余额 {current_balance}"

        balance_before = current_balance
        setattr(user_any, "balance", balance_before - points)
        setattr(
            user_any,
            "total_spent",
            int(getattr(user_any, "total_spent", 0) or 0) + points,
        )
        setattr(user_any, "updated_at", datetime.now())

        history = PointsHistory(
            user_id=user_id,
            action="redeem",
            points=-points,
            balance_before=balance_before,
            balance_after=int(getattr(user_any, "balance", 0) or 0),
            description=description,
            metadata_json={"product_id": product_id},
        )
        db.add(history)
        await db.commit()

        logger.info(f"用户 {user_id} 消耗 {points} 积分 (商品: {product_id})")

        return True, None

    async def get_history(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[PointsHistoryItem]:
        """获取积分历史"""
        result = await db.execute(
            select(PointsHistory)
            .where(PointsHistory.user_id == user_id)
            .order_by(PointsHistory.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        histories = result.scalars().all()

        return [
            PointsHistoryItem(
                id=int(getattr(h, "id", 0) or 0),
                user_id=int(getattr(h, "user_id", 0) or 0),
                action=str(getattr(h, "action", "")),
                points=int(getattr(h, "points", 0) or 0),
                balance_after=int(getattr(h, "balance_after", 0) or 0),
                description=str(getattr(h, "description", "") or ""),
                created_at=getattr(h, "created_at", datetime.now()),
                extra_data=getattr(h, "metadata_json", None),
            )
            for h in histories
        ]

    async def get_daily_stats(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Dict[str, int]:
        """获取今日统计"""
        today = datetime.now().strftime("%Y-%m-%d")
        result = await db.execute(
            select(PointsDailyCount)
            .where(
                PointsDailyCount.user_id == user_id,
                PointsDailyCount.date == today,
            )
        )
        dailies = result.scalars().all()

        return {str(getattr(d, "action", "")): int(
            getattr(d, "count", 0) or 0) for d in dailies}

    async def get_continuous_days(self, db: AsyncSession, user_id: int) -> int:
        """获取连续签到天数"""
        user = await self._get_or_create_user(db, user_id)
        return int(getattr(user, "continuous_signin_days", 0) or 0)

    async def daily_signin(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """每日签到

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            签到结果，包含success, points, continuous_days, total_points等字段
        """
        # 使用award_points方法处理签到
        points, error = await self.award_points(
            db=db,
            user_id=user_id,
            action="daily_signin",
            description="每日签到"
        )

        if error:
            return {
                "success": False,
                "message": error,
                "points": 0,
                "continuous_days": await self.get_continuous_days(db, user_id),
                "total_points": await self.get_balance(db, user_id),
            }

        return {
            "success": True,
            "message": "签到成功",
            "points": points,
            "continuous_days": await self.get_continuous_days(db, user_id),
            "total_points": await self.get_balance(db, user_id),
        }

    def get_rules(self) -> List[Dict[str, Any]]:
        """获取积分规则列表"""
        return [
            {
                "action": rule.action.value,
                "points": rule.points,
                "max_daily": rule.max_daily,
                "description": rule.description,
                "vip_multiplier": rule.vip_multiplier,
                "requires_auth": rule.requires_auth,
            }
            for rule in POINTS_RULES.values()
        ]

    async def get_leaderboard(
        self,
        db: AsyncSession,
        top_k: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取积分排行榜"""
        result = await db.execute(
            select(PointsUser)
            .order_by(PointsUser.balance.desc())
            .limit(top_k)
        )
        users = result.scalars().all()

        return [
            {
                "rank": i + 1,
                "user_id": u.user_id,
                "balance": int(getattr(u, "balance", 0) or 0),
                "continuous_days": int(getattr(u, "continuous_signin_days", 0) or 0),
            }
            for i, u in enumerate(users)
        ]

    async def reset_daily_counts(
            self, db: AsyncSession, date: str | None = None):
        """重置每日计数"""
        date = date or datetime.now().strftime("%Y-%m-%d")
        await db.execute(
            select(PointsDailyCount)
            .where(PointsDailyCount.date == date)
        )
        result = await db.execute(
            select(PointsDailyCount).where(PointsDailyCount.date == date)
        )
        dailies = result.scalars().all()
        for d in dailies:
            setattr(d, "count", 0)
        await db.commit()
        logger.info(f"每日积分计数已重置 ({date})")


# 便捷函数
async def get_balance_db(db: AsyncSession, user_id: int) -> int:
    """获取积分余额"""
    service = PointsServiceDB()
    return await service.get_balance(db, user_id)


async def award_points_db(
    db: AsyncSession,
    user_id: int,
    action: str,
    description: Optional[str] = None,
    extra_data: Optional[Dict] = None,
) -> tuple[int, Optional[str]]:
    """奖励积分"""
    service = PointsServiceDB()
    return await service.award_points(db, user_id, action, description, extra_data)


async def redeem_points_db(
    db: AsyncSession,
    user_id: int,
    points: int,
    product_id: str,
    description: str,
) -> tuple[bool, Optional[str]]:
    """消耗积分"""
    service = PointsServiceDB()
    return await service.redeem_points(db, user_id, points, product_id, description)


points_service_db = PointsServiceDB()
