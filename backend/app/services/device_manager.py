"""设备管理服务"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import NamedTuple

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user_security import UserDevice, DeviceType


class DeviceInfo(NamedTuple):
    """设备信息"""
    device_name: str | None
    device_type: DeviceType
    user_agent: str | None
    ip_address: str | None
    location: str | None


class DeviceManager:
    """设备管理服务"""

    @staticmethod
    async def list_devices(
        db: AsyncSession,
        user_id: int,
        include_revoked: bool = False
    ) -> list[UserDevice]:
        """获取用户设备列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            include_revoked: 是否包含已撤销的设备
            
        Returns:
            list[UserDevice]: 设备列表
        """
        query = select(UserDevice).where(
            UserDevice.user_id == user_id
        )
        
        if not include_revoked:
            query = query.where(UserDevice.is_revoked == False)
        
        query = query.order_by(desc(UserDevice.last_login_at))
        
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def register_device(
        db: AsyncSession,
        user_id: int,
        device_info: DeviceInfo,
        token_fingerprint: str | None = None
    ) -> UserDevice:
        """注册新设备
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            device_info: 设备信息
            token_fingerprint: Token指纹
            
        Returns:
            UserDevice: 创建的设备记录
        """
        now = datetime.now()
        
        device = UserDevice(
            user_id=user_id,
            device_id=str(uuid.uuid4()),
            device_name=device_info.device_name,
            device_type=device_info.device_type,
            user_agent=device_info.user_agent,
            ip_address=device_info.ip_address,
            location=device_info.location,
            first_login_at=now,
            last_login_at=now,
            is_current=True,
            is_revoked=False,
            token_fingerprint=token_fingerprint
        )
        
        db.add(device)
        await db.commit()
        await db.refresh(device)
        return device

    @staticmethod
    async def revoke_device(
        db: AsyncSession,
        user_id: int,
        device_id: str
    ) -> bool:
        """撤销设备
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            device_id: 设备ID
            
        Returns:
            bool: 是否成功撤销
        """
        result = await db.execute(
            select(UserDevice).where(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.device_id == device_id,
                    UserDevice.is_revoked == False
                )
            )
        )
        device = result.scalar_one_or_none()
        
        if not device:
            return False
        
        device.is_revoked = True
        device.is_current = False
        device.revoked_at = datetime.now()
        
        await db.commit()
        return True

    @staticmethod
    async def revoke_other_devices(
        db: AsyncSession,
        user_id: int,
        current_device_id: str
    ) -> int:
        """撤销其他设备
        
        撤销用户的所有其他活跃设备。
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            current_device_id: 当前设备ID（保留）
            
        Returns:
            int: 撤销的设备数量
        """
        result = await db.execute(
            select(UserDevice).where(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.device_id != current_device_id,
                    UserDevice.is_revoked == False
                )
            )
        )
        devices = result.scalars().all()
        
        revoked_count = 0
        now = datetime.now()
        
        for device in devices:
            device.is_revoked = True
            device.is_current = False
            device.revoked_at = now
            revoked_count += 1
        
        if revoked_count > 0:
            await db.commit()
        
        return revoked_count

    @staticmethod
    async def get_current_device(
        db: AsyncSession,
        user_id: int,
        token_fingerprint: str
    ) -> UserDevice | None:
        """获取当前设备
        
        根据 Token 指纹获取当前设备信息。
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            token_fingerprint: Token指纹
            
        Returns:
            UserDevice | None: 设备记录，未找到返回 None
        """
        result = await db.execute(
            select(UserDevice).where(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.token_fingerprint == token_fingerprint,
                    UserDevice.is_revoked == False
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_last_login(
        db: AsyncSession,
        device_id: str
    ) -> bool:
        """更新设备最后登录时间
        
        Args:
            db: 数据库会话
            device_id: 设备ID
            
        Returns:
            bool: 是否成功更新
        """
        result = await db.execute(
            select(UserDevice).where(
                and_(
                    UserDevice.device_id == device_id,
                    UserDevice.is_revoked == False
                )
            )
        )
        device = result.scalar_one_or_none()
        
        if not device:
            return False
        
        device.last_login_at = datetime.now()
        await db.commit()
        return True

    @staticmethod
    async def set_current_device(
        db: AsyncSession,
        user_id: int,
        device_id: str
    ) -> bool:
        """设置当前设备
        
        将指定设备标记为当前设备，其他设备取消当前标记。
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            device_id: 设备ID
            
        Returns:
            bool: 是否成功设置
        """
        # 先取消所有设备的当前标记
        result = await db.execute(
            select(UserDevice).where(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.is_current == True
                )
            )
        )
        devices = result.scalars().all()
        
        for device in devices:
            device.is_current = False
        
        # 设置指定设备为当前设备
        result = await db.execute(
            select(UserDevice).where(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.device_id == device_id,
                    UserDevice.is_revoked == False
                )
            )
        )
        target_device = result.scalar_one_or_none()
        
        if not target_device:
            return False
        
        target_device.is_current = True
        target_device.last_login_at = datetime.now()
        
        await db.commit()
        return True

    @staticmethod
    def generate_device_fingerprint(user_agent: str, ip: str) -> str:
        """生成设备指纹
        
        基于用户代理和 IP 地址生成设备唯一标识。
        
        Args:
            user_agent: 用户代理字符串
            ip: IP 地址
            
        Returns:
            str: 设备指纹（32位十六进制字符串）
        """
        # 使用 SHA-256 哈希
        data = f"{user_agent}:{ip}"
        fingerprint = hashlib.sha256(data.encode()).hexdigest()[:32]
        return fingerprint

    @staticmethod
    def parse_user_agent(user_agent: str | None) -> tuple[str | None, DeviceType]:
        """解析用户代理字符串
        
        从 User-Agent 中提取设备名称和类型。
        
        Args:
            user_agent: 用户代理字符串
            
        Returns:
            tuple[str | None, DeviceType]: (设备名称, 设备类型)
        """
        if not user_agent:
            return (None, DeviceType.WEB)
        
        ua = user_agent.lower()
        device_name = None
        device_type = DeviceType.WEB
        
        # 检测移动设备
        if "mobile" in ua or "android" in ua or "iphone" in ua:
            device_type = DeviceType.MOBILE
            if "android" in ua:
                device_name = "Android 设备"
            elif "iphone" in ua:
                device_name = "iPhone"
            elif "ipad" in ua:
                device_name = "iPad"
            else:
                device_name = "移动设备"
        elif any(app in ua for app in ["app", "native", "flutter", "react native"]):
            device_type = DeviceType.APP
            device_name = "App"
        else:
            # 浏览器
            if "chrome" in ua:
                device_name = "Chrome 浏览器"
            elif "firefox" in ua:
                device_name = "Firefox 浏览器"
            elif "safari" in ua:
                device_name = "Safari 浏览器"
            elif "edge" in ua:
                device_name = "Edge 浏览器"
            else:
                device_name = "Web 浏览器"
        
        return (device_name, device_type)

    @staticmethod
    async def get_device_by_id(
        db: AsyncSession,
        user_id: int,
        device_id: str
    ) -> UserDevice | None:
        """通过设备ID获取设备
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            device_id: 设备ID
            
        Returns:
            UserDevice | None: 设备记录
        """
        result = await db.execute(
            select(UserDevice).where(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.device_id == device_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def cleanup_revoked_devices(
        db: AsyncSession,
        user_id: int,
        days: int = 30
    ) -> int:
        """清理旧的已撤销设备
        
        删除指定天数前撤销的设备记录。
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            days: 天数阈值
            
        Returns:
            int: 删除的设备数量
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        result = await db.execute(
            select(UserDevice).where(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.is_revoked == True,
                    UserDevice.revoked_at <= cutoff_date
                )
            )
        )
        devices = result.scalars().all()
        
        deleted_count = 0
        for device in devices:
            await db.delete(device)
            deleted_count += 1
        
        if deleted_count > 0:
            await db.commit()
        
        return deleted_count


# 全局服务实例
device_manager = DeviceManager()