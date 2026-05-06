"""配置中心统一加载器

提供统一的配置加载，支持：
- 环境变量
- Consul KV
- 配置文件
- 配置热更新
- 配置验证
"""
import os
import json
import logging
from typing import Any, Optional, TypeVar, Generic, Type
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ConfigError(Exception):
    """配置错误"""
    pass


class BaseAppConfig(BaseSettings):
    """应用基础配置"""

    # 应用信息
    app_name: str = Field(default="baixing-falvzhushou", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    app_env: str = Field(default="development", description="运行环境")

    # 数据库
    database_url: str = Field(default="postgresql://localhost:5432/baixing", description="数据库连接")
    db_pool_size: int = Field(default=5, ge=1, description="数据库连接池大小")
    db_max_overflow: int = Field(default=10, ge=0, description="数据库最大溢出连接数")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", description="Redis连接")

    # Kafka
    kafka_bootstrap_servers: str = Field(default="localhost:9092", description="Kafka地址")
    kafka_enabled: bool = Field(default=False, description="是否启用Kafka")

    # Consul
    consul_host: str = Field(default="localhost", description="Consul主机")
    consul_port: int = Field(default=8500, ge=1, description="Consul端口")
    consul_enabled: bool = Field(default=False, description="是否启用Consul")

    # 安全
    jwt_secret_key: str = Field(default="change-me-in-production", description="JWT密钥")
    jwt_algorithm: str = Field(default="HS256", description="JWT算法")
    jwt_expiration_minutes: int = Field(default=60, ge=1, description="JWT过期时间")

    # 限流
    rate_limit_enabled: bool = Field(default=True, description="是否启用限流")

    # 日志
    log_level: str = Field(default="INFO", description="日志级别")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class ServiceConfig(BaseSettings):
    """微服务基础配置"""

    service_name: str
    service_port: int = Field(default=8000, ge=1, le=65535)
    service_host: str = Field(default="0.0.0.0", description="服务绑定地址")

    database_url: str
    redis_url: str = "redis://localhost:6379"

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_prefix: str = "baixing"

    consul_enabled: bool = False
    consul_host: str = "localhost"
    consul_port: int = 8500

    otel_enabled: bool = False
    otel_endpoint: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class ConfigLoader:
    """配置加载器"""

    @staticmethod
    def load_env_config(config_class: Type[T], env_prefix: str = "") -> T:
        """从环境变量加载配置"""
        config = config_class()
        logger.info(f"Config loaded: {config_class.__name__}")
        return config

    @staticmethod
    def load_from_consul(
        config_class: Type[T],
        consul_host: str = "localhost",
        consul_port: int = 8500,
        key_prefix: str = "baixing/config/",
    ) -> T:
        """从 Consul KV 加载配置"""
        try:
            import consul
            client = consul.Consul(host=consul_host, port=consul_port)

            _, keys = client.kv.get(key_prefix, recurse=True)
            if not keys:
                logger.warning(f"No config found in Consul at {key_prefix}")
                return config_class()

            config_dict = {}
            for item in keys:
                key = item["Key"].replace(key_prefix, "")
                value = item["Value"]
                if value:
                    try:
                        config_dict[key] = json.loads(value.decode("utf-8"))
                    except json.JSONDecodeError:
                        config_dict[key] = value.decode("utf-8")

            config = config_class(**config_dict)
            logger.info(f"Config loaded from Consul: {config_class.__name__}")
            return config

        except ImportError:
            logger.warning("python-consul not installed, falling back to env config")
            return config_class()
        except Exception as e:
            logger.error(f"Failed to load config from Consul: {e}")
            return config_class()

    @staticmethod
    def validate_config(config: BaseModel) -> list[str]:
        """验证配置"""
        errors = []

        for field_name, field_info in config.model_fields.items():
            value = getattr(config, field_name)
            if value is None and field_info.is_required():
                errors.append(f"Required field '{field_name}' is missing")

        return errors
