"""积分服务基础定义

包含积分动作枚举、规则配置等。
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import dataclass
from enum import Enum


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


async def get_vip_multiplier(user_id: int, db: AsyncSession) -> float:
    """获取用户 VIP 加成倍率

    根据用户的 vip_expires_at 字段判断是否为 VIP 用户
    如果是 VIP 用户，返回配置的倍率；否则返回 1.0

    Args:
        user_id: 用户 ID
        db: 数据库会话

    Returns:
        VIP 倍率（VIP 用户返回 2.0，普通用户返回 1.0）
    """
    from sqlalchemy import select
    from datetime import datetime, timezone

    from ...models.user import User

    result = await db.execute(
        select(User.vip_expires_at).where(User.id == user_id)
    )
    vip_expires = result.scalar_one_or_none()

    if vip_expires is None:
        return 1.0

    # 检查 VIP 是否过期
    if vip_expires.tzinfo is None:
        # 如果没有时区信息，假设为 UTC
        vip_expires = vip_expires.replace(tzinfo=timezone.utc)

    if vip_expires <= datetime.now(timezone.utc):
        return 1.0

    return 2.0  # VIP 用户获得 2 倍积分


def get_points_rule(action: str) -> Optional[PointsRule]:
    """获取积分规则"""
    return POINTS_RULES.get(action)
