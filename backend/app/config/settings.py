"""应用配置 - 按领域拆分为多个配置类"""
import os
import secrets
import sys
from datetime import timedelta
from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, Field, field_validator, model_validator
from functools import lru_cache


def _running_tests() -> bool:
    """检查是否在测试环境中运行"""
    return "pytest" in sys.modules


def _generate_test_secret() -> str:
    """生成随机测试密钥，避免硬编码密钥风险"""
    return "test-" + secrets.token_urlsafe(32)


def _resolve_env_files() -> list[str] | None:
    """解析环境文件路径"""
    if _running_tests():
        return None

    explicit = os.getenv("ENV_FILE", "").strip()
    if explicit:
        return [explicit]

    here = Path(__file__).resolve()
    backend_dir = here.parents[2]  # app/config/ -> app/ -> backend/
    repo_root = here.parents[3]    # -> repo root/

    candidates = [
        backend_dir / ".env.local",
        backend_dir / ".env",
        repo_root / ".env.local",
        repo_root / ".env",
    ]
    existing = [str(p) for p in candidates if p.exists()]
    return existing or None


# ==========================================
# 领域配置子类
# ==========================================

class AppConfig(BaseSettings):
    """应用基础配置"""
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(extra="ignore", env_file=_resolve_env_files())

    app_name: str = "百姓法律助手"
    debug: bool = Field(default_factory=_running_tests)
    frontend_base_url: str = "http://localhost:5173"


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(extra="ignore", env_file=_resolve_env_files())

    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/app.db",
        validation_alias=AliasChoices("DATABASE_URL", "DB_URL", "SQLALCHEMY_DATABASE_URL"),
    )


class SecurityConfig(BaseSettings):
    """安全配置 (JWT/CSRF/密钥)"""
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(extra="ignore", env_file=_resolve_env_files())

    # JWT
    jwt_audience: str | None = Field(default=None, validation_alias=AliasChoices("JWT_AUDIENCE", "JWT_AUD"))
    jwt_rsa_private_key: str = Field(
        default="",
        validation_alias=AliasChoices("JWT_RSA_PRIVATE_KEY", "JWT_PRIVATE_KEY"),
        json_schema_extra={"writeOnly": True},
    )
    jwt_rsa_public_key: str = Field(
        default="",
        validation_alias=AliasChoices("JWT_RSA_PUBLIC_KEY", "JWT_PUBLIC_KEY"),
        json_schema_extra={"writeOnly": True},
    )
    secret_key: str = Field(
        default_factory=lambda: _generate_test_secret() if _running_tests() else "",
        validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET_KEY"),
        json_schema_extra={"writeOnly": True},
    )
    algorithm: str = Field(default_factory=lambda: "HS256" if _running_tests() else "RS256")
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Rate limiting
    rate_limit_requests_per_minute: int = Field(default=60, validation_alias=AliasChoices("RATE_LIMIT_PER_MINUTE", "RATE_LIMIT_MINU"))
    rate_limit_requests_per_second: int = Field(default=10, validation_alias=AliasChoices("RATE_LIMIT_PER_SECOND", "RATE_LIMIT_SEC"))

    # CSRF
    csrf_secret_key: str = Field(
        default="",
        validation_alias=AliasChoices("CSRF_SECRET_KEY"),
        description="专用CSRF密钥，与JWT密钥分离，提升安全性",
        json_schema_extra={"writeOnly": True},
    )
    csrf_enabled: bool = Field(default=True, validation_alias=AliasChoices("CSRF_ENABLED"))
    csrf_token_expire_hours: int = Field(default=24, validation_alias=AliasChoices("CSRF_TOKEN_EXPIRE_HOURS"))
    csrf_token_size: int = Field(default=32, validation_alias=AliasChoices("CSRF_TOKEN_SIZE"))
    csrf_protected_methods: list[str] = Field(
        default=["POST", "PUT", "PATCH", "DELETE"],
        validation_alias=AliasChoices("CSRF_PROTECTED_METHODS"),
    )
    csrf_exempt_paths: list[str] = Field(
        default=[
            "/api/auth/login", "/api/auth/register", "/api/auth/refresh",
            "/api/user/login", "/api/user/register", "/api/user/logout",
        ],
        validation_alias=AliasChoices("CSRF_EXEMPT_PATHS"),
    )

    # Card encryption
    card_encryption_key: str = Field(
        default="",
        validation_alias=AliasChoices("CARD_ENCRYPTION_KEY", "BANK_CARD_KEY"),
        json_schema_extra={"writeOnly": True},
    )

    @model_validator(mode="after")
    def _validate_security(self):
        """验证生产环境安全配置"""
        if _running_tests():
            return self

        insecure_defaults = {
            "your-super-secret-key-change-in-production",
            "your-secret-key-change-in-production",
            "your-secret-key-here",
        }

        if not getattr(self, "debug", False):
            if self.algorithm == "RS256":
                if not self.jwt_rsa_private_key:
                    raise ValueError(
                        "SECURITY ERROR: JWT_RSA_PRIVATE_KEY must be set when using RS256. "
                        "Generate keys with: openssl genrsa -out private_key.pem 2048"
                    )
                if not self.jwt_rsa_public_key:
                    raise ValueError(
                        "SECURITY ERROR: JWT_RSA_PUBLIC_KEY must be set when using RS256."
                    )
            else:
                if not self.secret_key or self.secret_key in insecure_defaults or len(self.secret_key) < 32:
                    raise ValueError(
                        "SECURITY WARNING: HS256 is not recommended for production. "
                        "Consider upgrading to RS256."
                    )

            if not (self.csrf_secret_key and len(self.csrf_secret_key) >= 32):
                raise ValueError(
                    "SECURITY ERROR: CSRF_SECRET_KEY must be set with at least 32 characters in production. "
                    "Generate with: openssl rand -hex 32"
                )

        return self


class PaymentConfig(BaseSettings):
    """支付配置"""
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(extra="ignore", env_file=_resolve_env_files())

    payment_webhook_secret: str = Field(
        default="",
        validation_alias=AliasChoices("PAYMENT_WEBHOOK_SECRET", "PAYMENT_CALLBACK_SECRET"),
        json_schema_extra={"writeOnly": True},
    )

    # Alipay
    alipay_app_id: str = Field(default="", validation_alias=AliasChoices("ALIPAY_APP_ID", "PAY_ALIPAY_APP_ID"), json_schema_extra={"writeOnly": True})
    alipay_private_key: str = Field(default="", validation_alias=AliasChoices("ALIPAY_PRIVATE_KEY", "PAY_ALIPAY_PRIVATE_KEY"), json_schema_extra={"writeOnly": True})
    alipay_public_key: str = Field(default="", validation_alias=AliasChoices("ALIPAY_PUBLIC_KEY", "PAY_ALIPAY_PUBLIC_KEY"), json_schema_extra={"writeOnly": True})
    alipay_gateway_url: str = Field(default="https://openapi.alipay.com/gateway.do", validation_alias=AliasChoices("ALIPAY_GATEWAY_URL", "PAY_ALIPAY_GATEWAY_URL"))
    alipay_notify_url: str = Field(default="", validation_alias=AliasChoices("ALIPAY_NOTIFY_URL", "PAY_ALIPAY_NOTIFY_URL"))
    alipay_return_url: str = Field(default="", validation_alias=AliasChoices("ALIPAY_RETURN_URL", "PAY_ALIPAY_RETURN_URL"))
    alipay_callback_ips: list[str] = Field(
        default=["103.52.76.0/24", "103.52.77.0/24", "110.76.16.0/24", "110.76.17.0/24", "110.76.18.0/24", "110.76.19.0/24", "110.76.20.0/24", "110.76.21.0/24", "110.76.22.0/24", "110.76.23.0/24"],
        validation_alias=AliasChoices("ALIPAY_CALLBACK_IPS"),
    )

    # IkunPay
    ikunpay_pid: str = Field(default="", validation_alias=AliasChoices("IKUNPAY_PID", "PAY_IKUNPAY_PID"), json_schema_extra={"writeOnly": True})
    ikunpay_key: str = Field(default="", validation_alias=AliasChoices("IKUNPAY_KEY", "PAY_IKUNPAY_KEY"), json_schema_extra={"writeOnly": True})
    ikunpay_gateway_url: str = Field(default="https://ikunpay.com/submit.php", validation_alias=AliasChoices("IKUNPAY_GATEWAY_URL", "IKUNPAY_SUBMIT_URL", "PAY_IKUNPAY_GATEWAY_URL"))
    ikunpay_notify_url: str = Field(default="", validation_alias=AliasChoices("IKUNPAY_NOTIFY_URL", "PAY_IKUNPAY_NOTIFY_URL"))
    ikunpay_return_url: str = Field(default="", validation_alias=AliasChoices("IKUNPAY_RETURN_URL", "PAY_IKUNPAY_RETURN_URL"))
    ikunpay_default_type: str = Field(default="", validation_alias=AliasChoices("IKUNPAY_DEFAULT_TYPE", "PAY_IKUNPAY_DEFAULT_TYPE"))
    ikunpay_callback_ips: list[str] = Field(default=[], validation_alias=AliasChoices("IKUNPAY_CALLBACK_IPS"))

    # WeChatPay
    wechatpay_mch_id: str = Field(default="", validation_alias=AliasChoices("WECHATPAY_MCH_ID", "WECHAT_MCH_ID"), json_schema_extra={"writeOnly": True})
    wechatpay_mch_serial_no: str = Field(default="", validation_alias=AliasChoices("WECHATPAY_MCH_SERIAL_NO", "WECHAT_MCH_SERIAL_NO"), json_schema_extra={"writeOnly": True})
    wechatpay_private_key: str = Field(default="", validation_alias=AliasChoices("WECHATPAY_PRIVATE_KEY", "WECHAT_PRIVATE_KEY"), json_schema_extra={"writeOnly": True})
    wechatpay_api_v3_key: str = Field(default="", validation_alias=AliasChoices("WECHATPAY_API_V3_KEY", "WECHAT_API_V3_KEY"), json_schema_extra={"writeOnly": True})
    wechatpay_certificates_url: str = Field(default="https://api.mch.weixin.qq.com/v3/certificates", validation_alias=AliasChoices("WECHATPAY_CERTIFICATES_URL", "WECHAT_CERTIFICATES_URL"))
    wechatpay_notify_url: str = Field(default="", validation_alias=AliasChoices("WECHATPAY_NOTIFY_URL", "WECHAT_NOTIFY_URL"))
    wechatpay_callback_ips: list[str] = Field(
        default=["203.205.219.0/24", "203.205.220.0/24", "203.205.221.0/24", "203.205.222.0/24", "203.205.223.0/24"],
        validation_alias=AliasChoices("WECHATPAY_CALLBACK_IPS"),
    )

    @model_validator(mode="after")
    def _validate_payment(self):
        """验证支付配置"""
        if _running_tests():
            return self

        if not getattr(self, "debug", False):
            payment_errors = []
            if not self.payment_webhook_secret or len(self.payment_webhook_secret) < 16:
                payment_errors.append("PAYMENT_WEBHOOK_SECRET must be set (min 16 chars)")

            if self.alipay_app_id:
                if not self.alipay_private_key:
                    payment_errors.append("ALIPAY_PRIVATE_KEY missing")
                if not self.alipay_public_key:
                    payment_errors.append("ALIPAY_PUBLIC_KEY missing")

            if self.wechatpay_mch_id:
                if not self.wechatpay_private_key:
                    payment_errors.append("WECHATPAY_PRIVATE_KEY missing")
                if not self.wechatpay_api_v3_key:
                    payment_errors.append("WECHATPAY_API_V3_KEY missing")

            if self.ikunpay_pid:
                if not self.ikunpay_key:
                    payment_errors.append("IKUNPAY_KEY missing")

            if payment_errors:
                error_msg = "SECURITY ERROR - Payment configuration:\n" + "\n".join(f"  - {err}" for err in payment_errors)
                raise ValueError(error_msg)

        return self


class AIConfig(BaseSettings):
    """AI 配置"""
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(extra="ignore", env_file=_resolve_env_files())

    openai_api_key: str = Field(default="", json_schema_extra={"writeOnly": True})
    openai_base_url: str = "https://api.openai.com/v1"
    openai_transcribe_api_key: str = Field(default="", validation_alias=AliasChoices("OPENAI_TRANSCRIBE_API_KEY"), json_schema_extra={"writeOnly": True})
    openai_transcribe_base_url: str = Field(default="", validation_alias=AliasChoices("OPENAI_TRANSCRIBE_BASE_URL"))
    ai_model: str = "deepseek-chat"
    ai_fallback_models: str = Field(default="", validation_alias=AliasChoices("AI_FALLBACK_MODELS", "OPENAI_FALLBACK_MODELS"))

    # Sherpa ASR
    sherpa_asr_enabled: bool = Field(default=False, validation_alias=AliasChoices("SHERPA_ASR_ENABLED"))
    sherpa_asr_mode: str = Field(default="off", validation_alias=AliasChoices("SHERPA_ASR_MODE"))
    sherpa_asr_remote_url: str = Field(default="", validation_alias=AliasChoices("SHERPA_ASR_REMOTE_URL"))
    sherpa_onnx_tokens: str = Field(default="", validation_alias=AliasChoices("SHERPA_ONNX_TOKENS"))
    sherpa_onnx_wenet_ctc_model: str = Field(default="", validation_alias=AliasChoices("SHERPA_ONNX_WENET_CTC_MODEL"))
    sherpa_onnx_whisper_encoder: str = Field(default="", validation_alias=AliasChoices("SHERPA_ONNX_WHISPER_ENCODER"))
    sherpa_onnx_whisper_decoder: str = Field(default="", validation_alias=AliasChoices("SHERPA_ONNX_WHISPER_DECODER"))
    sherpa_onnx_whisper_language: str = Field(default="", validation_alias=AliasChoices("SHERPA_ONNX_WHISPER_LANGUAGE"))
    sherpa_onnx_whisper_task: str = Field(default="transcribe", validation_alias=AliasChoices("SHERPA_ONNX_WHISPER_TASK"))
    sherpa_onnx_whisper_tail_paddings: int = Field(default=-1, validation_alias=AliasChoices("SHERPA_ONNX_WHISPER_TAIL_PADDINGS"))
    sherpa_onnx_num_threads: int = Field(default=2, validation_alias=AliasChoices("SHERPA_ONNX_NUM_THREADS"))
    sherpa_onnx_decoding_method: str = Field(default="greedy_search", validation_alias=AliasChoices("SHERPA_ONNX_DECODING_METHOD"))
    sherpa_onnx_debug: bool = Field(default=False, validation_alias=AliasChoices("SHERPA_ONNX_DEBUG"))
    sherpa_onnx_sample_rate: int = Field(default=16000, validation_alias=AliasChoices("SHERPA_ONNX_SAMPLE_RATE"))
    sherpa_onnx_feature_dim: int = Field(default=80, validation_alias=AliasChoices("SHERPA_ONNX_FEATURE_DIM"))

    # News AI
    NEWS_AI_SUMMARY_ENABLED: bool = Field(default=False, validation_alias=AliasChoices("NEWS_AI_SUMMARY_ENABLED"))
    NEWS_AI_MAX_AGE: timedelta = Field(default=timedelta(days=7), validation_alias=AliasChoices("NEWS_AI_MAX_AGE"))
    NEWS_AI_BATCH_SIZE: int = Field(default=50, validation_alias=AliasChoices("NEWS_AI_BATCH_SIZE"))
    NEWS_AI_MAX_CONCURRENT: int = Field(default=5, validation_alias=AliasChoices("NEWS_AI_MAX_CONCURRENT"))

    # Voice transcribe
    voice_transcribe_force_enabled: bool = Field(default=False, validation_alias=AliasChoices("VOICE_TRANSCRIBE_FORCE_ENABLED"))
    voice_transcribe_provider: str = Field(default="auto", validation_alias=AliasChoices("VOICE_TRANSCRIBE_PROVIDER", "TRANSCRIBE_PROVIDER"))

    @property
    def ai_fallback_models_list(self) -> list[str]:
        """获取AI回退模型列表"""
        import json

        value = self.ai_fallback_models
        if not value or not value.strip():
            return []

        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                cleaned = [str(v).strip() for v in parsed if str(v).strip()]
            else:
                parts = [p.strip() for p in value.replace("，", ",").split(",")]
                cleaned = [p for p in parts if p]
        except (json.JSONDecodeError, ValueError):
            parts = [p.strip() for p in value.replace("，", ",").split(",")]
            cleaned = [p for p in parts if p]

        seen: set[str] = set()
        out: list[str] = []
        for item in cleaned:
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out


class WebSocketConfig(BaseSettings):
    """WebSocket 安全配置"""
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(extra="ignore", env_file=_resolve_env_files())

    ws_max_connections_per_ip: int = Field(default=5, validation_alias=AliasChoices("WS_MAX_CONNECTIONS_PER_IP"))
    ws_max_connections_per_user: int = Field(default=3, validation_alias=AliasChoices("WS_MAX_CONNECTIONS_PER_USER"))
    ws_message_rate_limit: int = Field(default=30, validation_alias=AliasChoices("WS_MESSAGE_RATE_LIMIT"))
    ws_message_rate_window: int = Field(default=60, validation_alias=AliasChoices("WS_MESSAGE_RATE_WINDOW"))
    ws_max_message_size: int = Field(default=10240, validation_alias=AliasChoices("WS_MAX_MESSAGE_SIZE"))
    ws_connection_timeout: int = Field(default=300, validation_alias=AliasChoices("WS_CONNECTION_TIMEOUT"))
    ws_ping_timeout: int = Field(default=60, validation_alias=AliasChoices("WS_PING_TIMEOUT"))
    ws_max_reconnect_attempts: int = Field(default=3, validation_alias=AliasChoices("WS_MAX_RECONNECT_ATTEMPTS"))
    ws_reconnect_backoff: int = Field(default=5, validation_alias=AliasChoices("WS_RECONNECT_BACKOFF"))


class StorageConfig(BaseSettings):
    """存储配置"""
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(extra="ignore", env_file=_resolve_env_files())

    chroma_persist_dir: str = "./chroma_db"
    storage_provider: str = Field(default="local", validation_alias=AliasChoices("STORAGE_PROVIDER", "UPLOAD_STORAGE_PROVIDER"))
    storage_public_base_url: str = Field(default="", validation_alias=AliasChoices("STORAGE_PUBLIC_BASE_URL", "UPLOAD_PUBLIC_BASE_URL"))
    storage_s3_bucket: str = Field(default="", validation_alias=AliasChoices("STORAGE_S3_BUCKET", "UPLOAD_S3_BUCKET"))
    storage_s3_endpoint_url: str = Field(default="", validation_alias=AliasChoices("STORAGE_S3_ENDPOINT_URL", "UPLOAD_S3_ENDPOINT_URL", "S3_ENDPOINT_URL"))
    storage_s3_region: str = Field(default="", validation_alias=AliasChoices("STORAGE_S3_REGION", "UPLOAD_S3_REGION", "AWS_REGION"))
    storage_s3_access_key_id: str = Field(default="", validation_alias=AliasChoices("STORAGE_S3_ACCESS_KEY_ID", "UPLOAD_S3_ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID"))
    storage_s3_secret_access_key: str = Field(default="", validation_alias=AliasChoices("STORAGE_S3_SECRET_ACCESS_KEY", "UPLOAD_S3_SECRET_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY"))
    storage_s3_prefix: str = Field(default="uploads", validation_alias=AliasChoices("STORAGE_S3_PREFIX", "UPLOAD_S3_PREFIX"))


class InfraConfig(BaseSettings):
    """基础设施配置 (CORS/Redis/Proxy/Sentry/Logging)"""
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(extra="ignore", env_file=_resolve_env_files())

    cors_allow_origins: list[str] = Field(default=[], validation_alias=AliasChoices("CORS_ALLOW_ORIGINS"))
    cors_allow_credentials: bool = True
    redis_url: str = Field(default="", validation_alias=AliasChoices("REDIS_URL", "REDIS_URI"))
    trusted_proxies: list[str] = []

    # Sentry
    sentry_dsn: str = Field(default="", validation_alias=AliasChoices("SENTRY_DSN"))
    sentry_environment: str = Field(default="", validation_alias=AliasChoices("SENTRY_ENVIRONMENT", "SENTRY_ENV"))
    sentry_release: str = Field(default="", validation_alias=AliasChoices("SENTRY_RELEASE"))
    sentry_traces_sample_rate: float = Field(default=0.0, validation_alias=AliasChoices("SENTRY_TRACES_SAMPLE_RATE"))
    sentry_profiles_sample_rate: float = Field(default=0.0, validation_alias=AliasChoices("SENTRY_PROFILES_SAMPLE_RATE"))

    # Logging
    log_mask_level: str = Field(default="standard", validation_alias=AliasChoices("LOG_MASK_LEVEL", "LOG_SANITIZER_LEVEL"))
    log_mask_fields: list[str] = Field(default_factory=list, validation_alias=AliasChoices("LOG_MASK_FIELDS", "LOG_SANITIZER_FIELDS"))
    log_mask_disable_in_debug: bool = Field(default=True, validation_alias=AliasChoices("LOG_MASK_DISABLE_IN_DEBUG", "LOG_SANITIZER_DISABLE_IN_DEBUG"))

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _parse_cors_allow_origins(cls, value: object):
        """解析CORS允许的来源"""
        if isinstance(value, str):
            parts = [p.strip() for p in value.replace("，", ",").split(",")]
            return [p for p in parts if p]
        return value

    @model_validator(mode="after")
    def _validate_infra(self):
        """验证基础设施配置"""
        if _running_tests():
            return self

        if not getattr(self, "debug", False):
            if not self.cors_allow_origins:
                raise ValueError("SECURITY ERROR: CORS_ALLOW_ORIGINS must be configured in production.")
            if not (self.redis_url or "").strip():
                raise ValueError("SECURITY ERROR: REDIS_URL must be set in production.")

        return self


# ==========================================
# 组合设置类（保持向后兼容）
# ==========================================

class Settings:
    """应用设置 - 组合所有领域配置

    保持向后兼容：所有字段仍可通过 settings.xxx 访问。
    """

    def __init__(self):
        self.app = AppConfig()
        self.db = DatabaseConfig()
        self.security = SecurityConfig()
        self.payment = PaymentConfig()
        self.ai = AIConfig()
        self.ws = WebSocketConfig()
        self.storage = StorageConfig()
        self.infra = InfraConfig()

    # 向后兼容：扁平化属性代理
    def __getattr__(self, name: str):
        """属性代理 - 保持向后兼容"""
        for domain in (self.app, self.db, self.security, self.payment, self.ai, self.ws, self.storage, self.infra):
            if hasattr(domain, name):
                return getattr(domain, name)
        raise AttributeError(f"'Settings' has no attribute '{name}'")


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的设置实例"""
    return Settings()


# 保持向后兼容
def get_config() -> Settings:
    """向后兼容的配置获取函数"""
    return get_settings()
