"""积分服务

提供积分获取、消耗、查询等功能。
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.points import PointsUser, PointsHistory

logger = logging.getLogger(__name__)


class PointsAction(str, Enum):
    """积分动作"""
    DAILY_SIGNIN = "daily_signin"
    AI_CONSULTATION = "ai_consultation"
    POST_CREATED = "post_created"
    COMMENT_CREATED = "comment_created"
    SHARE_CONTENT = "share_content"
    DOCUMENT_GENERATED = "document_generated"
    LAWYER_BOOKING = "lawyer_booking"
    INVITE_FRIEND = "invite_friend"
    FAVORITE_POST = "favorite_post"
    COMPLETE_PROFILE = "complete_profile"
    FIRST_QUESTION = "first_question"


@dataclass
class PointsRule:
    """积分规则"""
    action: PointsAction
    points: int
    max_daily: int = 1
    description: str = ""
    continuous_bonus: Optional[Dict[str, Dict[str, Any]]] = None
    requires_auth: bool = False
    vip_multiplier: float = 1.0


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
    metadata: Optional[Dict] = None


# 积分规则配置
POINTS_RULES: Dict[str, PointsRule] = {
    "daily_signin": PointsRule(
        action=PointsAction.DAILY_SIGNIN,
        points=5,
        max_daily=1,
        description="每日签到",
        continuous_bonus={
            "7_days": {"bonus": 10, "description": "连续签到7天奖励"},
            "30_days": {"bonus": 50, "description": "连续签到30天奖励"},
        },
    ),
    "ai_consultation": PointsRule(
        action=PointsAction.AI_CONSULTATION,
        points=2,
        max_daily=10,
        description="完成 AI 咨询",
        vip_multiplier=1.5,
        requires_auth=True,
    ),
    "post_created": PointsRule(
        action=PointsAction.POST_CREATED,
        points=10,
        max_daily=5,
        description="发布帖子",
        requires_auth=True,
    ),
    "comment_created": PointsRule(
        action=PointsAction.COMMENT_CREATED,
        points=5,
        max_daily=20,
        description="发表评论",
        requires_auth=True,
    ),
    "share_content": PointsRule(
        action=PointsAction.SHARE_CONTENT,
        points=15,
        max_daily=10,
        description="分享内容",
    ),
    "document_generated": PointsRule(
        action=PointsAction.DOCUMENT_GENERATED,
        points=8,
        max_daily=5,
        description="生成文书",
        requires_auth=True,
    ),
    "lawyer_booking": PointsRule(
        action=PointsAction.LAWYER_BOOKING,
        points=20,
        max_daily=2,
        description="预约律师",
        requires_auth=True,
    ),
    "invite_friend": PointsRule(
        action=PointsAction.INVITE_FRIEND,
        points=100,
        max_daily=10,
        description="邀请好友",
        requires_auth=True,
    ),
    "favorite_post": PointsRule(
        action=PointsAction.FAVORITE_POST,
        points=2,
        max_daily=10,
        description="收藏帖子",
        requires_auth=True,
    ),
    "complete_profile": PointsRule(
        action=PointsAction.COMPLETE_PROFILE,
        points=50,
        max_daily=1,
        description="完善个人资料",
        requires_auth=True,
    ),
    "first_question": PointsRule(
        action=PointsAction.FIRST_QUESTION,
        points=20,
        max_daily=1,
        description="首次提问",
    ),
}


class PointsService:
    """积分服务"""

    def __init__(self):
        self._user_points: Dict[int, int] = {}  # user_id -> balance
        # user_id -> history
        self._user_history: Dict[int, List[PointsHistoryItem]] = {}
        # user_id -> action -> count
        self._daily_counts: Dict[int, Dict[str, int]] = {}
        # user_id -> last signin date
        self._last_signin: Dict[int, datetime] = {}
        # user_id -> continuous days
        self._continuous_days: Dict[int, int] = {}

    def get_balance(self, user_id: int) -> int:
        """获取用户积分余额"""
        return self._user_points.get(user_id, 0)

    async def award_points(
        self,
        user_id: int,
        action: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[int, Optional[str]]:
        """奖励积分

        Returns:
            (获得积分, 错误信息)
        """
        rule = POINTS_RULES.get(action)
        if not rule:
            return 0, f"未知的积分动作: {action}"

        # 检查权限
        if rule.requires_auth and user_id <= 0:
            return 0, "需要登录后才能获得积分"

        # 初始化用户数据
        if user_id not in self._user_points:
            self._user_points[user_id] = 0
        if user_id not in self._daily_counts:
            self._daily_counts[user_id] = {}
        if user_id not in self._user_history:
            self._user_history[user_id] = []

        # 检查每日限制
        _ = datetime.now().strftime("%Y-%m-%d")
        today_count = self._daily_counts[user_id].get(action, 0)

        if today_count >= rule.max_daily:
            return 0, f"今日 {rule.description} 次数已达上限"

        # 计算积分
        points = rule.points

        # VIP 加成
        # 这里可以检查用户是否是 VIP
        # is_vip = await self._check_vip_status(user_id)
        # if is_vip:
        #     points = int(points * rule.vip_multiplier)

        # 连续签到加成
        if action == "daily_signin":
            continuous_days = self._continuous_days.get(user_id, 0)
            last_signin = self._last_signin.get(user_id)

            if last_signin:
                last_date = last_signin.date()
                today_date = datetime.now().date()

                if last_date == today_date:
                    return 0, "今日已签到"

                if last_date == today_date - timedelta(days=1):
                    continuous_days += 1
                else:
                    continuous_days = 1

            self._continuous_days[user_id] = continuous_days
            self._last_signin[user_id] = datetime.now()

            # 连续签到奖励
            bonuses = rule.continuous_bonus or {}
            if continuous_days >= 30 and continuous_days % 30 == 1:
                bonus = bonuses.get("30_days", {}).get("bonus", 50)
                points += bonus
            elif continuous_days >= 7 and continuous_days % 7 == 1:
                bonus = bonuses.get("7_days", {}).get("bonus", 10)
                points += bonus

        # 更新计数
        self._daily_counts[user_id][action] = today_count + 1

        # 更新余额
        balance_before = self._user_points[user_id]
        self._user_points[user_id] = balance_before + points

        # 记录历史
        history_item = PointsHistoryItem(
            id=len(self._user_history[user_id]) + 1,
            user_id=user_id,
            action=action,
            points=points,
            balance_after=self._user_points[user_id],
            description=description or f"奖励: {rule.description}",
            created_at=datetime.now(),
            metadata=metadata,
        )
        self._user_history[user_id].append(history_item)

        logger.info(f"用户 {user_id} 获得 {points} 积分 (动作: {action})")

        return points, None

    async def redeem_points(
        self,
        user_id: int,
        points: int,
        product_id: str,
        description: str,
    ) -> tuple[bool, Optional[str]]:
        """消耗积分

        Returns:
            (是否成功, 错误信息)
        """
        if user_id not in self._user_points:
            return False, "用户不存在"

        if self._user_points[user_id] < points:
            return False, f"积分不足，需要 {points} 积分，当前余额 {self._user_points[user_id]}"

        # 扣减积分
        balance_before = self._user_points[user_id]
        self._user_points[user_id] = balance_before - points

        # 记录历史
        if user_id not in self._user_history:
            self._user_history[user_id] = []

        history_item = PointsHistoryItem(
            id=len(self._user_history[user_id]) + 1,
            user_id=user_id,
            action="redeem",
            points=-points,
            balance_after=self._user_points[user_id],
            description=description,
            metadata={"product_id": product_id},
            created_at=datetime.now(),
        )
        self._user_history[user_id].append(history_item)

        logger.info(f"用户 {user_id} 消耗 {points} 积分 (商品: {product_id})")

        return True, None

    def get_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[PointsHistoryItem]:
        """获取积分历史"""
        if user_id not in self._user_history:
            return []

        return self._user_history[user_id][offset:offset + limit]

    def get_daily_stats(self, user_id: int) -> Dict[str, int]:
        """获取今日统计"""
        if user_id not in self._daily_counts:
            return {}

        return self._daily_counts[user_id]

    def get_continuous_days(self, user_id: int) -> int:
        """获取连续签到天数"""
        return self._continuous_days.get(user_id, 0)

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

    def get_leaderboard(self, top_k: int = 100) -> List[Dict[str, Any]]:
        """获取积分排行榜"""
        sorted_users = sorted(
            self._user_points.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        leaderboard: list[dict[str, Any]] = []
        for rank, (user_id, balance) in enumerate(sorted_users[:top_k], 1):
            leaderboard.append({
                "rank": rank,
                "user_id": user_id,
                "balance": balance,
                "continuous_days": self._continuous_days.get(user_id, 0),
            })

        return leaderboard

    def reset_daily_counts(self) -> None:
        """重置每日计数（用于每日任务）"""
        self._daily_counts.clear()
        logger.info("每日积分计数已重置")


# 积分服务单例
_points_service: Optional[PointsService] = None


def get_points_service() -> PointsService:
    """获取积分服务单例"""
    global _points_service
    if _points_service is None:
        _points_service = PointsService()
    return _points_service


# 便捷函数
async def award_points(
    user_id: int,
    action: str,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> tuple[int, Optional[str]]:
    """奖励积分的便捷函数"""
    service = get_points_service()
    return await service.award_points(user_id, action, description, metadata)


async def redeem_points(
    user_id: int,
    points: int,
    product_id: str,
    description: str,
) -> tuple[bool, Optional[str]]:
    """消耗积分的便捷函数"""
    service = get_points_service()
    return await service.redeem_points(user_id, points, product_id, description)


def get_balance(user_id: int) -> int:
    """获取积分余额"""
    service = get_points_service()
    return service.get_balance(user_id)


@dataclass
class PointsSummary:
    total_points: int
    available_points: int
    frozen_points: int


@dataclass
class PointsHistoryList:
    items: list[PointsHistory]
    total: int
    page: int
    page_size: int


class PointsServiceFacade:
    """测试兼容的 DB 外观服务"""

    async def _get_or_create_user(
            self, db: AsyncSession, user_id: int) -> PointsUser:
        result = await db.execute(select(PointsUser).where(PointsUser.user_id == int(user_id)))
        user = result.scalar_one_or_none()
        if user is None:
            user = PointsUser(
                user_id=int(user_id),
                balance=0,
                total_earned=0,
                total_spent=0)
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    async def get_user_points(self, db: AsyncSession,
                              user_id: int) -> PointsSummary:
        user = await self._get_or_create_user(db, int(user_id))
        total = int(getattr(user, "balance", 0) or 0)
        return PointsSummary(total_points=total,
                             available_points=total, frozen_points=0)

    async def award_points(
        self,
        db: AsyncSession,
        user_id: int,
        amount: int,
        reason: str | None = None,
        source: str | None = None,
    ) -> bool:
        user = await self._get_or_create_user(db, int(user_id))
        before = int(getattr(user, "balance", 0) or 0)
        setattr(user, "balance", before + int(amount))
        total_earned = int(getattr(user, "total_earned", 0) or 0) + int(amount)
        setattr(user, "total_earned", total_earned)
        history = PointsHistory(
            user_id=int(user_id),
            action=str(source or "award"),
            points=int(amount),
            balance_before=before,
            balance_after=int(getattr(user, "balance", 0) or 0),
            description=reason,
            metadata_json={"source": source} if source else None,
        )
        db.add(history)
        await db.commit()
        return True

    async def deduct_points(
        self,
        db: AsyncSession,
        user_id: int,
        amount: int,
        reason: str | None = None,
        order_no: str | None = None,
    ) -> bool:
        user = await self._get_or_create_user(db, int(user_id))
        before = int(getattr(user, "balance", 0) or 0)
        if before < int(amount):
            return False
        setattr(user, "balance", before - int(amount))
        total_spent = int(getattr(user, "total_spent", 0) or 0) + int(amount)
        setattr(user, "total_spent", total_spent)
        history = PointsHistory(
            user_id=int(user_id),
            action="deduct",
            points=-int(amount),
            balance_before=before,
            balance_after=int(getattr(user, "balance", 0) or 0),
            description=reason,
            metadata_json={"order_no": order_no} if order_no else None,
        )
        db.add(history)
        await db.commit()
        return True

    async def get_points_history(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> PointsHistoryList:
        total = int(
            (await db.execute(select(func.count(PointsHistory.id)).where(PointsHistory.user_id == int(user_id))))
            .scalar()
            or 0
        )
        result = await db.execute(
            select(PointsHistory)
            .where(PointsHistory.user_id == int(user_id))
            .order_by(PointsHistory.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        return PointsHistoryList(
            items=items, total=total, page=page, page_size=page_size)

    async def check_expired_points(
            self, db: AsyncSession, user_id: int) -> int:
        await self._get_or_create_user(db, int(user_id))
        return 0

    async def transfer_points(
        self,
        db: AsyncSession,
        *,
        from_user_id: int,
        to_user_id: int,
        amount: int,
        remark: str | None = None,
    ) -> bool:
        if int(amount) <= 0:
            return False
        from_user = await self._get_or_create_user(db, int(from_user_id))
        to_user = await self._get_or_create_user(db, int(to_user_id))
        if int(getattr(from_user, "balance", 0) or 0) < int(amount):
            return False
        from_before = int(getattr(from_user, "balance", 0) or 0)
        to_before = int(getattr(to_user, "balance", 0) or 0)
        setattr(from_user, "balance", from_before - int(amount))
        setattr(to_user, "balance", to_before + int(amount))
        db.add(
            PointsHistory(
                user_id=int(from_user_id),
                action="transfer_out",
                points=-int(amount),
                balance_before=from_before,
                balance_after=int(getattr(from_user, "balance", 0) or 0),
                description=remark,
                metadata_json={"to_user_id": int(to_user_id)},
            )
        )
        db.add(
            PointsHistory(
                user_id=int(to_user_id),
                action="transfer_in",
                points=int(amount),
                balance_before=to_before,
                balance_after=int(getattr(to_user, "balance", 0) or 0),
                description=remark,
                metadata_json={"from_user_id": int(from_user_id)},
            )
        )
        await db.commit()
        return True


points_service = PointsServiceFacade()
