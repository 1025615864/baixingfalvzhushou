"""个人数据导出路由 - 符合个人信息保护法（异步版）"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.data_export_service import DataExportService
from ..middleware.auth import get_current_user
from ..models import User
from ..tasks.export_task import export_task_processor

router = APIRouter(prefix="/account", tags=["账号"])


@router.post(
    "/data/export",
    summary="创建数据导出任务",
    description="创建异步数据导出任务，符合《个人信息保护法》要求。",
    responses={
        200: {"description": "导出任务已创建"},
        429: {"description": "已有待处理或进行中的导出任务"},
    }
)
async def create_export_task(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """创建数据导出任务

    返回任务ID，可通过 GET /data/export/{task_id} 查询进度和结果。
    任务完成后结果保留24小时。
    """
    task = await export_task_processor.create_export_task(
        db, current_user.id, "json"
    )

    return {
        "task_id": task.id,
        "status": task.status,
        "message": "导出任务已创建，请在24小时内下载",
        "check_url": f"/api/v1/account/data/export/{task.id}"
    }


@router.get(
    "/data/export/{task_id}",
    summary="查询导出任务状态",
    description="查询异步导出任务的进度和结果。",
    responses={
        200: {"description": "返回导出结果"},
        404: {"description": "任务不存在或已过期"},
        202: {"description": "任务处理中"},
    }
)
async def get_export_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """查询导出任务状态

    返回任务状态和结果（如果已完成）：
    - pending: 等待处理
    - processing: 处理中
    - completed: 已完成，可获取结果
    - failed: 处理失败
    - expired: 已过期
    """
    task = await export_task_processor.get_task_status(
        db, task_id, current_user.id
    )

    if not task:
        raise HTTPException(status_code=404, detail="导出任务不存在或已过期")

    response = {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }

    if task.status == "processing":
        response["message"] = "数据导出处理中，请稍候"

    elif task.status == "completed":
        response["progress"] = 100
        response["data"] = task.result_data
        response["message"] = "导出完成，请在24小时内下载"
        response["expires_at"] = task.expires_at.isoformat() if task.expires_at else None

    elif task.status == "failed":
        response["error"] = task.error_message
        response["message"] = "导出失败，请稍后重试"

    elif task.status == "expired":
        response["message"] = "导出结果已过期，请重新创建导出任务"

    return response


@router.get(
    "/data/export-quick",
    summary="快速导出个人数据",
    description="直接返回用户数据（同步方式），适用于数据量较小的场景。",
    responses={
        200: {"description": "返回导出数据"},
        404: {"description": "用户不存在"},
    }
)
async def export_data_sync(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """快速导出个人数据

    适用于数据量较小的场景。
    数据量较大时建议使用异步接口 POST /data/export。
    """
    service = DataExportService(db)
    data = await service.export_user_data(current_user.id)

    if not data:
        raise HTTPException(status_code=404, detail="用户不存在")

    return JSONResponse(content=data)


@router.get(
    "/data/export/preview",
    summary="数据导出预览",
    description="查看即将导出的数据概览，不包含详细数据。",
)
async def export_data_preview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal)
):
    """数据导出预览

    返回导出的数据摘要，帮助用户了解将导出的数据类型。
    """
    service = DataExportService(db)
    summary = await service.get_data_summary(current_user.id)

    if not summary:
        raise HTTPException(status_code=404, detail="用户不存在")

    return summary
