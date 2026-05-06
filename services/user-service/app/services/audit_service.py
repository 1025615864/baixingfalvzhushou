"""审计日志服务"""
import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """审计日志服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        user_id: Optional[int] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        details: Optional[dict] = None,
    ) -> bool:
        """记录审计日志

        Args:
            action: 动作类型
            user_id: 用户ID
            resource: 资源类型
            resource_id: 资源ID
            ip_address: IP地址
            user_agent: User-Agent
            status: 状态 (success/failed)
            details: 详情字典

        Returns:
            是否记录成功
        """
        try:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                details=json.dumps(details, ensure_ascii=False) if details else None,
            )
            self.db.add(audit)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            await self.db.rollback()
            return False

    async def log_login(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
    ):
        """记录登录日志"""
        action = "login" if success else "login_failed"
        details = {"failure_reason": failure_reason} if failure_reason else None
        return await self.log(
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success" if success else "failed",
            details=details,
        )

    async def log_register(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """记录注册日志"""
        return await self.log(
            action="register",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_password_change(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """记录密码修改日志"""
        return await self.log(
            action="password_change",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_membership_change(
        self,
        user_id: int,
        action: str,
        old_level: Optional[str] = None,
        new_level: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """记录会员变更日志"""
        details = {"old_level": old_level, "new_level": new_level}
        return await self.log(
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
        )

    async def log_token_refresh(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
    ):
        """记录Token刷新日志"""
        return await self.log(
            action="token_refresh",
            user_id=user_id,
            ip_address=ip_address,
        )

    async def log_token_revoke(
        self,
        user_id: int,
        revoke_type: str = "all",
        ip_address: Optional[str] = None,
    ):
        """记录Token撤销日志"""
        return await self.log(
            action="token_revoke",
            user_id=user_id,
            ip_address=ip_address,
            details={"revoke_type": revoke_type},
        )

    async def log_profile_update(
        self,
        user_id: int,
        changed_fields: list[str],
        ip_address: Optional[str] = None,
    ):
        """记录用户资料更新日志"""
        return await self.log(
            action="profile_update",
            user_id=user_id,
            resource="user_profile",
            ip_address=ip_address,
            details={"changed_fields": changed_fields},
        )

    async def log_account_delete(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        deleted_by: Optional[int] = None,
    ):
        """记录账号删除日志"""
        return await self.log(
            action="account_delete",
            user_id=user_id,
            ip_address=ip_address,
            details={"deleted_by": deleted_by},
        )

    async def log_role_change(
        self,
        user_id: int,
        old_role: str,
        new_role: str,
        admin_id: int,
        ip_address: Optional[str] = None,
    ):
        """记录角色变更日志"""
        return await self.log(
            action="role_change",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "old_role": old_role,
                "new_role": new_role,
                "admin_id": admin_id,
            },
        )


audit_service = AuditService
