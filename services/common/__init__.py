"""Common package - 微服务共享代码

本项目所有微服务共享的工具、中间件、模型和配置。

模块列表:
- api: API 错误处理、统一响应格式
- config: 配置加载器
- discovery: Consul 服务注册与发现
- events: Kafka 事件定义与 Producer
- middleware: 认证、限流、审计、遥测中间件
- models: 审计日志、Saga 日志、Outbox 消息等共享模型
- monitoring: 事务监控、告警
- outbox: Outbox 模式实现
- saga: Saga 分布式事务编排器
- security: JWT 密钥管理、密码策略
- services: 审计服务
- testing: 共享测试工具
- tracing: OpenTelemetry 链路追踪
- vector: pgvector 向量存储

使用方式:
    from services.common.events import EventType, EventTopic, VectorSyncEvent
    from services.common.saga import SagaOrchestrator, create_saga
    from services.common.outbox import OutboxPublisher
    from services.common.middleware import get_current_user, check_permission
    from services.common.security import JWTKeyManager, validate_password
    from services.common.config import ServiceConfig, ConfigLoader
    from services.common.api import ErrorCode, create_http_exception
    from services.common.monitoring import TransactionMonitor
"""

__version__ = "1.0.0"
__all__ = [
    "api",
    "config",
    "discovery",
    "events",
    "middleware",
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
