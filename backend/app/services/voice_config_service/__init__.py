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


class _SettingsOverlay:
    def __init__(self, base: Any, overrides: dict):
        object.__setattr__(self, "_base", base)
        object.__setattr__(self, "_overrides", overrides)

    def __getattr__(self, name: str) -> Any:
        overrides = object.__getattribute__(self, "_overrides")
        if name in overrides:
            return overrides[name]
        return getattr(object.__getattribute__(self, "_base"), name)


_VOICE_CONFIG_PREFIXES = ("SHERPA_", "VOICE_")


async def load_voice_config_overrides(db_session: Any) -> dict[str, str]:
    overrides = {}
    try:
        from sqlalchemy import select
        from app.models.system import SystemConfig
        result = await db_session.execute(select(SystemConfig.key, SystemConfig.value))
        rows = result.all()
        for key, value in rows:
            if key and any(key.startswith(p) for p in _VOICE_CONFIG_PREFIXES):
                overrides[key] = value
    except Exception:
        pass
    return overrides


async def get_effective_voice_settings(db_session: Any, base_settings: Any) -> tuple[Any, dict[str, str], bool]:
    overrides = await load_voice_config_overrides(db_session)
    force_enabled = _parse_bool(getattr(base_settings, "voice_transcribe_force_enabled", False))
    if not force_enabled:
        return base_settings, {}, False
    settings = _SettingsOverlay(base_settings, overrides)
    sherpa_enabled = _parse_bool(overrides.get("SHERPA_ASR_ENABLED", getattr(base_settings, "sherpa_asr_enabled", False)))
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
