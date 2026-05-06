# Common - 微服务共享模块

提供微服务间共享的工具、中间件、模型和配置。

## 模块列表

| 模块 | 功能 | 状态 |
|------|------|------|
| `api` | API 错误处理、统一响应格式 | ✅ |
| `client` | HTTP 客户端、Kafka 客户端 | ✅ |
| `config` | 配置加载器、Consul KV 版本控制 | ✅ |
| `discovery` | Consul 服务注册与发现 | ✅ |
| `events` | Kafka 事件定义、Producer、Consumer | ✅ |
| `grpc` | gRPC 客户端连接池 | ✅ |
| `middleware` | 认证、限流、审计、遥测中间件 | ✅ |
| `migrations` | Alembic 数据库迁移模板 | ✅ |
| `models` | 审计日志、Saga、Outbox 共享模型 | ✅ |
| `monitoring` | 事务监控、告警 | ✅ |
| `outbox` | Outbox 模式实现 | ✅ |
| `saga` | Saga 分布式事务编排器、持久化 | ✅ |
| `security` | JWT 密钥管理、密码策略、密钥管理 | ✅ |
| `services` | 审计服务 | ✅ |
| `testing` | 共享测试工具、Pact 契约测试 | ✅ |
| `tracing` | OpenTelemetry 链路追踪 | ✅ |
| `vector` | pgvector 向量存储 | ✅ |

## 使用方式

```python
# 事件系统
from services.common.events import (
    EventType, EventTopic, VectorSyncEvent,
    create_knowledge_event, create_archive_event,
    KafkaProducerClient, KafkaConsumerClient,
)

# 分布式事务
from services.common.saga import SagaOrchestrator, create_saga, HybridSagaPersistence
from services.common.outbox import OutboxPublisher

# 中间件
from services.common.middleware import (
    get_current_user, check_permission,
    OpenTelemetryMiddleware, setup_telemetry,
)

# 安全
from services.common.security import JWTKeyManager, validate_password, get_secret

# 配置
from services.common.config import ServiceConfig, ConfigLoader, get_consul_kv_client

# API 错误处理
from services.common.api import ErrorCode, create_http_exception

# 监控
from services.common.monitoring import TransactionMonitor

# 客户端
from services.common.client import ServiceClient, KafkaClient

# gRPC
from services.common.grpc import GrpcClient, grpc_pool

# 服务发现
from services.common.discovery import get_discovery, ConsulServiceRegistration

# 测试
from services.common.testing import MockKafkaProducer, MockRedis, assert_response_success
```

## 服务列表

| 服务 | 端口 | 描述 |
|------|------|------|
| user-service | 8001 | 用户服务 |
| payment-channel-service | 8002 | 支付通道服务 |
| payment-accounting-service | 8003 | 账务服务 |
| legal-service | 8004 | 法律服务 |
| ai-service | 8005 | AI 服务 |
| news-service | 8006 | 新闻服务 |
| community-service | 8007 | 社区服务 |
| points-service | 8008 | 积分服务 |
| notification-service | 8009 | 通知服务 |
| recommendation-service | 8010 | 推荐服务 |
| search-service | 8011 | 搜索服务 |
| archive-service | 8012 | 案例档案服务 |
| knowledge-service | 8013 | 法律知识库服务 |
| order-service | 8014 | 订单服务 |
| embedding-service | 8015 | 向量嵌入服务 |

## 版本

当前版本: 1.1.0
