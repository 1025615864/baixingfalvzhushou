"""设备管理服务"""
from datetime import datetime
from typing import Optional
import logging

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from ..models import UserDevice
from .audit_service import AuditService

logger = logging.getLogger(__name__)

MAX_DEVICES_PER_USER = 5


class DeviceService:
    """设备管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_device(
        self,
        user_id: int,
        device_id: str,
        device_name: Optional[str] = None,
        device_type: Optional[str] = None,
        fcm_token: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """注册或更新设备

        Args:
            user_id: 用户ID
            device_id: 设备唯一标识
            device_name: 设备名称
            device_type: 设备类型 (ios/android/web)
            fcm_token: FCM推送令牌
            ip_address: IP地址
            user_agent: User-Agent

        Returns:
            设备信息
        """
        result = await self.db.execute(
            select(UserDevice).where(UserDevice.device_id == device_id)
        )
        device = result.scalar_one_or_none()

        if device:
            device.last_active_at = datetime.utcnow()
            if device_name:
                device.device_name = device_name
            if device_type:
                device.device_type = device_type
            if fcm_token:
                device.fcm_token = fcm_token
            device.updated_at = datetime.utcnow()
        else:
            device_count = await self._count_user_devices(user_id)
            if device_count >= MAX_DEVICES_PER_USER:
                oldest_result = await self.db.execute(
                    select(UserDevice)
                    .where(UserDevice.user_id == user_id)
                    .order_by(UserDevice.last_active_at.asc())
                    .limit(1)
                )
                oldest = oldest_result.scalar_one_or_none()
                if oldest:
                    await self.db.delete(oldest)
                    logger.info(f"Removed oldest device {oldest.device_id} for user {user_id}")

            device = UserDevice(
                user_id=user_id,
                device_id=device_id,
                device_name=device_name,
                device_type=device_type,
                fcm_token=fcm_token,
                last_active_at=datetime.utcnow(),
            )
            self.db.add(device)

        await self.db.commit()
        await self.db.refresh(device)

        await AuditService(self.db).log(
            user_id=user_id,
            action="device_registered",
            resource="device",
            resource_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success",
            details=f"Device {device_id} registered: {device_name or 'unknown'}",
        )

        return self._device_to_dict(device)

    async def list_user_devices(
        self,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> list[dict]:
        """列出用户的所有设备

        Args:
            user_id: 用户ID
            ip_address: IP地址
            user_agent: User-Agent

        Returns:
            设备列表
        """
        result = await self.db.execute(
            select(UserDevice)
            .where(UserDevice.user_id == user_id)
            .order_by(UserDevice.last_active_at.desc())
        )
        devices = result.scalars().all()

        await AuditService(self.db).log(
            user_id=user_id,
            action="device_listed",
            resource="device",
            ip_address=ip_address,
            user_agent=user_agent,
            status="success",
            details=f"Listed {len(devices)} devices",
        )

        return [self._device_to_dict(d) for d in devices]

    async def remove_device(
        self,
        user_id: int,
        device_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """移除设备

        Args:
            user_id: 用户ID
            device_id: 设备ID
            ip_address: IP地址
            user_agent: User-Agent

        Returns:
            是否成功
        """
        result = await self.db.execute(
            select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.device_id == device_id,
            )
        )
        device = result.scalar_one_or_none()

        if not device:
            return False

        await self.db.delete(device)
        await self.db.commit()

        await AuditService(self.db).log(
            user_id=user_id,
            action="device_removed",
            resource="device",
            resource_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success",
            details=f"Device {device_id} removed",
        )

        return True

    async def remove_all_devices(
        self,
        user_id: int,
        except_device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        """移除用户所有设备（可选保留指定设备）

        Args:
            user_id: 用户ID
            except_device_id: 保留的设备ID
            ip_address: IP地址
            user_agent: User-Agent

        Returns:
            移除的设备数量
        """
        query = select(UserDevice).where(UserDevice.user_id == user_id)
        if except_device_id:
            query = query.where(UserDevice.device_id != except_device_id)

        result = await self.db.execute(query)
        devices = result.scalars().all()
        count = len(devices)

        for device in devices:
            await self.db.delete(device)

        await self.db.commit()

        await AuditService(self.db).log(
            user_id=user_id,
            action="devices_removed",
            resource="device",
            ip_address=ip_address,
            user_agent=user_agent,
            status="success",
            details=f"Removed {count} devices (except {except_device_id})",
        )

        return count

    async def get_device_info(
        self,
        user_id: int,
        device_id: str,
    ) -> Optional[dict]:
        """获取设备信息

        Args:
            user_id: 用户ID
            device_id: 设备ID

        Returns:
            设备信息
        """
        result = await self.db.execute(
            select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.device_id == device_id,
            )
        )
        device = result.scalar_one_or_none()

        if not device:
            return None

        return self._device_to_dict(device)

    async def update_fcm_token(
        self,
        user_id: int,
        device_id: str,
        fcm_token: str,
    ) -> bool:
        """更新设备的FCM令牌

        Args:
            user_id: 用户ID
            device_id: 设备ID
            fcm_token: 新的FCM令牌

        Returns:
            是否成功
        """
        result = await self.db.execute(
            select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.device_id == device_id,
            )
        )
        device = result.scalar_one_or_none()

        if not device:
            return False

        device.fcm_token = fcm_token
        device.updated_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def update_last_active(
        self,
        device_id: str,
    ) -> bool:
        """更新设备最后活跃时间

        Args:
            device_id: 设备ID

        Returns:
            是否成功
        """
        result = await self.db.execute(
            select(UserDevice).where(UserDevice.device_id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            return False

        device.last_active_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def _count_user_devices(self, user_id: int) -> int:
        """统计用户设备数量"""
        result = await self.db.execute(
            select(func.count()).select_from(UserDevice).where(UserDevice.user_id == user_id)
        )
        return result.scalar() or 0

    @staticmethod
    def _device_to_dict(device: UserDevice) -> dict:
        """将设备对象转换为字典"""
        return {
            "id": device.id,
            "device_id": device.device_id,
            "device_name": device.device_name,
            "device_type": device.device_type,
            "last_active_at": device.last_active_at.isoformat() if device.last_active_at else None,
            "created_at": device.created_at.isoformat() if device.created_at else None,
        }
