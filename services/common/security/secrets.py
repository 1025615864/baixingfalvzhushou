"""统一密钥和Secret管理

支持：
- 环境变量读取
- Kubernetes Secrets
- Vault (可选)
- 敏感信息加密/解密
"""

import os
import json
import logging
import base64
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecretSource(Enum):
    ENV = "env"
    K8S_SECRET = "k8s_secret"
    VAULT = "vault"
    FILE = "file"


@dataclass
class SecretConfig:
    name: str
    source: SecretSource = SecretSource.ENV
    key: Optional[str] = None
    required: bool = True
    default: Optional[str] = None
    encoder: str = "none"


class SecretManager:
    """统一密钥管理器"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._k8s_secret_dir = os.getenv("K8S_SECRETS_DIR", "/var/secrets")
        self._vault_url = os.getenv("VAULT_URL", "")
        self._vault_token = os.getenv("VAULT_TOKEN", "")

    def get(
        self,
        name: str,
        source: SecretSource = SecretSource.ENV,
        key: Optional[str] = None,
        required: bool = True,
        default: Optional[str] = None,
        encoder: str = "none",
    ) -> Optional[str]:
        """获取密钥值"""
        if name in self._cache:
            return self._cache[name]

        value = None

        if source == SecretSource.ENV:
            value = self._get_from_env(name, key or name, required, default)
        elif source == SecretSource.K8S_SECRET:
            value = self._get_from_k8s_secret(name, key or name, required, default)
        elif source == SecretSource.VAULT:
            value = self._get_from_vault(name, required, default)
        elif source == SecretSource.FILE:
            value = self._get_from_file(name, required, default)

        if value is not None:
            value = self._decode_value(value, encoder)

        if value is None and required and default is None:
            raise ValueError(f"Required secret '{name}' not found")

        self._cache[name] = value
        return value

    def _get_from_env(self, name: str, key: str, required: bool, default: Optional[str]) -> Optional[str]:
        value = os.getenv(key) or os.getenv(name)
        if value is None and default is not None:
            return default
        if value is None and required:
            logger.error(f"Required environment variable not found: {key}")
        return value

    def _get_from_k8s_secret(self, name: str, key: str, required: bool, default: Optional[str]) -> Optional[str]:
        secret_file = os.path.join(self._k8s_secret_dir, name, key)
        try:
            if os.path.exists(secret_file):
                with open(secret_file, "r") as f:
                    return f.read().strip()
            secret_file_default = os.path.join(self._k8s_secret_dir, key)
            if os.path.exists(secret_file_default):
                with open(secret_file_default, "r") as f:
                    return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to read K8s secret {name}/{key}: {e}")

        if default is not None:
            return default
        if required:
            logger.error(f"Required K8s secret not found: {name}/{key}")
        return None

    def _get_from_vault(self, name: str, required: bool, default: Optional[str]) -> Optional[str]:
        if not self._vault_url:
            if default is not None:
                return default
            if required:
                raise ValueError("Vault URL not configured")
            return None

        try:
            import httpx
            url = f"{self._vault_url}/v1/secret/data/{name}"
            headers = {"X-Vault-Token": self._vault_token}
            response = httpx.get(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("data", {}).get("value")
        except Exception as e:
            logger.error(f"Failed to read from Vault: {e}")

        if default is not None:
            return default
        if required:
            raise ValueError(f"Required Vault secret not found: {name}")
        return None

    def _get_from_file(self, name: str, required: bool, default: Optional[str]) -> Optional[str]:
        file_path = os.getenv(f"{name}_PATH", default)
        if file_path and os.path.exists(file_path):
            with open(file_path, "r") as f:
                return f.read().strip()
        if default is not None:
            return default
        if required:
            raise ValueError(f"Required secret file not found: {name}")
        return None

    def _decode_value(self, value: str, encoder: str) -> Optional[str]:
        if encoder == "base64":
            try:
                return base64.b64decode(value).decode("utf-8")
            except Exception as e:
                logger.error(f"Failed to decode base64: {e}")
                return value
        return value

    def get_database_url(
        self,
        host: str = "DB_HOST",
        port: str = "DB_PORT",
        user: str = "DB_USER",
        password: str = "DB_PASSWORD",
        database: str = "DB_NAME",
    ) -> str:
        """获取数据库连接URL"""
        db_host = self.get(host, default="localhost")
        db_port = self.get(port, default="5432")
        db_user = self.get(user, default="postgres")
        db_password = self.get(password, required=False, default="")
        db_name = self.get(database, default="baixing")

        if db_password:
            return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        return f"postgresql+asyncpg://{db_user}@{db_host}:{db_port}/{db_name}"

    def get_redis_url(self, host: str = "REDIS_HOST", port: str = "REDIS_PORT", password: str = "REDIS_PASSWORD") -> str:
        """获取Redis连接URL"""
        redis_host = self.get(host, default="localhost")
        redis_port = self.get(port, default="6379")
        redis_password = self.get(password, required=False, default="")

        if redis_password:
            return f"redis://:{redis_password}@{redis_host}:{redis_port}"
        return f"redis://{redis_host}:{redis_port}"

    def get_kafka_bootstrap(self) -> str:
        """获取Kafka bootstrap servers"""
        return self.get("KAFKA_BOOTSTRAP_SERVERS", default="kafka:9092")

    def get_jwt_secret(self) -> str:
        """获取JWT密钥"""
        return self.get("JWT_SECRET", required=False, default="changeme-in-production")

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        logger.info("Secret manager cache cleared")


secret_manager = SecretManager()


def get_secret(
    name: str,
    source: SecretSource = SecretSource.ENV,
    key: Optional[str] = None,
    required: bool = True,
    default: Optional[str] = None,
    encoder: str = "none",
) -> Optional[str]:
    """快捷函数：获取密钥"""
    return secret_manager.get(name, source, key, required, default, encoder)


def get_database_url() -> str:
    """快捷函数：获取数据库URL"""
    return secret_manager.get_database_url()


def get_redis_url() -> str:
    """快捷函数：获取Redis URL"""
    return secret_manager.get_redis_url()


def get_jwt_secret() -> str:
    """快捷函数：获取JWT密钥"""
    return secret_manager.get_jwt_secret()
