"""System configuration service."""
from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass, field


@dataclass
class ConfigItem:
    key: str
    value: Any
    description: str = ""
    category: str = "general"
    is_public: bool = False


class SystemConfigService:
    def __init__(self):
        self._configs: dict[str, ConfigItem] = {}

    def get(self, key: str, default: Any = None) -> Any:
        item = self._configs.get(key)
        if item is None:
            return default
        return item.value

    def set(self, key: str, value: Any, description: str = "", category: str = "general", is_public: bool = False) -> ConfigItem:
        item = ConfigItem(key=key, value=value, description=description, category=category, is_public=is_public)
        self._configs[key] = item
        return item

    def delete(self, key: str) -> bool:
        if key in self._configs:
            del self._configs[key]
            return True
        return False

    def list_configs(self, category: Optional[str] = None) -> list[ConfigItem]:
        configs = list(self._configs.values())
        if category:
            configs = [c for c in configs if c.category == category]
        return configs

    def get_public_configs(self) -> list[ConfigItem]:
        return [c for c in self._configs.values() if c.is_public]

    def bulk_set(self, configs: dict[str, Any]) -> list[ConfigItem]:
        results = []
        for key, value in configs.items():
            results.append(self.set(key, value))
        return results


def _mask_secret_value(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    if len(value) <= 4:
        return "****"
    return value[:2] + "****" + value[-2:]


class SystemSecretService:
    def __init__(self):
        self._secrets: dict[str, str] = {}

    def set_secret(self, key: str, value: str) -> None:
        self._secrets[key] = value

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._secrets.get(key, default)

    def delete_secret(self, key: str) -> bool:
        if key in self._secrets:
            del self._secrets[key]
            return True
        return False

    def mask_secret(self, key: str) -> Optional[str]:
        value = self._secrets.get(key)
        return _mask_secret_value(value)


system_config_service = SystemConfigService()
