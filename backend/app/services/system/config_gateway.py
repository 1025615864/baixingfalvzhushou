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
    domain: str = ""
    value_type: ConfigValueType = ConfigValueType.STRING
    default: Any = None
    category: str = ""
    description: str = ""
    required: bool = False
    allow_empty: bool = True


@dataclass
class PrefixConfigSpec:
    prefix: str
    domain: str = ""
    value_type: ConfigValueType = ConfigValueType.STRING
    default: Any = None
    category: str = ""
    description: str = ""
    allow_empty: bool = True


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ("true", "1", "yes", "y", "on"):
            return True
        if value.lower() in ("false", "0", "no", "n", "off"):
            return False
        raise ValueError(f"value must be a boolean value, got: {value!r}")
    return bool(value)


def _parse_int(value: Any) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        try:
            return int(float(str(value).strip()))
        except (ValueError, TypeError):
            raise ValueError(f"value must be an integer, got: {value!r}")


def _parse_float(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        raise ValueError(f"value must be a number, got: {value!r}")


def _validate_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            raise ValueError(f"value must be valid JSON, got: {value!r}")
    return value


def _validate_json_b64(value: Any) -> Any:
    if isinstance(value, str):
        try:
            decoded = base64.b64decode(value).decode("utf-8")
        except Exception:
            raise ValueError(f"value must be base64-encoded JSON, got: {value!r}")
        try:
            return json.loads(decoded)
        except (json.JSONDecodeError, ValueError):
            raise ValueError(f"value must be valid JSON, got decoded: {decoded!r}")
    return value


_CONFIG_SPECS: tuple[ConfigKeySpec, ...] = (
    ConfigKeySpec(
        key="FREE_AI_CHAT_DAILY_LIMIT",
        domain="ai",
        value_type=ConfigValueType.INT,
        default=10,
        category="quota",
        description="Free user daily AI chat limit",
    ),
    ConfigKeySpec(
        key="VIP_AI_CHAT_DAILY_LIMIT",
        domain="ai",
        value_type=ConfigValueType.INT,
        default=100,
        category="quota",
        description="VIP user daily AI chat limit",
    ),
    ConfigKeySpec(
        key="AI_PROMPT_VERSION_DEFAULT",
        domain="ai",
        value_type=ConfigValueType.STRING,
        default="v1.0",
        category="ai",
        description="Default AI prompt version",
        allow_empty=True,
    ),
    ConfigKeySpec(
        key="VIP_DEFAULT_PRICE",
        domain="payment",
        value_type=ConfigValueType.FLOAT,
        default=29.9,
        category="payment",
        description="Default VIP subscription price",
    ),
    ConfigKeySpec(
        key="enable_notifications",
        domain="system",
        value_type=ConfigValueType.BOOL,
        default=True,
        category="system",
        description="Enable notification system",
    ),
    ConfigKeySpec(
        key="CONSULT_REVIEW_SLA_JSON",
        domain="consult",
        value_type=ConfigValueType.JSON,
        default={},
        category="consult",
        description="Consultation review SLA configuration as JSON",
    ),
    ConfigKeySpec(
        key="NEWS_AI_SUMMARY_LLM_PROVIDERS_B64",
        domain="news",
        value_type=ConfigValueType.JSON_B64,
        default={},
        category="news",
        description="News AI summary LLM providers config (base64-encoded JSON)",
    ),
)

_PREFIX_SPECS: list[PrefixConfigSpec] = [
    PrefixConfigSpec(
        prefix="SHERPA_ONNX_",
        domain="voice",
        value_type=ConfigValueType.STRING,
        category="voice",
        description="Sherpa ONNX voice configuration",
    ),
]


class ConfigGateway:
    def __init__(self):
        self._backends: dict[str, dict] = {}
        self._routes: dict[str, str] = {}
        self._spec_map: dict[str, ConfigKeySpec] = {s.key: s for s in _CONFIG_SPECS}

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

    def resolve_spec(self, key: str) -> Optional[ConfigKeySpec | PrefixConfigSpec]:
        if not key:
            return None
        if key in self._spec_map:
            return self._spec_map[key]
        for prefix_spec in _PREFIX_SPECS:
            if key.startswith(prefix_spec.prefix):
                return prefix_spec
        return None

    def normalize_category(self, key: str, fallback: Optional[str] = None) -> Optional[str]:
        spec = self.resolve_spec(key)
        if spec is not None:
            category = getattr(spec, "category", None)
            if category:
                return category
        return fallback

    def validate_value(self, key: str, value: Any) -> None:
        spec = self.resolve_spec(key)
        if spec is None:
            return
        if not getattr(spec, "allow_empty", True) and (value is None or value == ""):
            raise ValueError("value cannot be empty")
        vt = spec.value_type
        if vt == ConfigValueType.STRING:
            pass
        elif vt == ConfigValueType.INT:
            _parse_int(value)
        elif vt == ConfigValueType.FLOAT:
            _parse_float(value)
        elif vt == ConfigValueType.BOOL:
            _parse_bool(value)
        elif vt == ConfigValueType.JSON:
            _validate_json(value)
        elif vt == ConfigValueType.JSON_B64:
            _validate_json_b64(value)

    def iter_specs(self):
        return iter(self._spec_map.values())


config_gateway = ConfigGateway()
