"""登录审计服务"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user_security import LoginAudit, LoginAction


class LoginAuditService:
    """登录审计服务"""

    @staticmethod
    async def log_login(
        db: AsyncSession,
        user_id: int,
        success: bool,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_id: str | None = None,
        location: str | None = None,
        failure_reason: str | None = None
    ) -> LoginAudit:
        """记录登录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            success: 是否成功
            ip_address: IP地址
            user_agent: 用户代理
            device_id: 设备ID
            location: 地理位置
            failure_reason: 失败原因
            
        Returns:
            LoginAudit: 创建的审计记录
        """
        audit = LoginAudit(
            user_id=user_id,
            action=LoginAction.LOGIN,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            location=location,
            success=success,
            failure_reason=failure_reason
        )
        
        db.add(audit)
        await db.commit()
        await db.refresh(audit)
        return audit

    @staticmethod
    async def log_logout(
        db: AsyncSession,
        user_id: int,
        device_id: str | None = None
    ) -> LoginAudit:
        """记录登出
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            device_id: 设备ID
            
        Returns:
            LoginAudit: 创建的审计记录
        """
        audit = LoginAudit(
            user_id=user_id,
            action=LoginAction.LOGOUT,
            device_id=device_id,
            success=True
        )
        
        db.add(audit)
        await db.commit()
        await db.refresh(audit)
        return audit

    @staticmethod
    async def log_2fa_verify(
        db: AsyncSession,
        user_id: int,
        success: bool,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_id: str | None = None,
        failure_reason: str | None = None
    ) -> LoginAudit:
        """记录2FA验证
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            success: 是否成功
            ip_address: IP地址
            user_agent: 用户代理
            device_id: 设备ID
            failure_reason: 失败原因
            
        Returns:
            LoginAudit: 创建的审计记录
        """
        audit = LoginAudit(
            user_id=user_id,
            action=LoginAction.TWO_FA_VERIFY,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            success=success,
            failure_reason=failure_reason
        )
        
        db.add(audit)
        await db.commit()
        await db.refresh(audit)
        return audit

    @staticmethod
    async def log_failed_attempt(
        db: AsyncSession,
        user_id: int | None,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        failure_reason: str | None = None
    ) -> LoginAudit:
        """记录登录失败
        
        Args:
            db: 数据库会话
            user_id: 用户ID（可能未知）
            ip_address: IP地址
            user_agent: 用户代理
            failure_reason: 失败原因
            
        Returns:
            LoginAudit: 创建的审计记录
        """
        audit = LoginAudit(
            user_id=user_id or 0,  # 如果未知用户使用 0
            action=LoginAction.FAILED,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            failure_reason=failure_reason
        )
        
        db.add(audit)
        await db.commit()
        await db.refresh(audit)
        return audit

    @staticmethod
    async def log_password_change(
        db: AsyncSession,
        user_id: int,
        success: bool,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_id: str | None = None,
        failure_reason: str | None = None
    ) -> LoginAudit:
        """记录密码修改
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            success: 是否成功
            ip_address: IP地址
            user_agent: 用户代理
            device_id: 设备ID
            failure_reason: 失败原因
            
        Returns:
            LoginAudit: 创建的审计记录
        """
        audit = LoginAudit(
            user_id=user_id,
            action=LoginAction.PASSWORD_CHANGE,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            success=success,
            failure_reason=failure_reason
        )
        
        db.add(audit)
        await db.commit()
        await db.refresh(audit)
        return audit

    @staticmethod
    async def get_login_history(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        *,
        action: LoginAction | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> tuple[list[LoginAudit], int]:
        """查询登录历史
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            action: 操作类型筛选
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            tuple[list[LoginAudit], int]: (记录列表, 总数)
        """
        # 构建基础查询
        query = select(LoginAudit).where(LoginAudit.user_id == user_id)
        
        # 添加筛选条件
        if action:
            query = query.where(LoginAudit.action == action)
        
        if start_date:
            query = query.where(LoginAudit.created_at >= start_date)
        
        if end_date:
            query = query.where(LoginAudit.created_at <= end_date)
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页和排序
        query = query.order_by(desc(LoginAudit.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        records = list(result.scalars().all())
        
        return records, int(total)

    @staticmethod
    async def get_recent_failures(
        db: AsyncSession,
        user_id: int,
        minutes: int = 30
    ) -> list[LoginAudit]:
        """获取最近的登录失败记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            minutes: 时间范围（分钟）
            
        Returns:
            list[LoginAudit]: 失败记录列表
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        result = await db.execute(
            select(LoginAudit)
            .where(
                LoginAudit.user_id == user_id,
                LoginAudit.action == LoginAction.FAILED,
                LoginAudit.success == False,
                LoginAudit.created_at >= cutoff_time
            )
            .order_by(desc(LoginAudit.created_at))
        )
        
        return list(result.scalars().all())

    @staticmethod
    async def get_login_stats(
        db: AsyncSession,
        user_id: int,
        days: int = 30
    ) -> dict[str, Any]:
        """获取登录统计
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            dict[str, Any]: 统计数据
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # 总登录次数
        total_result = await db.execute(
            select(func.count()).where(
                LoginAudit.user_id == user_id,
                LoginAudit.action == LoginAction.LOGIN,
                LoginAudit.created_at >= cutoff_time
            )
        )
        total_logins = total_result.scalar() or 0
        
        # 成功次数
        success_result = await db.execute(
            select(func.count()).where(
                LoginAudit.user_id == user_id,
                LoginAudit.action == LoginAction.LOGIN,
                LoginAudit.success == True,
                LoginAudit.created_at >= cutoff_time
            )
        )
        success_logins = success_result.scalar() or 0
        
        # 失败次数
        failed_result = await db.execute(
            select(func.count()).where(
                LoginAudit.user_id == user_id,
                LoginAudit.action == LoginAction.FAILED,
                LoginAudit.created_at >= cutoff_time
            )
        )
        failed_attempts = failed_result.scalar() or 0
        
        # 2FA验证次数
        twofa_result = await db.execute(
            select(func.count()).where(
                LoginAudit.user_id == user_id,
                LoginAudit.action == LoginAction.TWO_FA_VERIFY,
                LoginAudit.created_at >= cutoff_time
            )
        )
        twofa_count = twofa_result.scalar() or 0
        
        # 2FA成功次数
        twofa_success_result = await db.execute(
            select(func.count()).where(
                LoginAudit.user_id == user_id,
                LoginAudit.action == LoginAction.TWO_FA_VERIFY,
                LoginAudit.success == True,
                LoginAudit.created_at >= cutoff_time
            )
        )
        twofa_success = twofa_success_result.scalar() or 0
        
        return {
            "period_days": days,
            "total_logins": total_logins,
            "success_logins": success_logins,
            "failed_attempts": failed_attempts,
            "twofa_attempts": twofa_count,
            "twofa_success": twofa_success,
            "success_rate": (success_logins / total_logins * 100) if total_logins > 0 else 0
        }

    @staticmethod
    async def get_unique_devices_count(
        db: AsyncSession,
        user_id: int,
        days: int = 30
    ) -> int:
        """获取唯一设备数量
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            days: 时间范围（天数）
            
        Returns:
            int: 设备数量
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        result = await db.execute(
            select(func.count(func.distinct(LoginAudit.device_id))).where(
                LoginAudit.user_id == user_id,
                LoginAudit.device_id.isnot(None),
                LoginAudit.created_at >= cutoff_time
            )
        )
        
        return result.scalar() or 0

    @staticmethod
    async def cleanup_old_records(
        db: AsyncSession,
        user_id: int,
        days: int = 90
    ) -> int:
        """清理旧记录
        
        删除指定天数前的审计记录。
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            days: 保留天数
            
        Returns:
            int: 删除的记录数
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        result = await db.execute(
            select(LoginAudit).where(
                LoginAudit.user_id == user_id,
                LoginAudit.created_at < cutoff_time
            )
        )
        records = result.scalars().all()
        
        deleted_count = 0
        for record in records:
            await db.delete(record)
            deleted_count += 1
        
        if deleted_count > 0:
            await db.commit()
        
        return deleted_count


# 全局服务实例
login_audit_service = LoginAuditService()