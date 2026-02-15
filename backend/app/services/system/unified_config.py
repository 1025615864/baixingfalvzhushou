"""统一配置服务 - 集成 ConfigGateway 和 SystemConfigService，提供类型化配置访问"""
from __future__ import annotations

import json
import logging
from typing import Annotated, Any

from fastapi import Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db  # pyright: ignore
from app.models.system import SystemConfig  # pyright: ignore
from .config import SystemConfigService
from .config_gateway import (
    ConfigGateway,
    ConfigValueType,
    config_gateway,
    _parse_bool,
    _parse_int,
    _parse_float,
)

logger = logging.getLogger(__name__)


class ConfigParseError(ValueError):
    """配置解析错误"""
    pass


class TypedConfigService:
    """类型化配置服务 - 提供强类型的配置获取方法"""

    def __init__(self, gateway: ConfigGateway | None = None) -> None:
        self._gateway = gateway or config_gateway

    async def get_typed(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],  # pyright: ignore
        key: str,
        expected_type: ConfigValueType,
        default: Any = None,
    ) -> Any:
        """获取类型化配置值

        Args:
            db: 数据库会话
            key: 配置键
            expected_type: 期望的类型
            default: 默认值（配置不存在时返回）

        Returns:
            解析后的值

        Raises:
            ConfigParseError: 值无法解析为期望类型
        """
        config = await SystemConfigService.get_config(db, key)  # pyright: ignore
        raw_value = config.value if config else None  # pyright: ignore

        # 如果配置不存在且有默认值，返回默认值
        if raw_value is None or not str(raw_value).strip():  # pyright: ignore
            if default is not None:
                return default
            # 检查是否允许空值
            spec = self._gateway.resolve_spec(key)
            if spec and not spec.allow_empty:
                raise ConfigParseError(f"配置 '{key}' 不能为空")
            return None

        return self._parse_value(
            key, raw_value, expected_type)  # pyright: ignore

    async def get_int(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],  # pyright: ignore
        key: str,
        default: int | None = None,
    ) -> int | None:
        """获取整数配置"""
        return await self.get_typed(db, key, ConfigValueType.INT, default)

    async def get_float(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],  # pyright: ignore
        key: str,
        default: float | None = None,
    ) -> float | None:
        """获取浮点数配置"""
        return await self.get_typed(db, key, ConfigValueType.FLOAT, default)

    async def get_bool(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],  # pyright: ignore
        key: str,
        default: bool | None = None,
    ) -> bool | None:
        """获取布尔配置"""
        return await self.get_typed(db, key, ConfigValueType.BOOL, default)

    async def get_str(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],  # pyright: ignore
        key: str,
        default: str | None = None,
    ) -> str | None:
        """获取字符串配置"""
        return await self.get_typed(db, key, ConfigValueType.STRING, default)

    # pyright: ignore
    async def get_json(self, db: Annotated[AsyncSession, Depends(
            get_db)], key: str, default: dict | list | None = None) -> dict | list | None:
        """获取 JSON 配置"""
        raw = await self.get_typed(db, key, ConfigValueType.JSON, None)  # pyright: ignore
        if raw is None:
            return default  # pyright: ignore
        if isinstance(raw, (dict, list)):
            return raw  # pyright: ignore
        try:
            return json.loads(raw)  # pyright: ignore
        except (json.JSONDecodeError, TypeError):
            return default  # pyright: ignore

    async def get_required_int(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],  # pyright: ignore
        key: str,
    ) -> int:  # pyright: ignore
        """获取必需的整数配置（不存在则抛出异常）"""
        result = await self.get_typed(db, key, ConfigValueType.INT)
        if result is None:
            raise ConfigParseError(f"配置 '{key}' 不存在或无法解析为整数")
        return result  # pyright: ignore

    async def get_required_bool(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],  # pyright: ignore
        key: str,
    ) -> bool:  # pyright: ignore
        """获取必需的布尔配置"""
        result = await self.get_typed(db, key, ConfigValueType.BOOL)
        if result is None:
            raise ConfigParseError(f"配置 '{key}' 不存在或无法解析为布尔值")
        return result  # pyright: ignore

    def _parse_value(
        self,
        key: str,
        raw_value: str,
        expected_type: ConfigValueType,
    ) -> Any:
        """解析配置值"""
        try:
            if expected_type == ConfigValueType.STRING:
                return raw_value
            elif expected_type == ConfigValueType.INT:
                return _parse_int(raw_value)
            elif expected_type == ConfigValueType.FLOAT:
                return _parse_float(raw_value)
            elif expected_type == ConfigValueType.BOOL:
                return _parse_bool(raw_value)
            elif expected_type == ConfigValueType.JSON:
                return json.loads(raw_value)
            elif expected_type == ConfigValueType.JSON_B64:
                import base64
                decoded = base64.b64decode(raw_value).decode("utf-8")
                return json.loads(decoded)
            else:
                return raw_value
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"配置 '{key}' 解析失败: {e}")
            raise ConfigParseError(
                f"配置 '{key}' 无法解析为 {expected_type.value}: {e}")


class ConfigDomain(BaseModel):
    """配置域模型 - 用于管理特定域的配置"""
    model_config = {"arbitrary_types_allowed": True}

    domain: str
    configs: list[SystemConfig] = Field(default_factory=list)


class UnifiedConfigService:
    """统一配置服务 - 提供配置管理和验证的聚合接口"""

    def __init__(self) -> None:
        self._typed_service = TypedConfigService()
        self._gateway = config_gateway

    async def validate_and_set(self, db: Annotated[AsyncSession, Depends(get_db)], key: str, value: str | None, description: str | None = None, category: str = "general", updated_by: int | None = None) -> SystemConfig:  # pyright: ignore
        """验证并设置配置

        Args:
            db: 数据库会话
            key: 配置键
            value: 配置值
            description: 描述
            category: 分类
            updated_by: 更新者ID

        Returns:
            更新后的配置

        Raises:
            ValueError: 值无法通过 schema 校验
        """
        # 使用 ConfigGateway 验证值
        self._gateway.validate_value(key, value)

        # 自动确定 category（如果未提供）
        effective_category = category
        if effective_category is None or effective_category == "":
            effective_category = self._gateway.normalize_category(
                key, "general")
            if effective_category is None:
                effective_category = "general"

        return await SystemConfigService.set_config(  # pyright: ignore
            db=db,
            key=key,
            value=value,
            description=description,
            category=effective_category,
            updated_by=updated_by,
        )

    # pyright: ignore
    async def get_by_domain(self, db: Annotated[AsyncSession, Depends(
            get_db)], domain: str) -> list[SystemConfig]:
        """获取指定域的所有配置

        Args:
            db: 数据库会话
            domain: 配置域（如: system, news_ai, ai, payment）

        Returns:
            该域的配置列表
        """
        configs = await SystemConfigService.get_all_configs(db, category=domain)  # pyright: ignore

        # 如果 category 不匹配，尝试通过 key 前缀过滤
        if not configs:
            # pyright: ignore
            all_configs = await SystemConfigService.get_all_configs(db)
            prefix = f"{domain}." if "." not in domain else domain.rstrip(
                ".") + "."
            configs = [c for c in all_configs if c.key.startswith(
                prefix)]  # pyright: ignore

        return configs  # pyright: ignore

    def list_specs_by_domain(self, domain: str) -> list:  # pyright: ignore
        """列出指定域的所有配置规格

        Args:
            domain: 配置域

        Returns:
            该域的配置规格列表
        """
        return [spec for spec in self._gateway.iter_specs(
        ) if spec.domain == domain]  # pyright: ignore

    def get_domain_schema(self, domain: str) -> dict:  # pyright: ignore
        """获取域的 schema 概要

        Args:
            domain: 配置域

        Returns:
            包含 keys, descriptions 的字典
        """
        specs = self.list_specs_by_domain(domain)  # pyright: ignore
        return {
            "domain": domain,
            "keys": [spec.key for spec in specs],  # pyright: ignore
            "count": len(specs),  # pyright: ignore
            "schema": {
                spec.key: {  # pyright: ignore
                    "type": spec.value_type.value,  # pyright: ignore
                    "description": spec.description,  # pyright: ignore
                    "allow_empty": spec.allow_empty,  # pyright: ignore
                }
                for spec in specs  # pyright: ignore
            },
        }


# 便捷实例
typed_config_service = TypedConfigService()
unified_config_service = UnifiedConfigService()
