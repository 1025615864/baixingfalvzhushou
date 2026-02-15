"""积分服务整合模块

统一积分服务接口，整合内存版和数据库版服务。

功能:
    - 统一积分操作接口
    - 支持数据库持久化
    - 积分规则管理
    - 签到功能
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .points.points_service_base import (
    PointsAction,
    PointsRule,
    POINTS_RULES,
    get_vip_multiplier,
    get_points_rule,
)
from .points.points_service_db import PointsServiceDB

logger = logging.getLogger("points")


class PointsManager:
    """积分管理器

    统一积分服务入口，支持积分获取、消耗、查询等功能。

    Attributes:
        db_service: 数据库服务
    """

    def __init__(self):
        self.db_service = PointsServiceDB()

    async def award_points(
        self,
        db: AsyncSession,
        user_id: int,
        action: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """发放积分

        Args:
            db: 数据库会话
            user_id: 用户ID
            action: 积分动作
            description: 描述

        Returns:
            发放结果
        """
        return await self.db_service.award_points_db(
            db=db,
            user_id=user_id,
            action=action,
            description=description,
        )

    async def redeem_points(
        self,
        db: AsyncSession,
        user_id: int,
        action: str,
        amount: int,
        description: str | None = None,
    ) -> dict[str, Any]:
        """兑换积分

        Args:
            db: 数据库会话
            user_id: 用户ID
            action: 兑换动作
            amount: 兑换积分数
            description: 描述

        Returns:
            兑换结果
        """
        return await self.db_service.redeem_points_db(
            db=db,
            user_id=user_id,
            action=action,
            amount=amount,
            description=description,
        )

    async def get_balance(self, db: AsyncSession, user_id: int) -> dict[str, Any]:
        """查询积分余额

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            余额信息
        """
        return await self.db_service.get_balance_db(db=db, user_id=user_id)

    async def get_history(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """查询积分历史

        Args:
            db: 数据库会话
            user_id: 用户ID
            limit: 限制
            offset: 偏移

        Returns:
            历史记录
        """
        return await self.db_service.get_points_history(
            db=db, user_id=user_id, limit=limit, offset=offset
        )

    async def daily_signin(self, db: AsyncSession, user_id: int) -> dict[str, Any]:
        """每日签到

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            签到结果
        """
        return await self.db_service.daily_signin(db=db, user_id=user_id)


_points_manager: PointsManager | None = None


def get_points_manager() -> PointsManager:
    """获取积分管理器单例"""
    global _points_manager
    if _points_manager is None:
        _points_manager = PointsManager()
    return _points_manager


async def award_points(
    db: AsyncSession,
    user_id: int,
    action: str,
    description: str | None = None,
) -> dict[str, Any]:
    """便捷函数：发放积分"""
    manager = get_points_manager()
    return await manager.award_points(db, user_id, action, description)


async def redeem_points(
    db: AsyncSession,
    user_id: int,
    action: str,
    amount: int,
    description: str | None = None,
) -> dict[str, Any]:
    """便捷函数：兑换积分"""
    manager = get_points_manager()
    return await manager.redeem_points(db, user_id, action, amount, description)


async def get_points_balance(db: AsyncSession, user_id: int) -> dict[str, Any]:
    """便捷函数：查询积分余额"""
    manager = get_points_manager()
    return await manager.get_balance(db, user_id)


async def daily_signin(db: AsyncSession, user_id: int) -> dict[str, Any]:
    """便捷函数：每日签到"""
    manager = get_points_manager()
    return await manager.daily_signin(db, user_id)


def get_points_rules() -> dict[str, PointsRule]:
    """获取积分规则"""
    return POINTS_RULES


def get_points_rule(action: str) -> PointsRule | None:
    """获取指定积分规则"""
    return POINTS_RULES.get(action)


def get_vip_bonus_multiplier(vip_level: int) -> float:
    """获取VIP加成倍数"""
    return get_vip_multiplier(vip_level)
