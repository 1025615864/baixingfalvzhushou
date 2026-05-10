"""Unified configuration service."""
from __future__ import annotations
import base64
import json
import enum
from typing import Optional, Any
from dataclasses import dataclass, field


class ConfigParseError(ValueError):
    pass


class ConfigValueType(enum.Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    JSON = "json"
    JSON_B64 = "json_b64"


@dataclass
class ConfigDomain:
    domain: str
    configs: list = field(default_factory=list)


@dataclass
class ConfigSpec:
    key: str
    value_type: ConfigValueType = ConfigValueType.STRING
    default: Any = None
    description: str = ""
    allow_empty: bool = True
    category: str = "general"


class ConfigGateway:
    def __init__(self):
        self._specs: dict[str, ConfigSpec] = {
            "system.debug": ConfigSpec(key="system.debug", value_type=ConfigValueType.BOOL, default=False, description="调试模式", category="system"),
            "system.log_level": ConfigSpec(key="system.log_level", value_type=ConfigValueType.STRING, default="INFO", description="日志级别", category="system"),
            "system.max_upload_size": ConfigSpec(key="system.max_upload_size", value_type=ConfigValueType.INT, default=10485760, description="最大上传大小", category="system"),
        }

    def resolve_spec(self, key: str) -> Optional[ConfigSpec]:
        return self._specs.get(key)

    def validate_value(self, key: str, value: Any) -> bool:
        return True

    def normalize_category(self, category: str) -> str:
        return category if category else "general"


class TypedConfigService:
    def __init__(self, gateway: Optional[ConfigGateway] = None):
        self._gateway = gateway or ConfigGateway()

    def _parse_value(self, key: str, raw_value: str, value_type: ConfigValueType) -> Any:
        if raw_value is None:
            raise ConfigParseError(f"配置 {key} 值为空")
        raw = str(raw_value).strip()
        if value_type == ConfigValueType.STRING:
            return raw
        elif value_type == ConfigValueType.INT:
            try:
                return int(raw)
            except (ValueError, TypeError):
                raise ConfigParseError(f"配置 {key} 无法解析为整数: {raw_value}")
        elif value_type == ConfigValueType.FLOAT:
            try:
                return float(raw)
            except (ValueError, TypeError):
                raise ConfigParseError(f"配置 {key} 无法解析为浮点数: {raw_value}")
        elif value_type == ConfigValueType.BOOL:
            return raw.lower() in ("true", "1", "yes", "on")
        elif value_type == ConfigValueType.JSON:
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                raise ConfigParseError(f"配置 {key} 无法解析为JSON: {raw_value}")
        elif value_type == ConfigValueType.JSON_B64:
            try:
                decoded = base64.b64decode(raw).decode("utf-8")
                return json.loads(decoded)
            except Exception:
                raise ConfigParseError(f"配置 {key} 无法解析为Base64 JSON: {raw_value}")
        return raw

    async def get_typed(self, db, key: str, value_type: ConfigValueType, default: Any = None) -> Any:
        from app.services.system_config_service import SystemConfigService
        config = await SystemConfigService.get_config(db, key)
        if config is None or config.value is None:
            return default
        spec = self._gateway.resolve_spec(key)
        if config.value == "" and spec and not spec.allow_empty:
            raise ConfigParseError(f"配置 {key} 不能为空")
        try:
            return self._parse_value(key, config.value, value_type)
        except ConfigParseError:
            return default

    async def get_int(self, db, key: str, default: int = 0) -> int:
        return await self.get_typed(db, key, ConfigValueType.INT, default=default)

    async def get_float(self, db, key: str, default: float = 0.0) -> float:
        return await self.get_typed(db, key, ConfigValueType.FLOAT, default=default)

    async def get_bool(self, db, key: str, default: bool = False) -> bool:
        return await self.get_typed(db, key, ConfigValueType.BOOL, default=default)

    async def get_str(self, db, key: str, default: str = "") -> str:
        return await self.get_typed(db, key, ConfigValueType.STRING, default=default)

    async def get_json(self, db, key: str, default: Any = None) -> Any:
        return await self.get_typed(db, key, ConfigValueType.JSON, default=default)

    async def get_required_int(self, db, key: str) -> int:
        from app.services.system_config_service import SystemConfigService
        config = await SystemConfigService.get_config(db, key)
        if config is None or config.value is None:
            raise ConfigParseError(f"配置 {key} 不存在或无法解析")
        return self._parse_value(key, config.value, ConfigValueType.INT)

    async def get_required_bool(self, db, key: str) -> bool:
        from app.services.system_config_service import SystemConfigService
        config = await SystemConfigService.get_config(db, key)
        if config is None or config.value is None:
            raise ConfigParseError(f"配置 {key} 不存在或无法解析")
        return self._parse_value(key, config.value, ConfigValueType.BOOL)


@dataclass
class UnifiedConfigEntry:
    key: str
    value: Any
    source: str = "default"
    version: int = 1


class UnifiedConfigService:
    def __init__(self):
        self._entries: dict[str, UnifiedConfigEntry] = {}
        self._version = 1
        self._typed_service = TypedConfigService()
        self._gateway = ConfigGateway()

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._entries.get(key)
        if entry is None:
            return default
        return entry.value

    def set(self, key: str, value: Any, source: str = "manual") -> UnifiedConfigEntry:
        existing = self._entries.get(key)
        version = (existing.version + 1) if existing else 1
        entry = UnifiedConfigEntry(key=key, value=value, source=source, version=version)
        self._entries[key] = entry
        self._version += 1
        return entry

    def delete(self, key: str) -> bool:
        if key in self._entries:
            del self._entries[key]
            self._version += 1
            return True
        return False

    def list_entries(self) -> list[UnifiedConfigEntry]:
        return list(self._entries.values())

    def get_version(self) -> int:
        return self._version

    def reload(self) -> dict:
        self._version += 1
        return {"reloaded": True, "version": self._version}

    def list_specs_by_domain(self, domain: str) -> list[ConfigSpec]:
        return [spec for spec in self._gateway._specs.values() if spec.key.startswith(f"{domain}.")]

    def get_domain_schema(self, domain: str) -> dict:
        specs = self.list_specs_by_domain(domain)
        return {
            "domain": domain,
            "keys": [{"key": s.key, "type": s.value_type.value, "default": s.default, "description": s.description} for s in specs],
            "count": len(specs),
            "schema": {s.key: {"type": s.value_type.value, "default": s.default} for s in specs},
        }

    async def validate_and_set(self, db, key: str, value: Any, description: str = "", category: str = "", updated_by: int = 0) -> Any:
        self._gateway.validate_value(key, value)
        normalized_category = self._gateway.normalize_category(category)
        from app.services.system_config_service import SystemConfigService
        result = await SystemConfigService.set_config(db, key, str(value), description=description, category=normalized_category, updated_by=updated_by)
        return result

    async def get_by_domain(self, db, domain: str) -> list:
        from app.services.system_config_service import SystemConfigService
        all_configs = await SystemConfigService.get_all_configs(db)
        return [c for c in all_configs if getattr(c, 'key', '').startswith(f"{domain}.")]


unified_config_service = UnifiedConfigService()
