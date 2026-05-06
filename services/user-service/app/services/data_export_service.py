"""个人数据导出服务 - 符合个人信息保护法要求"""
import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import User, UserProfile, LoginAudit, AuditLog

logger = logging.getLogger(__name__)


class DataExportService:
    """个人数据导出服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_user_data(self, user_id: int) -> Optional[dict]:
        """导出用户所有个人数据

        符合《个人信息保护法》要求，用户有权导出其个人数据。

        Returns:
            用户数据字典，包含:
            - basic_info: 基本信息
            - profile: 用户画像
            - account_info: 账号信息
            - activity_history: 活动历史摘要
            - exported_at: 导出时间
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        basic_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": self._mask_phone(user.phone) if user.phone else None,
            "nickname": user.nickname,
            "role": user.role,
            "status": user.status,
            "avatar": user.avatar,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }

        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()

        profile_data = None
        if profile:
            profile_data = {
                "bio": profile.bio,
                "gender": profile.gender,
                "birthday": profile.birthday.isoformat() if profile.birthday else None,
                "province": profile.province,
                "city": profile.city,
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
            }

        login_audit_result = await self.db.execute(
            select(LoginAudit)
            .where(LoginAudit.user_id == user_id)
            .order_by(LoginAudit.created_at.desc())
            .limit(100)
        )
        login_audits = login_audit_result.scalars().all()

        login_history = [
            {
                "event_type": audit.event_type,
                "ip_address": audit.ip_address,
                "success": audit.success,
                "created_at": audit.created_at.isoformat() if audit.created_at else None,
            }
            for audit in login_audits
        ]

        audit_result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(50)
        )
        audit_logs = audit_result.scalars().all()

        activity_summary = [
            {
                "action": log.action,
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in audit_logs
        ]

        return {
            "basic_info": basic_info,
            "profile": profile_data,
            "account_info": {
                "vip_expires_at": user.vip_expires_at.isoformat() if user.vip_expires_at else None,
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified,
            },
            "activity_history": {
                "login_records_count": len(login_history),
                "recent_logins": login_history[:10],
                "activity_records_count": len(activity_summary),
                "recent_activities": activity_summary[:20],
            },
            "export_info": {
                "exported_at": datetime.utcnow().isoformat(),
                "data_subject_id": user_id,
                "purpose": "个人数据导出请求",
                "legal_basis": "《个人信息保护法》第四十五条",
            },
        }

    async def export_as_json(self, user_id: int) -> Optional[str]:
        """导出为JSON格式"""
        data = await self.export_user_data(user_id)
        if not data:
            return None
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _mask_phone(self, phone: str) -> str:
        """手机号脱敏"""
        if not phone or len(phone) < 7:
            return "***"
        return phone[:3] + "****" + phone[-4:]

    async def get_data_summary(self, user_id: int) -> Optional[dict]:
        """获取数据摘要（用于导出前的预览）"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        login_count_result = await self.db.execute(
            select(LoginAudit).where(LoginAudit.user_id == user_id)
        )
        login_count = len(login_count_result.scalars().all())

        audit_count_result = await self.db.execute(
            select(AuditLog).where(AuditLog.user_id == user_id)
        )
        audit_count = len(audit_count_result.scalars().all())

        return {
            "user_id": user_id,
            "username": user.username,
            "has_email": bool(user.email),
            "has_phone": bool(user.phone),
            "login_records_count": login_count,
            "activity_records_count": audit_count,
            "account_created_at": user.created_at.isoformat() if user.created_at else None,
        }


data_export_service = DataExportService
