"""设备管理路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from pydantic import BaseModel

from ..database import AsyncSessionLocal
from ..services.device_service import DeviceService
from ..services.auth_service import AuthService

router = APIRouter()


class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    fcm_token: Optional[str] = None


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    last_active_at: Optional[str] = None
    created_at: Optional[str] = None


class DeviceListResponse(BaseModel):
    devices: list[DeviceResponse]
    total: int


class FCMTokenUpdateRequest(BaseModel):
    device_id: str
    fcm_token: str


class RemoveDeviceRequest(BaseModel):
    device_id: str


class RemoveAllDevicesRequest(BaseModel):
    except_device_id: Optional[str] = None


async def get_current_user_id(
    authorization: str = Header(None),
    db=Depends(lambda: AsyncSessionLocal()),
) -> int:
    """获取当前用户ID"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = authorization[7:]
    auth_service = AuthService(db)
    user_info = await auth_service.verify_token(token)

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return user_info["user_id"]


@router.post(
    "/register",
    response_model=DeviceResponse,
    summary="注册设备",
    description="注册或更新用户设备信息。同一设备重复注册会更新最后活跃时间。",
    responses={
        200: {"description": "设备注册成功"},
        401: {"description": "未认证"},
    }
)
async def register_device(
    request: Request,
    device_request: DeviceRegisterRequest,
    user_id: int = Depends(get_current_user_id),
    db=Depends(lambda: AsyncSessionLocal()),
):
    """注册或更新设备

    - **device_id**: 设备唯一标识（必填）
    - **device_name**: 设备名称（如 "iPhone 15"）
    - **device_type**: 设备类型 (ios/android/web)
    - **fcm_token**: FCM推送令牌

    用户最多绑定5个设备，超出时自动移除最旧的设备。
    """
    device_service = DeviceService(db)
    result = await device_service.register_device(
        user_id=user_id,
        device_id=device_request.device_id,
        device_name=device_request.device_name,
        device_type=device_request.device_type,
        fcm_token=device_request.fcm_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result


@router.get(
    "/list",
    response_model=DeviceListResponse,
    summary="获取设备列表",
    description="获取当前用户绑定的所有设备列表。",
    responses={
        200: {"description": "成功获取设备列表"},
        401: {"description": "未认证"},
    }
)
async def list_devices(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db=Depends(lambda: AsyncSessionLocal()),
):
    """获取设备列表

    返回用户绑定的所有设备，按最后活跃时间倒序排列。
    """
    device_service = DeviceService(db)
    devices = await device_service.list_user_devices(
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return DeviceListResponse(devices=[DeviceResponse(**d) for d in devices], total=len(devices))


@router.delete(
    "/{device_id}",
    summary="移除设备",
    description="移除指定的已绑定设备。",
    responses={
        200: {"description": "设备移除成功"},
        401: {"description": "未认证"},
        404: {"description": "设备不存在"},
    }
)
async def remove_device(
    request: Request,
    device_id: str,
    user_id: int = Depends(get_current_user_id),
    db=Depends(lambda: AsyncSessionLocal()),
):
    """移除设备

    - **device_id**: 要移除的设备ID
    """
    device_service = DeviceService(db)
    success = await device_service.remove_device(
        user_id=user_id,
        device_id=device_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return {"message": "Device removed successfully"}


@router.delete(
    "/all",
    summary="移除所有设备",
    description="移除用户绑定的所有设备。可选保留当前设备。",
    responses={
        200: {"description": "设备移除成功"},
        401: {"description": "未认证"},
    }
)
async def remove_all_devices(
    request: Request,
    except_device_id: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    db=Depends(lambda: AsyncSessionLocal()),
):
    """移除所有设备

    - **except_device_id**: 可选，保留的设备ID
    """
    device_service = DeviceService(db)
    count = await device_service.remove_all_devices(
        user_id=user_id,
        except_device_id=except_device_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {"message": f"Removed {count} devices"}


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="获取设备信息",
    description="获取指定设备的详细信息。",
    responses={
        200: {"description": "成功获取设备信息"},
        401: {"description": "未认证"},
        404: {"description": "设备不存在"},
    }
)
async def get_device(
    device_id: str,
    user_id: int = Depends(get_current_user_id),
    db=Depends(lambda: AsyncSessionLocal()),
):
    """获取设备信息

    - **device_id**: 设备ID
    """
    device_service = DeviceService(db)
    device = await device_service.get_device_info(user_id=user_id, device_id=device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return DeviceResponse(**device)


@router.put(
    "/fcm-token",
    summary="更新FCM令牌",
    description="更新指定设备的FCM推送令牌。",
    responses={
        200: {"description": "更新成功"},
        401: {"description": "未认证"},
        404: {"description": "设备不存在"},
    }
)
async def update_fcm_token(
    request: FCMTokenUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    db=Depends(lambda: AsyncSessionLocal()),
):
    """更新FCM令牌

    - **device_id**: 设备ID
    - **fcm_token**: 新的FCM令牌
    """
    device_service = DeviceService(db)
    success = await device_service.update_fcm_token(
        user_id=user_id,
        device_id=request.device_id,
        fcm_token=request.fcm_token,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return {"message": "FCM token updated successfully"}
