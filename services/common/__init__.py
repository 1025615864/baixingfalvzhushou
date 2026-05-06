"""Common package - 微服务共享代码

本项目所有微服务共享的工具、中间件、模型和配置。

模块列表:
- api: API 错误处理、统一响应格式
- client: HTTP 客户端、Kafka 客户端
- config: 配置加载器、Consul KV 版本控制
- discovery: Consul 服务注册与发现
- events: Kafka 事件定义与 Producer
- grpc: gRPC 客户端连接池
- middleware: 认证、限流、审计、遥测中间件
- migrations: Alembic 数据库迁移
- models: 审计日志、Saga 日志、Outbox 消息等共享模型
- monitoring: 事务监控、告警
- outbox: Outbox 模式实现
- saga: Saga 分布式事务编排器、持久化
- security: JWT 密钥管理、密码策略、密钥管理
- services: 审计服务
- testing: 共享测试工具
- tracing: OpenTelemetry 链路追踪
- vector: pgvector 向量存储

使用方式:
    from services.common.events import EventType, EventTopic, VectorSyncEvent
    from services.common.saga import SagaOrchestrator, create_saga
    from services.common.outbox import OutboxPublisher
    from services.common.middleware import get_current_user, check_permission
    from services.common.security import JWTKeyManager, validate_password, get_secret
    from services.common.config import ServiceConfig, ConfigLoader, get_consul_kv_client
    from services.common.api import ErrorCode, create_http_exception
    from services.common.monitoring import TransactionMonitor
    from services.common.client import ServiceClient, KafkaClient
    from services.common.grpc import GrpcClient, grpc_pool
    from services.common.discovery import get_discovery, ConsulServiceRegistration
"""

__version__ = "1.1.0"
__all__ = [
    "api",
    "client",
    "config",
    "discovery",
    "events",
    "grpc",
    "middleware",
    "migrations",
    "models",
    "monitoring",
    "outbox",
    "saga",
    "security",
    "services",
    "testing",
    "tracing",
    "vector",
]
