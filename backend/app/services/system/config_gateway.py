
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ConfigValueType(str, Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    JSON = "json"
    JSON_B64 = "json_b64"


@dataclass(frozen=True)
class ConfigKeySpec:
    key: str
    domain: str
    value_type: ConfigValueType
    category: str
    description: str = ""
    allow_empty: bool = True


@dataclass(frozen=True)
class PrefixConfigSpec:
    prefix: str
    domain: str
    value_type: ConfigValueType
    category: str
    description: str = ""
    allow_empty: bool = True


_BOOL_TRUE = {"1", "true", "yes", "y", "on"}
_BOOL_FALSE = {"0", "false", "no", "n", "off"}


def _parse_bool(raw: str) -> bool:
    value = str(raw).strip().lower()
    if value in _BOOL_TRUE:
        return True
    if value in _BOOL_FALSE:
        return False
    raise ValueError("must be a boolean value")


def _parse_int(raw: str) -> int:
    try:
        return int(float(str(raw).strip()))
    except Exception as exc:
        raise ValueError("must be an integer") from exc


def _parse_float(raw: str) -> float:
    try:
        return float(str(raw).strip())
    except Exception as exc:
        raise ValueError("must be a number") from exc


def _validate_json(raw: str) -> None:
    try:
        json.loads(raw)
    except Exception as exc:
        raise ValueError("must be valid JSON") from exc


def _validate_json_b64(raw: str) -> None:
    try:
        decoded = base64.b64decode(str(raw).strip()).decode("utf-8")
    except Exception as exc:
        raise ValueError("must be base64-encoded JSON") from exc
    _validate_json(decoded)


class ConfigGateway:
    def __init__(self) -> None:
        self._spec_map = {spec.key: spec for spec in _CONFIG_SPECS}
        self._prefix_specs = list(_PREFIX_SPECS)

    def resolve_spec(
            self, key: str) -> ConfigKeySpec | PrefixConfigSpec | None:
        normalized = str(key or "").strip()
        if not normalized:
            return None
        spec = self._spec_map.get(normalized)
        if spec is not None:
            return spec
        for prefix_spec in self._prefix_specs:
            if normalized.startswith(prefix_spec.prefix):
                return prefix_spec
        return None

    def normalize_category(self, key: str, fallback: str | None) -> str | None:
        spec = self.resolve_spec(key)
        if spec is None:
            return fallback
        return spec.category or fallback

    def validate_value(self, key: str, value: str | None) -> None:
        spec = self.resolve_spec(key)
        if spec is None:
            return
        if value is None or not str(value).strip():
            if spec.allow_empty:
                return
            raise ValueError("value cannot be empty")

        raw = str(value).strip()
        if spec.value_type == ConfigValueType.STRING:
            return
        if spec.value_type == ConfigValueType.INT:
            _parse_int(raw)
            return
        if spec.value_type == ConfigValueType.FLOAT:
            _parse_float(raw)
            return
        if spec.value_type == ConfigValueType.BOOL:
            _parse_bool(raw)
            return
        if spec.value_type == ConfigValueType.JSON:
            _validate_json(raw)
            return
        if spec.value_type == ConfigValueType.JSON_B64:
            _validate_json_b64(raw)
            return

    def iter_specs(self) -> Iterable[ConfigKeySpec]:
        return self._spec_map.values()


_CONFIG_SPECS = (
    ConfigKeySpec(
        key="FREE_AI_CHAT_DAILY_LIMIT",
        domain="quota",
        value_type=ConfigValueType.INT,
        category="quota",
        description="Daily AI chat limit for free users",
    ),
    ConfigKeySpec(
        key="VIP_AI_CHAT_DAILY_LIMIT",
        domain="quota",
        value_type=ConfigValueType.INT,
        category="quota",
        description="Daily AI chat limit for VIP users",
    ),
    ConfigKeySpec(
        key="FREE_DOCUMENT_GENERATE_DAILY_LIMIT",
        domain="quota",
        value_type=ConfigValueType.INT,
        category="quota",
        description="Daily document generate limit for free users",
    ),
    ConfigKeySpec(
        key="VIP_DOCUMENT_GENERATE_DAILY_LIMIT",
        domain="quota",
        value_type=ConfigValueType.INT,
        category="quota",
        description="Daily document generate limit for VIP users",
    ),
    ConfigKeySpec(
        key="CONSULT_REVIEW_SLA_JSON",
        domain="review",
        value_type=ConfigValueType.JSON,
        category="review",
        description="Review SLA configuration JSON",
    ),
    ConfigKeySpec(
        key="enable_notifications",
        domain="notification",
        value_type=ConfigValueType.BOOL,
        category="notification",
        description="Global notification switch",
    ),
    ConfigKeySpec(
        key="AI_PROMPT_VERSION_DEFAULT",
        domain="ai",
        value_type=ConfigValueType.STRING,
        category="ai",
        description="Default AI prompt version",
    ),
    ConfigKeySpec(
        key="AI_PROMPT_VERSION_V2",
        domain="ai",
        value_type=ConfigValueType.STRING,
        category="ai",
        description="AI prompt v2 version label",
    ),
    ConfigKeySpec(
        key="AI_PROMPT_VERSION_V2_PERCENT",
        domain="ai",
        value_type=ConfigValueType.INT,
        category="ai",
        description="AI prompt v2 rollout percent",
    ),
    ConfigKeySpec(
        key="VOICE_TRANSCRIBE_FORCE_ENABLED",
        domain="voice",
        value_type=ConfigValueType.BOOL,
        category="voice",
        description="Force voice config override",
    ),
    ConfigKeySpec(
        key="VOICE_TRANSCRIBE_PROVIDER",
        domain="voice",
        value_type=ConfigValueType.STRING,
        category="voice",
        description="Voice transcription provider",
    ),
    ConfigKeySpec(
        key="SHERPA_ASR_ENABLED",
        domain="voice",
        value_type=ConfigValueType.BOOL,
        category="voice",
        description="Enable Sherpa ASR",
    ),
    ConfigKeySpec(
        key="SHERPA_ASR_MODE",
        domain="voice",
        value_type=ConfigValueType.STRING,
        category="voice",
        description="Sherpa ASR mode",
    ),
    ConfigKeySpec(
        key="SHERPA_ASR_REMOTE_URL",
        domain="voice",
        value_type=ConfigValueType.STRING,
        category="voice",
        description="Sherpa ASR remote URL",
    ),
    ConfigKeySpec(
        key="SHERPA_ONNX_DEBUG",
        domain="voice",
        value_type=ConfigValueType.BOOL,
        category="voice",
        description="Sherpa ONNX debug switch",
    ),
    ConfigKeySpec(
        key="SHERPA_ONNX_NUM_THREADS",
        domain="voice",
        value_type=ConfigValueType.INT,
        category="voice",
        description="Sherpa ONNX num threads",
    ),
    ConfigKeySpec(
        key="SHERPA_ONNX_SAMPLE_RATE",
        domain="voice",
        value_type=ConfigValueType.INT,
        category="voice",
        description="Sherpa ONNX sample rate",
    ),
    ConfigKeySpec(
        key="SHERPA_ONNX_FEATURE_DIM",
        domain="voice",
        value_type=ConfigValueType.INT,
        category="voice",
        description="Sherpa ONNX feature dim",
    ),
    ConfigKeySpec(
        key="SHERPA_ONNX_WHISPER_TAIL_PADDINGS",
        domain="voice",
        value_type=ConfigValueType.INT,
        category="voice",
        description="Sherpa Whisper tail paddings",
    ),
    ConfigKeySpec(
        key="news_ai.summary_enabled",
        domain="news_ai",
        value_type=ConfigValueType.BOOL,
        category="news_ai",
        description="News AI summary switch",
    ),
    ConfigKeySpec(
        key="news_ai.batch_size",
        domain="news_ai",
        value_type=ConfigValueType.INT,
        category="news_ai",
        description="News AI batch size",
    ),
    ConfigKeySpec(
        key="news_ai.max_concurrent",
        domain="news_ai",
        value_type=ConfigValueType.INT,
        category="news_ai",
        description="News AI concurrency",
    ),
    ConfigKeySpec(
        key="forum.review.enabled",
        domain="forum",
        value_type=ConfigValueType.BOOL,
        category="forum",
        description="Forum comment review switch",
    ),
    ConfigKeySpec(
        key="forum.post_review.enabled",
        domain="forum",
        value_type=ConfigValueType.BOOL,
        category="forum",
        description="Forum post review switch",
    ),
    ConfigKeySpec(
        key="forum.post_review.mode",
        domain="forum",
        value_type=ConfigValueType.STRING,
        category="forum",
        description="Forum post review mode",
    ),
    ConfigKeySpec(
        key="forum.content_filter.sensitive_words",
        domain="forum",
        value_type=ConfigValueType.JSON,
        category="forum",
        description="Forum sensitive words list",
    ),
    ConfigKeySpec(
        key="forum.content_filter.ad_words",
        domain="forum",
        value_type=ConfigValueType.JSON,
        category="forum",
        description="Forum ad words list",
    ),
    ConfigKeySpec(
        key="forum.content_filter.ad_words_threshold",
        domain="forum",
        value_type=ConfigValueType.INT,
        category="forum",
        description="Forum ad words threshold",
    ),
    ConfigKeySpec(
        key="forum.content_filter.check_url",
        domain="forum",
        value_type=ConfigValueType.BOOL,
        category="forum",
        description="Forum check URL switch",
    ),
    ConfigKeySpec(
        key="forum.content_filter.check_phone",
        domain="forum",
        value_type=ConfigValueType.BOOL,
        category="forum",
        description="Forum check phone switch",
    ),
    ConfigKeySpec(
        key="AI_CHAT_PACK_OPTIONS_JSON",
        domain="payment",
        value_type=ConfigValueType.JSON,
        category="payment",
        description="AI chat pack options",
    ),
    ConfigKeySpec(
        key="DOCUMENT_GENERATE_PACK_OPTIONS_JSON",
        domain="payment",
        value_type=ConfigValueType.JSON,
        category="payment",
        description="Document generate pack options",
    ),
    ConfigKeySpec(
        key="VIP_DEFAULT_DAYS",
        domain="payment",
        value_type=ConfigValueType.INT,
        category="payment",
        description="VIP default days",
    ),
    ConfigKeySpec(
        key="VIP_DEFAULT_PRICE",
        domain="payment",
        value_type=ConfigValueType.FLOAT,
        category="payment",
        description="VIP default price",
    ),
    ConfigKeySpec(
        key="LIGHT_CONSULT_REVIEW_PRICE",
        domain="payment",
        value_type=ConfigValueType.FLOAT,
        category="payment",
        description="Light consult review price",
    ),
    ConfigKeySpec(
        key="WECHATPAY_PLATFORM_CERTS_JSON",
        domain="payment",
        value_type=ConfigValueType.JSON,
        category="payment",
        description="WeChatPay platform certs cache",
    ),
    ConfigKeySpec(
        key="CONTRACT_REVIEW_RULES_JSON",
        domain="contracts",
        value_type=ConfigValueType.JSON,
        category="contracts",
        description="Contract review rules",
    ),
    ConfigKeySpec(
        key="FAQ_PUBLIC_ITEMS_JSON",
        domain="faq",
        value_type=ConfigValueType.JSON,
        category="faq",
        description="Public FAQ items",
    ),
    ConfigKeySpec(
        key="EMAIL_SMTP_HOST",
        domain="email",
        value_type=ConfigValueType.STRING,
        category="email",
        description="SMTP host",
    ),
    ConfigKeySpec(
        key="EMAIL_SMTP_PORT",
        domain="email",
        value_type=ConfigValueType.INT,
        category="email",
        description="SMTP port",
    ),
    ConfigKeySpec(
        key="EMAIL_SMTP_USER",
        domain="email",
        value_type=ConfigValueType.STRING,
        category="email",
        description="SMTP user",
    ),
    ConfigKeySpec(
        key="EMAIL_FROM_EMAIL",
        domain="email",
        value_type=ConfigValueType.STRING,
        category="email",
        description="Email from address",
    ),
    ConfigKeySpec(
        key="EMAIL_FROM_NAME",
        domain="email",
        value_type=ConfigValueType.STRING,
        category="email",
        description="Email from name",
    ),
    ConfigKeySpec(
        key="EMAIL_SMTP_USE_TLS",
        domain="email",
        value_type=ConfigValueType.BOOL,
        category="email",
        description="SMTP use TLS",
    ),
    ConfigKeySpec(
        key="EMAIL_SMTP_START_TLS",
        domain="email",
        value_type=ConfigValueType.BOOL,
        category="email",
        description="SMTP start TLS",
    ),
)

_PREFIX_SPECS = (
    PrefixConfigSpec(
        prefix="NEWS_AI_SUMMARY_LLM_PROVIDERS_JSON",
        domain="news_ai",
        value_type=ConfigValueType.JSON,
        category="news_ai",
        description="News AI providers JSON",
    ),
    PrefixConfigSpec(
        prefix="NEWS_AI_SUMMARY_LLM_PROVIDERS_B64",
        domain="news_ai",
        value_type=ConfigValueType.JSON_B64,
        category="news_ai",
        description="News AI providers base64 JSON",
    ),
    PrefixConfigSpec(
        prefix="SHERPA_ONNX_",
        domain="voice",
        value_type=ConfigValueType.STRING,
        category="voice",
        description="Sherpa ONNX settings",
    ),
    PrefixConfigSpec(
        prefix="news_ai.",
        domain="news_ai",
        value_type=ConfigValueType.STRING,
        category="news_ai",
        description="News AI overrides",
    ),
)


config_gateway = ConfigGateway()
