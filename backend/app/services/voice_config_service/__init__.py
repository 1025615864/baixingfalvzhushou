"""Voice configuration service."""
from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass, field


def _parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _parse_int(value: Any, default: int = 0) -> int:
    if value is None or isinstance(value, bool):
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _parse_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


_VALID_PROVIDERS = {"openai", "sherpa", "auto"}
_VALID_MODES = {"local", "remote", "off"}


def _normalize_provider(value: Any) -> str:
    s = str(value or "").strip().lower()
    if not s:
        return "auto"
    return s if s in _VALID_PROVIDERS else "auto"


def _normalize_mode(value: Any) -> str:
    s = str(value or "").strip().lower()
    if not s:
        return "off"
    return s if s in _VALID_MODES else "off"


_ATTR_TO_OVERRIDE_KEY = {
    "voice_transcribe_provider": "VOICE_TRANSCRIBE_PROVIDER",
    "voice_transcribe_force_enabled": "VOICE_TRANSCRIBE_FORCE_ENABLED",
    "sherpa_asr_mode": "SHERPA_ASR_MODE",
    "sherpa_asr_enabled": "SHERPA_ASR_ENABLED",
    "sherpa_onnx_num_threads": "SHERPA_ONNX_NUM_THREADS",
    "sherpa_onnx_debug": "SHERPA_ONNX_DEBUG",
    "sherpa_onnx_sample_rate": "SHERPA_ONNX_SAMPLE_RATE",
    "sherpa_onnx_feature_dim": "SHERPA_ONNX_FEATURE_DIM",
}

_NORMALIZE_PROVIDER_KEYS = {"VOICE_TRANSCRIBE_PROVIDER", "voice_transcribe_provider"}
_NORMALIZE_MODE_KEYS = {"SHERPA_ASR_MODE", "sherpa_asr_mode"}
_PARSE_BOOL_KEYS = {"SHERPA_ASR_ENABLED", "SHERPA_ONNX_DEBUG", "sherpa_asr_enabled", "sherpa_onnx_debug"}
_PARSE_INT_KEYS = {"SHERPA_ONNX_NUM_THREADS", "SHERPA_ONNX_SAMPLE_RATE", "SHERPA_ONNX_FEATURE_DIM",
                   "sherpa_onnx_num_threads", "sherpa_onnx_sample_rate", "sherpa_onnx_feature_dim"}


class _SettingsOverlay:
    def __init__(self, base: Any, overrides: dict):
        object.__setattr__(self, "_base", base)
        object.__setattr__(self, "_overrides", overrides)

    def __getattr__(self, name: str) -> Any:
        overrides = object.__getattribute__(self, "_overrides")
        override_key = _ATTR_TO_OVERRIDE_KEY.get(name, name)
        key = name if name in overrides else (override_key if override_key in overrides else None)
        if key is not None:
            raw = overrides[key]
            if key in _NORMALIZE_PROVIDER_KEYS:
                return _normalize_provider(raw)
            if key in _NORMALIZE_MODE_KEYS:
                return _normalize_mode(raw)
            if key in _PARSE_BOOL_KEYS:
                return _parse_bool(raw)
            if key in _PARSE_INT_KEYS:
                return _parse_int(raw)
            return raw
        base = object.__getattribute__(self, "_base")
        raw = getattr(base, name, None)
        if name in _NORMALIZE_PROVIDER_KEYS:
            return _normalize_provider(raw)
        if name in _NORMALIZE_MODE_KEYS:
            return _normalize_mode(raw)
        return raw


_VOICE_CONFIG_PREFIXES = ("SHERPA_", "VOICE_")


async def load_voice_config_overrides(db_session: Any) -> dict[str, str]:
    overrides = {}
    from sqlalchemy import select
    from app.models.system import SystemConfig
    result = await db_session.execute(select(SystemConfig.key, SystemConfig.value))
    rows = result.all()
    for row in rows:
        key = row[0]
        value = row[1]
        if key and any(key.startswith(p) for p in _VOICE_CONFIG_PREFIXES):
            overrides[key] = value
    return overrides


async def get_effective_voice_settings(db_session: Any, base_settings: Any) -> tuple[Any, dict[str, str], bool]:
    import os
    overrides = await load_voice_config_overrides(db_session)
    env_force = os.environ.get("VOICE_TRANSCRIBE_FORCE_ENABLED", "")
    force_enabled = _parse_bool(env_force) or _parse_bool(getattr(base_settings, "voice_transcribe_force_enabled", False)) or _parse_bool(overrides.get("VOICE_TRANSCRIBE_FORCE_ENABLED", ""))
    if not force_enabled:
        return base_settings, {}, False

    cleaned_overrides = {}
    for k, v in overrides.items():
        sv = str(v or "").strip()
        if sv:
            cleaned_overrides[k] = sv

    settings = _SettingsOverlay(base_settings, cleaned_overrides)
    sherpa_enabled = _parse_bool(cleaned_overrides.get("SHERPA_ASR_ENABLED", getattr(base_settings, "sherpa_asr_enabled", False)))
    return settings, overrides, sherpa_enabled


@dataclass
class VoiceConfig:
    id: str
    user_id: int
    voice_name: str = "default"
    language: str = "zh"
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    provider: str = "default"


class VoiceConfigService:
    def __init__(self):
        self._configs: dict[str, VoiceConfig] = {}
        self._next_id = 1

    async def create_config(self, user_id: int, voice_name: str = "default", language: str = "zh", speed: float = 1.0, pitch: float = 1.0, volume: float = 1.0, provider: str = "default") -> VoiceConfig:
        config_id = f"vc_{self._next_id}"
        self._next_id += 1
        config = VoiceConfig(id=config_id, user_id=user_id, voice_name=voice_name, language=language, speed=speed, pitch=pitch, volume=volume, provider=provider)
        self._configs[config_id] = config
        return config

    async def get_config(self, config_id: str) -> Optional[VoiceConfig]:
        return self._configs.get(config_id)

    async def get_user_config(self, user_id: int) -> Optional[VoiceConfig]:
        for config in self._configs.values():
            if config.user_id == user_id:
                return config
        return None

    async def update_config(self, config_id: str, **kwargs) -> Optional[VoiceConfig]:
        config = self._configs.get(config_id)
        if not config:
            return None
        for k, v in kwargs.items():
            if hasattr(config, k):
                setattr(config, k, v)
        return config

    async def delete_config(self, config_id: str) -> bool:
        if config_id in self._configs:
            del self._configs[config_id]
            return True
        return False

    async def list_configs(self, user_id: Optional[int] = None) -> list[VoiceConfig]:
        configs = list(self._configs.values())
        if user_id:
            configs = [c for c in configs if c.user_id == user_id]
        return configs


voice_config_service = VoiceConfigService()
