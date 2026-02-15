"""用户安全中心主服务"""
from __future__ import annotations

from datetime import datetime
from typing import NamedTuple, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user_security import UserSecuritySettings
from .totp_service import totp_service, TOTPSetupResult
from .device_manager import device_manager
from .login_audit_service import login_audit_service


class TwoFAStatus(NamedTuple):
    """2FA 状态"""
    is_enabled: bool
    is_setup: bool  # 是否已设置（有密钥但未启用）


class SecurityLevel(NamedTuple):
    """安全等级"""
    score: int  # 0-100
    level: str  # low, medium, high
    factors: dict[str, Any]


class UserSecurityService:
    """用户安全中心主服务"""

    def __init__(self) -> None:
        """初始化安全服务"""
        self.totp = totp_service
        self.device = device_manager
        self.audit = login_audit_service

    async def _get_or_create_settings(
        self,
        db: AsyncSession,
        user_id: int
    ) -> UserSecuritySettings:
        """获取或创建设置
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            UserSecuritySettings: 安全设置记录
        """
        result = await db.execute(
            select(UserSecuritySettings).where(
                UserSecuritySettings.user_id == user_id
            )
        )
        settings_obj = result.scalar_one_or_none()
        
        if not settings_obj:
            settings_obj = UserSecuritySettings(
                user_id=user_id,
                is_2fa_enabled=False,
                login_alert_enabled=True,
                unusual_activity_alert=True
            )
            db.add(settings_obj)
            await db.commit()
            await db.refresh(settings_obj)
        
        return settings_obj

    async def get_2fa_status(self, db: AsyncSession, user_id: int) -> TwoFAStatus:
        """获取2FA状态
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            TwoFAStatus: 2FA 状态
        """
        settings_obj = await self._get_or_create_settings(db, user_id)
        
        # 有密钥但未启用表示正在设置中
        is_setup = settings_obj.totp_secret is not None
        
        return TwoFAStatus(
            is_enabled=settings_obj.is_2fa_enabled,
            is_setup=is_setup
        )

    async def setup_2fa(
        self,
        db: AsyncSession,
        user_id: int,
        username: str
    ) -> TOTPSetupResult:
        """初始化2FA设置
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            username: 用户名
            
        Returns:
            TOTPSetupResult: 设置结果（包含密钥、URI、备用码）
        """
        settings_obj = await self._get_or_create_settings(db, user_id)
        
        # 生成新的 TOTP 密钥和备用码
        setup_result = self.totp.setup_totp(username)
        
        # 加密存储密钥
        encrypted_secret = self.totp.encrypt_secret(setup_result.secret)
        
        settings_obj.totp_secret = encrypted_secret
        settings_obj.backup_codes = setup_result.backup_codes
        settings_obj.updated_at = datetime.now()
        
        await db.commit()
        
        return setup_result

    async def verify_and_enable_2fa(
        self,
        db: AsyncSession,
        user_id: int,
        code: str
    ) -> bool:
        """验证并启用2FA
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            code: 验证码
            
        Returns:
            bool: 是否成功启用
        """
        settings_obj = await self._get_or_create_settings(db, user_id)
        
        if not settings_obj.totp_secret:
            return False
        
        # 解密密钥
        secret = self.totp.decrypt_secret(settings_obj.totp_secret)
        if not secret:
            return False
        
        # 验证验证码
        if not self.totp.verify_code(secret, code):
            return False
        
        # 启用 2FA
        settings_obj.is_2fa_enabled = True
        settings_obj.updated_at = datetime.now()
        
        await db.commit()
        return True

    async def disable_2fa(
        self,
        db: AsyncSession,
        user_id: int,
        code: str
    ) -> bool:
        """禁用2FA
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            code: 验证码
            
        Returns:
            bool: 是否成功禁用
        """
        settings_obj = await self._get_or_create_settings(db, user_id)
        
        if not settings_obj.is_2fa_enabled or not settings_obj.totp_secret:
            return False
        
        # 解密密钥
        secret = self.totp.decrypt_secret(settings_obj.totp_secret)
        if not secret:
            return False
        
        # 验证验证码
        if not self.totp.verify_code(secret, code):
            # 尝试备用码
            if not settings_obj.backup_codes or not self.totp.verify_backup_code(settings_obj.backup_codes, code):
                return False
            # 使用备用码成功，移除该备用码
            settings_obj.backup_codes = self.totp.remove_used_backup_code(settings_obj.backup_codes, code)
        
        # 禁用 2FA
        settings_obj.is_2fa_enabled = False
        settings_obj.totp_secret = None
        settings_obj.backup_codes = None
        settings_obj.updated_at = datetime.now()
        
        await db.commit()
        return True

    async def verify_2fa_code(self, db: AsyncSession, user_id: int, code: str) -> bool:
        """验证2FA码（登录时用）
        
        支持 TOTP 码和备用码。
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            code: 验证码
            
        Returns:
            bool: 验证是否成功
        """
        settings_obj = await self._get_or_create_settings(db, user_id)
        
        if not settings_obj.is_2fa_enabled or not settings_obj.totp_secret:
            return False
        
        # 解密密钥
        secret = self.totp.decrypt_secret(settings_obj.totp_secret)
        if not secret:
            return False
        
        # 先尝试验证 TOTP 码
        if self.totp.verify_code(secret, code):
            return True
        
        # 再尝试备用码
        if settings_obj.backup_codes and self.totp.verify_backup_code(settings_obj.backup_codes, code):
            # 使用备用码成功，移除该备用码
            settings_obj.backup_codes = self.totp.remove_used_backup_code(settings_obj.backup_codes, code)
            await db.commit()
            return True
        
        return False

    async def regenerate_backup_codes(
        self,
        db: AsyncSession,
        user_id: int,
        code: str
    ) -> list[str] | None:
        """重新生成备用码
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            code: 当前2FA验证码
            
        Returns:
            list[str] | None: 新的备用码列表，验证失败返回 None
        """
        settings_obj = await self._get_or_create_settings(db, user_id)
        
        if not settings_obj.is_2fa_enabled or not settings_obj.totp_secret:
            return None
        
        # 解密密钥
        secret = self.totp.decrypt_secret(settings_obj.totp_secret)
        if not secret:
            return None
        
        # 验证验证码
        if not self.totp.verify_code(secret, code):
            return None
        
        # 生成新的备用码
        new_codes = self.totp.generate_backup_codes()
        settings_obj.backup_codes = new_codes
        settings_obj.updated_at = datetime.now()
        
        await db.commit()
        return new_codes

    async def get_security_level(
        self,
        db: AsyncSession,
        user_id: int
    ) -> SecurityLevel:
        """获取安全等级评分
        
        基于多种因素计算用户安全等级：
        - 是否启用 2FA
        - 密码修改时间
        - 活跃设备数量
        - 登录失败记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            SecurityLevel: 安全等级信息
        """
        settings_obj = await self._get_or_create_settings(db, user_id)
        
        score = 0
        factors: dict[str, Any] = {}
        
        # 1. 2FA 启用 (+40 分)
        if settings_obj.is_2fa_enabled:
            score += 40
            factors["two_fa_enabled"] = True
        else:
            factors["two_fa_enabled"] = False
        
        # 2. 密码修改时间 (+30 分，90天内修改)
        password_score = 0
        if settings_obj.password_changed_at:
            days_since_change = (datetime.now() - settings_obj.password_changed_at).days
            if days_since_change <= 30:
                password_score = 30
            elif days_since_change <= 90:
                password_score = 20
            else:
                password_score = 10
        else:
            password_score = 0
        score += password_score
        factors["password_age_score"] = password_score
        
        # 3. 设备数量 (+20 分，1-3个设备最佳)
        devices = await self.device.list_devices(db, user_id, include_revoked=False)
        device_count = len(devices)
        if 1 <= device_count <= 3:
            device_score = 20
        elif device_count <= 5:
            device_score = 10
        else:
            device_score = 5  # 设备过多可能不安全
        score += device_score
        factors["device_count"] = device_count
        factors["device_score"] = device_score
        
        # 4. 近期失败登录记录 (-10 分，有失败记录扣分)
        recent_failures = await self.audit.get_recent_failures(db, user_id, minutes=60 * 24 * 7)  # 最近7天
        failure_penalty = min(len(recent_failures) * 2, 10)  # 最多扣10分
        score -= failure_penalty
        factors["recent_failures"] = len(recent_failures)
        factors["failure_penalty"] = failure_penalty
        
        # 确保分数在 0-100 范围内
        score = max(0, min(100, score))
        
        # 确定等级
        if score >= 80:
            level = "high"
        elif score >= 60:
            level = "medium"
        else:
            level = "low"
        
        factors["recommendations"] = self._get_security_recommendations(
            factors, settings_obj
        )
        
        return SecurityLevel(score=score, level=level, factors=factors)

    def _get_security_recommendations(
        self,
        factors: dict[str, Any],
        settings_obj: UserSecuritySettings
    ) -> list[str]:
        """获取安全建议
        
        Args:
            factors: 安全因素
            settings_obj: 安全设置
            
        Returns:
            list[str]: 建议列表
        """
        recommendations: list[str] = []
        
        if not factors.get("two_fa_enabled"):
            recommendations.append("建议启用双因素认证(2FA)以提升账户安全性")
        
        if factors.get("password_age_score", 0) < 20:
            recommendations.append("建议定期更换密码（建议每90天内更换一次）")
        
        if factors.get("recent_failures", 0) > 0:
            recommendations.append("近期有登录失败记录，请检查账户是否存在异常")
        
        if factors.get("device_count", 0) > 5:
            recommendations.append("登录设备过多，建议撤销不常用的设备")
        
        if not settings_obj.login_alert_enabled:
            recommendations.append("建议开启登录提醒，及时获知账户动态")
        
        return recommendations

    async def update_security_preferences(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        login_alert_enabled: bool | None = None,
        unusual_activity_alert: bool | None = None
    ) -> bool:
        """更新安全偏好设置
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            login_alert_enabled: 登录提醒开关
            unusual_activity_alert: 异常活动提醒开关
            
        Returns:
            bool: 是否成功更新
        """
        settings_obj = await self._get_or_create_settings(db, user_id)
        
        if login_alert_enabled is not None:
            settings_obj.login_alert_enabled = login_alert_enabled
        
        if unusual_activity_alert is not None:
            settings_obj.unusual_activity_alert = unusual_activity_alert
        
        settings_obj.updated_at = datetime.now()
        await db.commit()
        return True

    async def get_security_overview(
        self,
        db: AsyncSession,
        user_id: int
    ) -> dict[str, Any]:
        """获取安全概览
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            dict[str, Any]: 安全概览信息
        """
        # 2FA 状态
        two_fa_status = await self.get_2fa_status(db, user_id)
        
        # 安全等级
        security_level = await self.get_security_level(db, user_id)
        
        # 设备列表
        devices = await self.device.list_devices(db, user_id, include_revoked=False)
        active_devices = [
            {
                "device_id": d.device_id,
                "device_name": d.device_name,
                "device_type": d.device_type.value,
                "last_login_at": d.last_login_at.isoformat() if d.last_login_at else None,
                "is_current": d.is_current,
                "location": d.location
            }
            for d in devices
        ]
        
        # 最近登录记录
        login_history, _ = await self.audit.get_login_history(
            db, user_id, page=1, page_size=5
        )
        recent_logins = [
            {
                "action": h.action.value,
                "success": h.success,
                "ip_address": h.ip_address,
                "location": h.location,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in login_history
        ]
        
        return {
            "two_fa": {
                "is_enabled": two_fa_status.is_enabled,
                "is_setup": two_fa_status.is_setup
            },
            "security_level": {
                "score": security_level.score,
                "level": security_level.level
            },
            "active_devices": active_devices,
            "recent_logins": recent_logins,
            "recommendations": security_level.factors.get("recommendations", [])
        }


# 全局服务实例
user_security_service = UserSecurityService()