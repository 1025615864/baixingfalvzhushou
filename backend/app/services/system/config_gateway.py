"""Configuration gateway service."""
from __future__ import annotations
import enum
import json
import base64
from typing import Optional, Any
from dataclasses import dataclass, field


class ConfigValueType(enum.Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    JSON = "json"
    JSON_B64 = "json_b64"


@dataclass
class ConfigKeySpec:
    key: str
    value_type: ConfigValueType = ConfigValueType.STRING
    default: Any = None
    description: str = ""
    required: bool = False


@dataclass
class PrefixConfigSpec:
    prefix: str
    value_type: ConfigValueType = ConfigValueType.STRING
    default: Any = None
    description: str = ""


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


def _parse_int(value: Any) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _parse_float(value: Any) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _validate_json(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


def _validate_json_b64(value: Any) -> Any:
    if isinstance(value, str):
        decoded = base64.b64decode(value).decode("utf-8")
        return json.loads(decoded)
    return value


_CONFIG_SPECS: dict[str, ConfigKeySpec] = {}
_PREFIX_SPECS: list[PrefixConfigSpec] = []


class ConfigGateway:
    def __init__(self):
        self._backends: dict[str, dict] = {}
        self._routes: dict[str, str] = {}

    def register_backend(self, name: str, backend: Any) -> None:
        self._backends[name] = {"instance": backend}

    def set_route(self, key_prefix: str, backend_name: str) -> None:
        self._routes[key_prefix] = backend_name

    def get(self, key: str, default: Any = None) -> Any:
        for prefix, backend_name in self._routes.items():
            if key.startswith(prefix):
                backend = self._backends.get(backend_name, {}).get("instance")
                if backend and hasattr(backend, "get"):
                    return backend.get(key, default)
        return default

    def set(self, key: str, value: Any) -> None:
        for prefix, backend_name in self._routes.items():
            if key.startswith(prefix):
                backend = self._backends.get(backend_name, {}).get("instance")
                if backend and hasattr(backend, "set"):
                    backend.set(key, value)
                    return

    def list_backends(self) -> list[str]:
        return list(self._backends.keys())


config_gateway = ConfigGateway()
