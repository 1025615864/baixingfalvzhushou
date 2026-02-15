"""用户行为分析服务核心模块

提供用户行为日志记录功能，支持页面浏览、点击、提交、搜索等行为追踪。

包含：
- AnalyticsService: 用户行为分析服务
"""

from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.analytics import UserBehaviorLog


class AnalyticsService:
    """用户行为分析服务"""

    # 行为类型常量
    ACTION_PAGE_VIEW = "page_view"  # 页面浏览
    ACTION_CLICK = "click"  # 点击
    ACTION_SUBMIT = "submit"  # 提交
    ACTION_SEARCH = "search"  # 搜索
    ACTION_DOWNLOAD = "download"  # 下载
    ACTION_SHARE = "share"  # 分享
    ACTION_FAVORITE = "favorite"  # 收藏
    ACTION_COMMENT = "comment"  # 评论
    ACTION_LIKE = "like"  # 点赞
    ACTION_PURCHASE = "purchase"  # 购买
    ACTION_REGISTER = "register"  # 注册
    ACTION_LOGIN = "login"  # 登录
    ACTION_LOGOUT = "logout"  # 登出

    # 资源类型常量
    RESOURCE_POST = "post"  # 帖子
    RESOURCE_CONSULTATION = "consultation"  # 咨询
    RESOURCE_LAWYER = "lawyer"  # 律师
    RESOURCE_NEWS = "news"  # 新闻
    RESOURCE_KNOWLEDGE = "knowledge"  # 知识库
    RESOURCE_CONTRACT = "contract"  # 合同
    RESOURCE_DOCUMENT = "document"  # 文档
    RESOURCE_PAYMENT = "payment"  # 支付
    RESOURCE_ORDER = "order"  # 订单

    async def log_behavior(
        self,
        db: AsyncSession,
        user_id: int | None,
        action: str,
        resource_type: str | None = None,
        resource_id: int | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        referrer: str | None = None,
        session_id: str | None = None,
    ) -> UserBehaviorLog:
        """
        记录用户行为日志

        Args:
            db: 数据库会话
            user_id: 用户ID，可为空（未登录用户）
            action: 行为类型
            resource_type: 资源类型
            resource_id: 资源ID
            metadata: 额外元数据，JSON格式
            ip_address: IP地址
            user_agent: 用户代理
            referrer: 来源页面
            session_id: 会话ID

        Returns:
            UserBehaviorLog: 创建的行为日志记录
        """
        import json

        log = UserBehaviorLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=json.dumps(metadata) if metadata else None,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            session_id=session_id,
            created_at=datetime.now(timezone.utc),
        )

        db.add(log)
        await db.flush()
        await db.refresh(log)

        return log

    async def get_user_behavior_history(
        self,
        db: AsyncSession,
        user_id: int,
        action: str | None = None,
        resource_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserBehaviorLog]:
        """
        获取用户行为历史

        Args:
            db: 数据库会话
            user_id: 用户ID
            action: 行为类型过滤
            resource_type: 资源类型过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            list[UserBehaviorLog]: 行为日志列表
        """
        query = select(UserBehaviorLog).where(
            UserBehaviorLog.user_id == user_id)

        if action:
            query = query.where(UserBehaviorLog.action == action)

        if resource_type:
            query = query.where(UserBehaviorLog.resource_type == resource_type)

        query = query.order_by(
            UserBehaviorLog.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_resource_view_count(
        self,
        db: AsyncSession,
        resource_type: str,
        resource_id: int,
    ) -> int:
        """
        获取资源浏览次数

        Args:
            db: 数据库会话
            resource_type: 资源类型
            resource_id: 资源ID

        Returns:
            int: 浏览次数
        """
        query = select(UserBehaviorLog).where(
            UserBehaviorLog.resource_type == resource_type,
            UserBehaviorLog.resource_id == resource_id,
            UserBehaviorLog.action == self.ACTION_PAGE_VIEW,
        )

        result = await db.execute(query)
        return len(result.scalars().all())

    async def get_user_session_activities(
        self,
        db: AsyncSession,
        session_id: str,
        limit: int = 50,
    ) -> list[UserBehaviorLog]:
        """
        获取会话活动记录

        Args:
            db: 数据库会话
            session_id: 会话ID
            limit: 返回数量限制

        Returns:
            list[UserBehaviorLog]: 行为日志列表
        """
        query = (
            select(UserBehaviorLog)
            .where(UserBehaviorLog.session_id == session_id)
            .order_by(UserBehaviorLog.created_at.asc())
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_daily_active_users(
        self,
        db: AsyncSession,
        date: datetime,
    ) -> int:
        """
        获取日活跃用户数

        Args:
            db: 数据库会话
            date: 日期

        Returns:
            int: 日活跃用户数
        """
        start_of_day = datetime(
            date.year,
            date.month,
            date.day,
            tzinfo=timezone.utc)
        end_of_day = datetime(
            date.year,
            date.month,
            date.day,
            23,
            59,
            59,
            tzinfo=timezone.utc)

        query = (
            select(UserBehaviorLog.user_id)
            .where(
                UserBehaviorLog.created_at >= start_of_day,
                UserBehaviorLog.created_at <= end_of_day,
                UserBehaviorLog.user_id.isnot(None),
            )
            .distinct()
        )

        result = await db.execute(query)
        return len(result.scalars().all())

    async def get_action_statistics(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        action: str | None = None,
    ) -> dict[str, int]:
        """
        获取行为统计

        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            action: 行为类型过滤

        Returns:
            dict[str, int]: 行为统计，key为行为类型，value为次数
        """
        query = select(UserBehaviorLog.action).where(
            UserBehaviorLog.created_at >= start_date,
            UserBehaviorLog.created_at <= end_date,
        )

        if action:
            query = query.where(UserBehaviorLog.action == action)

        result = await db.execute(query)
        actions = result.scalars().all()

        stats: dict[str, int] = {}
        for act in actions:
            stats[act] = stats.get(act, 0) + 1

        return stats

    async def get_conversion_funnel(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        funnel_steps: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        获取用户转化漏斗分析

        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            funnel_steps: 漏斗步骤列表，每个步骤包含：
                - name: 步骤名称
                - action: 行为类型
                - resource_type: 资源类型（可选）
                - condition: 额外条件（可选）

        Returns:
            list[dict[str, Any]]: 漏斗分析结果，每个步骤包含：
                - name: 步骤名称
                - count: 用户数
                - conversion_rate: 转化率（相对于第一步）
                - drop_rate: 流失率
        """
        results: list[dict[str, Any]] = []

        # 获取第一步的用户数
        first_step = funnel_steps[0]
        first_step_users = await self._get_step_users(
            db=db,
            start_date=start_date,
            end_date=end_date,
            action=first_step.get("action"),
            resource_type=first_step.get("resource_type"),
            condition=first_step.get("condition"),
        )
        first_count = len(first_step_users)

        for i, step in enumerate(funnel_steps):
            step_users = await self._get_step_users(
                db=db,
                start_date=start_date,
                end_date=end_date,
                action=step.get("action"),
                resource_type=step.get("resource_type"),
                condition=step.get("condition"),
            )
            count = len(step_users)

            # 计算转化率（相对于第一步）
            conversion_rate = (
                count /
                first_count *
                100) if first_count > 0 else 0

            # 计算流失率
            drop_rate = 0
            if i > 0:
                prev_count = results[i - 1]["count"]
                drop_rate = ((prev_count - count) / prev_count *
                             100) if prev_count > 0 else 0

            results.append({
                "name": step.get("name", f"步骤{i + 1}"),
                "count": count,
                "conversion_rate": round(conversion_rate, 2),
                "drop_rate": round(drop_rate, 2),
            })

        return results

    async def _get_step_users(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        action: str | None = None,
        resource_type: str | None = None,
        condition: dict[str, Any] | None = None,
    ) -> set[int]:
        """
        获取满足条件的用户ID集合

        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            action: 行为类型
            resource_type: 资源类型
            condition: 额外条件

        Returns:
            set[int]: 用户ID集合
        """
        query = select(UserBehaviorLog.user_id).where(
            UserBehaviorLog.created_at >= start_date,
            UserBehaviorLog.created_at <= end_date,
            UserBehaviorLog.user_id.isnot(None),
        )

        if action:
            query = query.where(UserBehaviorLog.action == action)

        if resource_type:
            query = query.where(UserBehaviorLog.resource_type == resource_type)

        result = await db.execute(query)
        user_ids = result.scalars().all()

        return {int(uid) for uid in user_ids if uid is not None}

    async def get_user_retention(
        self,
        db: AsyncSession,
        cohort_date: datetime,
        retention_days: list[int],
    ) -> list[dict[str, Any]]:
        """
        获取用户留存分析

        Args:
            db: 数据库会话
            cohort_date: 队列日期
            retention_days: 留存天数列表，如 [1, 7, 30]

        Returns:
            list[dict[str, Any]]: 留存分析结果，每个项包含：
                - day: 留存天数
                - count: 留存用户数
                - rate: 留存率
        """
        # 获取队列日期当天的新用户
        start_of_day = datetime(
            cohort_date.year,
            cohort_date.month,
            cohort_date.day,
            tzinfo=timezone.utc)
        end_of_day = datetime(
            cohort_date.year,
            cohort_date.month,
            cohort_date.day,
            23,
            59,
            59,
            tzinfo=timezone.utc)

        # 获取当天注册的用户
        from ...models.user import User
        query = select(User.id).where(
            User.created_at >= start_of_day,
            User.created_at <= end_of_day,
        )
        result = await db.execute(query)
        cohort_users = {int(uid) for uid in result.scalars().all()}

        cohort_count = len(cohort_users)
        if cohort_count == 0:
            return []

        results: list[dict[str, Any]] = []

        for day in retention_days:
            # 计算留存日期范围
            retention_start = start_of_day + timedelta(days=day)
            retention_end = retention_start.replace(
                hour=23, minute=59, second=59)

            # 获取留存用户
            query = select(UserBehaviorLog.user_id).where(
                UserBehaviorLog.user_id.in_(cohort_users),
                UserBehaviorLog.created_at >= retention_start,
                UserBehaviorLog.created_at <= retention_end,
            )
            result = await db.execute(query)
            retained_users = {
                int(uid) for uid in result.scalars().all() if uid is not None}

            retained_count = len(retained_users)
            retention_rate = (
                retained_count /
                cohort_count *
                100) if cohort_count > 0 else 0

            results.append({
                "day": day,
                "count": retained_count,
                "rate": round(retention_rate, 2),
            })

        return results
