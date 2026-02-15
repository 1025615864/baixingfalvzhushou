"""数据安全 API 路由

提供数据分级、敏感字段脱敏、审计日志查询功能。
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..utils.deps import get_current_user, require_admin
from ..services.data_security import data_security_service, DataLevel, SensitiveType

router = APIRouter(prefix="/security", tags=["数据安全"])


class FieldClassificationResponse(BaseModel):
    """字段分级响应"""

    field_name: str
    level: str
    sensitive_type: str | None
    description: str


class MaskResultResponse(BaseModel):
    """脱敏结果响应"""

    masked: bool
    masked_fields: list[str]


class AuditLogResponse(BaseModel):
    """审计日志响应"""

    id: str
    action: str
    user_id: int | None
    resource_type: str
    resource_id: str
    details: dict[str, object] | None
    ip_address: str | None
    timestamp: str


class AuditStatsResponse(BaseModel):
    """审计统计响应"""

    total_logs: int
    action_counts: dict[str, int]
    retention_days: int


class SecurityReportResponse(BaseModel):
    """安全报告响应"""

    audit_stats: dict[str, object]
    classification_count: int
    mask_rules_count: int


@router.get("/classifications",
            response_model=list[FieldClassificationResponse],
            summary="获取所有字段分级")
async def list_classifications():
    """列出所有已注册的字段分级"""
    return data_security_service.list_classifications()


@router.get("/classifications/{field_name}",
            response_model=dict, summary="获取字段分级")
async def get_field_classification(field_name: str):
    """获取指定字段的分级信息"""
    return data_security_service.get_field_classification(field_name)


@router.post("/classify", response_model=dict, summary="分级数据")
async def classify_data(
    data: dict[str, object],
    fields: list[str],
):
    """对指定字段进行数据分级

    Args:
        data: 原始数据
        fields: 要分级的字段列表
    """
    return await data_security_service.classify_data(data, fields)


@router.post("/mask", response_model=MaskResultResponse, summary="脱敏敏感数据")
async def mask_data(
    data: dict[str, object],
    fields: list[str],
    mask_type: SensitiveType | None = None,
):
    """对指定字段进行敏感数据脱敏

    Args:
        data: 原始数据
        fields: 要脱敏的字段列表
        mask_type: 敏感数据类型
    """
    return await data_security_service.mask_sensitive_data(data, fields, mask_type)


@router.post("/audit", response_model=dict, summary="记录审计操作")
async def create_audit_log(
    action: str,
    resource_type: str,
    resource_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    details: dict[str, object] | None = None,
    ip_address: str | None = None,
):
    """记录审计日志

    Args:
        action: 操作类型
        resource_type: 资源类型
        resource_id: 资源ID
        details: 详情
        ip_address: IP地址
    """
    return await data_security_service.audit_action(
        action=action,
        user_id=int(current_user.id),
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )


@router.get("/audit/logs",
            response_model=list[AuditLogResponse], summary="查询审计日志")
async def get_audit_logs(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int | None = Query(None, description="按用户ID筛选"),
    resource_type: str | None = Query(None, description="按资源类型筛选"),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """查询审计日志"""
    _ = current_user
    _ = db
    logs = await data_security_service.get_audit_logs(user_id, resource_type, limit=limit)
    return logs


@router.get("/audit/stats",
            response_model=AuditStatsResponse,
            summary="获取审计统计")
async def get_audit_stats(
    current_user: Annotated[User, Depends(require_admin)],
):
    """获取审计日志统计"""
    _ = current_user
    return data_security_service.get_audit_stats()


@router.get("/report", response_model=SecurityReportResponse, summary="获取安全报告")
async def get_security_report(
    current_user: Annotated[User, Depends(require_admin)],
):
    """获取整体安全报告"""
    _ = current_user
    return await data_security_service.get_security_report()


@router.post("/register-defaults",
             response_model=list[dict[str, object]], summary="注册默认分级配置")
async def register_default_classifications(
    current_user: Annotated[User, Depends(require_admin)],
):
    """注册默认的敏感字段分级配置"""
    _ = current_user
    return data_security_service.register_default_classifications()


@router.get("/levels", response_model=list[dict[str, object]], summary="获取数据分级级别")
async def get_data_levels():
    """获取所有数据分级级别"""
    return [
        {"level": level.value, "name": level.name}
        for level in DataLevel
    ]


@router.get("/sensitive-types", response_model=list[dict[str, object]], summary="获取敏感数据类型")
async def get_sensitive_types():
    """获取所有敏感数据类型"""
    return [
        {"type": t.value, "name": t.name}
        for t in SensitiveType
    ]


@router.get("/admin/report", response_model=SecurityReportResponse,
            summary="获取安全报告（管理员）")
async def admin_get_security_report(
    current_user: Annotated[User, Depends(require_admin)],
):
    """管理员获取整体安全报告"""
    _ = current_user
    return await data_security_service.get_security_report()


@router.get("/admin/audit/logs",
            response_model=list[AuditLogResponse], summary="查询审计日志（管理员）")
async def admin_get_audit_logs(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int | None = Query(None, description="按用户ID筛选"),
    resource_type: str | None = Query(None, description="按资源类型筛选"),
    start_time: datetime | None = Query(None, description="开始时间"),
    end_time: datetime | None = Query(None, description="结束时间"),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """管理员查询审计日志（支持时间范围）"""
    _ = current_user
    _ = db
    logs = await data_security_service.get_audit_logs(
        user_id=user_id,
        resource_type=resource_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return logs


@router.get("/admin/audit/stats",
            response_model=AuditStatsResponse, summary="获取审计统计（管理员）")
async def admin_get_audit_stats(
    current_user: Annotated[User, Depends(require_admin)],
):
    """管理员获取审计日志统计"""
    _ = current_user
    return data_security_service.get_audit_stats()
