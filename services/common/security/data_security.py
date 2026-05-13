"""数据安全服务

提供数据分级、敏感字段脱敏、审计日志功能。
"""
import logging
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DataLevel(Enum):
    """数据分级"""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class SensitiveType(Enum):
    """敏感数据类型"""

    PHONE = "phone"
    ID_CARD = "id_card"
    BANK_CARD = "bank_card"
    PASSWORD = "password"
    TOKEN = "token"
    EMAIL = "email"
    NAME = "name"
    ADDRESS = "address"


class DataClassificationConfig:
    """数据分级配置"""

    def __init__(self):
        self._field_mappings: dict[str, dict[str, Any]] = {}
        self._sensitive_patterns: dict[SensitiveType, re.Pattern[str]] = {}

    def register_field(
        self,
        field_name: str,
        level: DataLevel,
        sensitive_type: SensitiveType | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        """注册字段分级

        Args:
            field_name: 字段名
            level: 分级
            sensitive_type: 敏感类型
            description: 描述

        Returns:
            配置结果
        """
        self._field_mappings[field_name] = {
            "field_name": field_name,
            "level": level.value,
            "sensitive_type": sensitive_type.value if sensitive_type else None,
            "description": description,
        }

        return {
            "field_name": field_name,
            "level": level.value,
            "registered": True,
        }

    def get_field_level(self, field_name: str) -> dict[str, Any]:
        """获取字段分级

        Args:
            field_name: 字段名

        Returns:
            分级信息
        """
        return self._field_mappings.get(field_name, {
            "field_name": field_name,
            "level": DataLevel.INTERNAL.value,
            "sensitive_type": None,
        })

    def list_classifications(self) -> list[dict[str, Any]]:
        """列出所有分级

        Returns:
            分级列表
        """
        return list(self._field_mappings.values())


class DataMasker:
    """数据脱敏器"""

    def __init__(self):
        self._mask_rules: dict[str, dict[str, Any]] = {}
        self._sensitive_patterns: dict[SensitiveType, re.Pattern[str]] = {}
        self._init_default_patterns()

    def _init_default_patterns(self):
        """初始化默认模式"""
        self._sensitive_patterns = {
            SensitiveType.PHONE: re.compile(r"(\d{3})\d{4}(\d{4})"),
            SensitiveType.ID_CARD: re.compile(r"(\d{3})\d{11}(\d{4})"),
            SensitiveType.BANK_CARD: re.compile(r"(\d{4})\d+(\d{4})"),
            SensitiveType.EMAIL: re.compile(r"(\w{2})\w+(@.+)"),
        }

    def register_mask_rule(
        self,
        field_name: str,
        mask_char: str = "*",
        visible_prefix: int = 2,
        visible_suffix: int = 2,
    ) -> dict[str, Any]:
        """注册脱敏规则

        Args:
            field_name: 字段名
            mask_char: 掩码字符
            visible_prefix: 前缀可见位数
            visible_suffix: 后缀可见位数

        Returns:
            规则结果
        """
        self._mask_rules[field_name] = {
            "field_name": field_name,
            "mask_char": mask_char,
            "visible_prefix": visible_prefix,
            "visible_suffix": visible_suffix,
        }

        return {
            "field_name": field_name,
            "rule_registered": True,
        }

    def mask_value(
        self,
        value: str,
        mask_type: SensitiveType | None = None,
        mask_char: str = "*",
    ) -> str:
        """脱敏值

        Args:
            value: 原始值
            mask_type: 敏感类型
            mask_char: 掩码字符

        Returns:
            脱敏后值
        """
        if not value:
            return value

        if mask_type == SensitiveType.PHONE:
            return re.sub(r"(\d{3})\d{4}(\d{4})", r"\1****\2", value)
        elif mask_type == SensitiveType.ID_CARD:
            return re.sub(r"(\d{3})\d{11}(\d{4})", r"\1***********\2", value)
        elif mask_type == SensitiveType.BANK_CARD:
            return re.sub(r"(\d{4})\d+(\d{4})", r"\1**********\2", value)
        elif mask_type == SensitiveType.EMAIL:
            return re.sub(r"(\w{2})\w+(@.+)", r"\1****\2", value)
        else:
            return self._mask_custom(value, mask_char)

    def _mask_custom(
        self,
        value: str,
        mask_char: str,
        visible_prefix: int = 2,
        visible_suffix: int = 2,
    ) -> str:
        """自定义脱敏

        Args:
            value: 值
            mask_char: 掩码字符
            visible_prefix: 前缀可见
            visible_suffix: 后缀可见

        Returns:
            脱敏后值
        """
        if len(value) <= visible_prefix + visible_suffix:
            return mask_char * len(value)

        return value[:visible_prefix] + mask_char * \
            (len(value) - visible_prefix - visible_suffix) + \
            value[-visible_suffix:]

    def mask_dict(
        self,
        data: dict[str, Any],
        fields: list[str],
        mask_type: SensitiveType | None = None,
    ) -> dict[str, Any]:
        """脱敏字典

        Args:
            data: 原始数据
            fields: 要脱敏的字段
            mask_type: 敏感类型

        Returns:
            脱敏后数据
        """
        masked = data.copy()
        for field in fields:
            if field in masked and masked[field]:
                masked[field] = self.mask_value(str(masked[field]), mask_type)
        return masked


class AuditLogger:
    """审计日志记录器"""

    def __init__(self):
        self._audit_logs: list[dict[str, Any]] = []
        self._retention_days = 90

    def log(
        self,
        action: str,
        user_id: int | None,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """记录审计日志

        Args:
            action: 操作类型
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            details: 详情
            ip_address: IP地址

        Returns:
            日志记录
        """
        log_entry = {
            "id": f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            "action": action,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "timestamp": datetime.now(
                timezone.utc).isoformat(),
        }

        self._audit_logs.append(log_entry)

        logger.info(
            f"Audit: {action} on {resource_type}:{resource_id} by user {user_id}")

        return {
            "audit_id": log_entry["id"],
            "logged": True,
        }

    def get_logs(
        self,
        user_id: int | None = None,
        resource_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """获取审计日志

        Args:
            user_id: 用户ID
            resource_type: 资源类型
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制

        Returns:
            日志列表
        """
        filtered = self._audit_logs

        if user_id is not None:
            filtered = [l for l in filtered if l.get("user_id") == user_id]
        if resource_type:
            filtered = [l for l in filtered if l.get(
                "resource_type") == resource_type]
        if start_time or end_time:
            def _parse_time(value: object) -> datetime | None:
                try:
                    return datetime.fromisoformat(str(value))
                except Exception:
                    logger.warning("时间戳解析失败")
                    return None

            filtered_time: list[dict[str, Any]] = []
            for log in filtered:
                ts_raw = log.get("timestamp")
                ts = _parse_time(ts_raw)
                if ts is None:
                    continue
                if start_time and ts < start_time:
                    continue
                if end_time and ts > end_time:
                    continue
                filtered_time.append(log)
            filtered = filtered_time

        return filtered[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """获取统计

        Returns:
            统计信息
        """
        action_counts: dict[str, int] = {}
        for log in self._audit_logs:
            action = log.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1

        return {
            "total_logs": len(self._audit_logs),
            "action_counts": action_counts,
            "retention_days": self._retention_days,
        }


class DataSecurityService:
    """数据安全服务"""

    def __init__(self):
        self._classification = DataClassificationConfig()
        self._masker = DataMasker()
        self._audit = AuditLogger()

    def register_default_classifications(self) -> list[dict[str, Any]]:
        """注册默认分级

        Returns:
            注册结果
        """
        default_fields = [
            ("phone", DataLevel.CONFIDENTIAL, SensitiveType.PHONE, "手机号"),
            ("id_card", DataLevel.RESTRICTED, SensitiveType.ID_CARD, "身份证号"),
            ("bank_card", DataLevel.CONFIDENTIAL, SensitiveType.BANK_CARD, "银行卡号"),
            ("password", DataLevel.RESTRICTED, SensitiveType.PASSWORD, "密码"),
            ("token", DataLevel.RESTRICTED, SensitiveType.TOKEN, "令牌"),
            ("email", DataLevel.INTERNAL, SensitiveType.EMAIL, "邮箱"),
            ("name", DataLevel.INTERNAL, SensitiveType.NAME, "姓名"),
            ("address", DataLevel.CONFIDENTIAL, SensitiveType.ADDRESS, "地址"),
        ]

        results = []
        for field_name, level, sensitive_type, description in default_fields:
            result = self._classification.register_field(
                field_name=field_name,
                level=level,
                sensitive_type=sensitive_type,
                description=description,
            )
            results.append(result)

            self._masker.register_mask_rule(field_name=field_name)

        return results

    def list_classifications(self) -> list[dict[str, Any]]:
        return self._classification.list_classifications()

    def get_field_classification(self, field_name: str) -> dict[str, Any]:
        return self._classification.get_field_level(field_name)

    async def classify_data(
        self,
        data: dict[str, Any],
        fields: list[str],
    ) -> dict[str, Any]:
        """分级数据

        Args:
            data: 原始数据
            fields: 要分级的字段

        Returns:
            分级结果
        """
        classifications = {}
        for field in fields:
            if field in data:
                level_info = self._classification.get_field_level(field)
                classifications[field] = level_info

        return {
            "classified": True,
            "classifications": classifications,
        }

    async def mask_sensitive_data(
        self,
        data: dict[str, Any],
        fields: list[str],
        mask_type: SensitiveType | None = None,
    ) -> dict[str, Any]:
        """脱敏敏感数据

        Args:
            data: 原始数据
            fields: 要脱敏的字段
            mask_type: 敏感类型

        Returns:
            脱敏结果
        """
        masked = self._masker.mask_dict(data, fields, mask_type)

        return {
            "masked": True,
            "masked_fields": fields,
        }

    async def audit_action(
        self,
        action: str,
        user_id: int | None,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """审计操作

        Args:
            action: 操作类型
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            details: 详情
            ip_address: IP地址

        Returns:
            审计结果
        """
        return self._audit.log(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )

    async def get_audit_logs(
        self,
        user_id: int | None = None,
        resource_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """获取审计日志

        Args:
            user_id: 用户ID
            resource_type: 资源类型
            limit: 限制

        Returns:
            日志列表
        """
        return self._audit.get_logs(
            user_id=user_id,
            resource_type=resource_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    def get_audit_stats(self) -> dict[str, Any]:
        return self._audit.get_stats()

    async def get_security_report(self) -> dict[str, Any]:
        """获取安全报告

        Returns:
            安全报告
        """
        audit_stats = self.get_audit_stats()
        classifications = self.list_classifications()

        return {
            "audit_stats": audit_stats,
            "classification_count": len(classifications),
            "mask_rules_count": len(self._masker._mask_rules),
        }


# 单例实例
data_security_service = DataSecurityService()


async def classify_data(
    data: dict[str, Any],
    fields: list[str],
) -> dict[str, Any]:
    """便捷函数：分级数据

    Args:
        data: 原始数据
        fields: 要分级的字段

    Returns:
        分级结果
    """
    return await data_security_service.classify_data(data=data, fields=fields)


async def mask_sensitive_data(
    data: dict[str, Any],
    fields: list[str],
    mask_type: SensitiveType | None = None,
) -> dict[str, Any]:
    """便捷函数：脱敏敏感数据

    Args:
        data: 原始数据
        fields: 要脱敏的字段
        mask_type: 敏感类型

    Returns:
        脱敏结果
    """
    return await data_security_service.mask_sensitive_data(
        data=data,
        fields=fields,
        mask_type=mask_type,
    )


async def audit_action(
    action: str,
    user_id: int | None,
    resource_type: str,
    resource_id: str,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> dict[str, Any]:
    """便捷函数：审计操作

    Args:
        action: 操作类型
        user_id: 用户ID
        resource_type: 资源类型
        resource_id: 资源ID
        details: 详情
        ip_address: IP地址

    Returns:
        审计结果
    """
    return await data_security_service.audit_action(
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
