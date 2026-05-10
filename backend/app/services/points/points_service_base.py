"""Points service base."""
from __future__ import annotations
import enum
from typing import Optional, Any
from dataclasses import dataclass, field


class PointsAction(enum.Enum):
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
    SIGN_IN = "sign_in"
    CONSULTATION = "consultation"
    SHARE = "share"
    INVITE = "invite"
    PURCHASE = "purchase"


@dataclass
class PointsRule:
    action: PointsAction
    points: int
    max_daily: int = 1
    description: str = ""
    continuous_bonus: Optional[dict[str, Any]] = None
    requires_auth: bool = False
    vip_multiplier: float = 1.0


POINTS_RULES: dict[PointsAction, PointsRule] = {
    PointsAction.DAILY_SIGNIN: PointsRule(action=PointsAction.DAILY_SIGNIN, points=5, max_daily=1, description="每日签到"),
    PointsAction.AI_CONSULTATION: PointsRule(action=PointsAction.AI_CONSULTATION, points=3, max_daily=10, description="AI咨询"),
    PointsAction.POST_CREATED: PointsRule(action=PointsAction.POST_CREATED, points=10, max_daily=5, description="发布帖子"),
    PointsAction.COMMENT_CREATED: PointsRule(action=PointsAction.COMMENT_CREATED, points=5, max_daily=20, description="发表评论"),
    PointsAction.SHARE_CONTENT: PointsRule(action=PointsAction.SHARE_CONTENT, points=3, max_daily=10, description="分享内容"),
    PointsAction.DOCUMENT_GENERATED: PointsRule(action=PointsAction.DOCUMENT_GENERATED, points=2, max_daily=10, description="生成文档"),
    PointsAction.LAWYER_BOOKING: PointsRule(action=PointsAction.LAWYER_BOOKING, points=15, max_daily=3, description="预约律师"),
    PointsAction.INVITE_FRIEND: PointsRule(action=PointsAction.INVITE_FRIEND, points=50, max_daily=5, description="邀请好友"),
    PointsAction.FAVORITE_POST: PointsRule(action=PointsAction.FAVORITE_POST, points=2, max_daily=10, description="收藏帖子"),
    PointsAction.COMPLETE_PROFILE: PointsRule(action=PointsAction.COMPLETE_PROFILE, points=20, max_daily=1, description="完善资料"),
    PointsAction.FIRST_QUESTION: PointsRule(action=PointsAction.FIRST_QUESTION, points=10, max_daily=1, description="首次提问"),
}


def get_vip_multiplier(level: int) -> float:
    multipliers = {1: 1.0, 2: 1.2, 3: 1.5, 4: 2.0, 5: 3.0}
    return multipliers.get(level, 1.0)


def get_points_rule(action: PointsAction) -> Optional[PointsRule]:
    return POINTS_RULES.get(action)


@dataclass
class PointsAccount:
    user_id: int
    balance: int = 0
    total_earned: int = 0
    total_spent: int = 0
    level: int = 1


@dataclass
class PointsTransaction:
    id: str
    user_id: int
    action: PointsAction
    amount: int
    description: Optional[str] = None
    balance_after: int = 0


class PointsServiceBase:
    ACTION_POINTS = {
        PointsAction.SIGN_IN: 10,
        PointsAction.CONSULTATION: 5,
        PointsAction.SHARE: 3,
        PointsAction.INVITE: 50,
        PointsAction.PURCHASE: 0,
    }

    def __init__(self):
        self._accounts: dict[int, PointsAccount] = {}
        self._transactions: list[PointsTransaction] = []
        self._next_txn_id = 1

    def get_or_create_account(self, user_id: int) -> PointsAccount:
        if user_id not in self._accounts:
            self._accounts[user_id] = PointsAccount(user_id=user_id)
        return self._accounts[user_id]

    def get_balance(self, user_id: int) -> int:
        account = self.get_or_create_account(user_id)
        return account.balance

    def add_points(self, user_id: int, action: PointsAction, amount: Optional[int] = None, description: Optional[str] = None) -> PointsTransaction:
        account = self.get_or_create_account(user_id)
        pts = amount if amount is not None else self.ACTION_POINTS.get(action, 0)
        account.balance += pts
        account.total_earned += pts
        txn = PointsTransaction(
            id=f"txn_{self._next_txn_id}", user_id=user_id,
            action=action, amount=pts, description=description,
            balance_after=account.balance,
        )
        self._next_txn_id += 1
        self._transactions.append(txn)
        return txn

    def deduct_points(self, user_id: int, amount: int, description: Optional[str] = None) -> PointsTransaction:
        account = self.get_or_create_account(user_id)
        if account.balance < amount:
            raise ValueError("积分不足")
        account.balance -= amount
        account.total_spent += amount
        txn = PointsTransaction(
            id=f"txn_{self._next_txn_id}", user_id=user_id,
            action=PointsAction.PURCHASE, amount=-amount, description=description,
            balance_after=account.balance,
        )
        self._next_txn_id += 1
        self._transactions.append(txn)
        return txn

    def get_transactions(self, user_id: int, limit: int = 20) -> list[PointsTransaction]:
        return [t for t in self._transactions if t.user_id == user_id][-limit:]

    def get_level(self, user_id: int) -> int:
        account = self.get_or_create_account(user_id)
        if account.total_earned >= 10000:
            return 5
        elif account.total_earned >= 5000:
            return 4
        elif account.total_earned >= 1000:
            return 3
        elif account.total_earned >= 100:
            return 2
        return 1
