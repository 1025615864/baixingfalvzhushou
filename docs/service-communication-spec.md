# 微服务通信规范

> 版本: 1.0
> 更新日期: 2026-05-06
> 适用范围: 所有微服务之间的数据交互

---

## 1. 通信方式选型矩阵

| 场景 | 通信方式 | 协议 | 说明 |
|------|---------|------|------|
| BFF 调用微服务 | HTTP (REST) | JSON | 同步调用，请求-响应模式 |
| 微服务间同步调用 | HTTP 或 gRPC | JSON / Protobuf | 低延迟、强一致场景用 gRPC |
| 领域事件通知 | Kafka | Avro/JSON | 异步解耦，最终一致性 |
| 配置下发 | Consul KV | HTTP | 动态配置更新 |
| 服务发现 | Consul | HTTP/DNS | 服务注册与发现 |
| 文件/大对象 | S3/OSS | HTTP | 上传下载，不经过服务 |

---

## 2. HTTP 通信规范

### 2.1 服务发现与路由

所有 HTTP 调用通过 **Consul 服务发现** 或 **APISIX API Gateway**：

```python
# 方式一: 通过 Consul 发现服务
from services.common.discovery import get_discovery

discovery = get_discovery()
service = await discovery.resolve("user-service")
url = f"http://{service.address}:{service.port}/api/v1/users/{user_id}"

# 方式二: 通过 APISIX Gateway (推荐用于外部调用)
url = f"https://api.baixingfalv.com/users/{user_id}"
```

### 2.2 请求头规范

所有微服务间 HTTP 调用必须携带以下请求头：

| Header | 必填 | 说明 |
|--------|------|------|
| `Authorization` | 是 | Bearer JWT Token |
| `X-Request-ID` | 是 | 请求追踪 ID (UUID) |
| `X-Trace-ID` | 是 | OpenTelemetry Trace ID |
| `X-Service-Name` | 是 | 调用方服务名 |
| `X-Correlation-ID` | 否 | 跨服务关联 ID |
| `Content-Type` | 是 | `application/json` |

### 2.3 超时配置

| 场景 | 连接超时 | 请求超时 | 重试策略 |
|------|---------|---------|---------|
| 内部服务调用 | 3s | 10s | 不重试 |
| AI 服务调用 | 5s | 30s | 无重试 |
| 支付网关调用 | 5s | 15s | 不重试 (幂等) |
| 外部 API | 10s | 60s | 可重试 (幂等) |

```python
# 使用 ServiceClient 的默认超时配置
from services.common.client import ServiceClient

client = ServiceClient(
    connect_timeout=3.0,
    request_timeout=10.0,
    retry_count=0,  # 内部调用不重试
)
```

### 2.4 错误处理

微服务返回的统一错误格式：

```json
{
    "code": "ORDER-001",
    "message": "订单不存在",
    "details": null,
    "request_id": "req-abc-123"
}
```

**错误码命名规则**: `{SERVICE}-{SEQ}`
- `ORDER-001`: 订单服务错误
- `PAY-001`: 支付服务错误
- `USER-001`: 用户服务错误

---

## 3. Kafka 事件通信规范

### 3.1 Topic 命名

格式: `{domain}.{event-type}`

| Topic | 事件类型 | 说明 |
|-------|---------|------|
| `order.created` | OrderCreatedEvent | 订单创建 |
| `order.paid` | OrderPaidEvent | 订单支付完成 |
| `order.cancelled` | OrderCancelledEvent | 订单取消 |
| `user.registered` | UserRegisteredEvent | 用户注册 |
| `user.profile_updated` | UserProfileUpdatedEvent | 用户资料更新 |
| `payment.completed` | PaymentCompletedEvent | 支付完成 |
| `ai.vector_sync` | VectorSyncEvent | 向量同步 |
| `notification.send` | NotificationSendEvent | 通知发送 |

### 3.2 事件格式

```json
{
    "event_id": "evt-uuid",
    "event_type": "order.paid",
    "aggregate_type": "order",
    "aggregate_id": "ord-123",
    "timestamp": "2026-05-06T10:00:00Z",
    "version": 1,
    "source": "order-service",
    "payload": {
        "order_no": "ORD202605060001",
        "user_id": 42,
        "amount": 9900,
        "payment_method": "alipay"
    },
    "metadata": {
        "request_id": "req-abc-123",
        "trace_id": "0af7651916cd43dd8448eb211c80319c"
    }
}
```

### 3.3 事件发布与消费

```python
# 发布事件 (使用 Outbox 模式保证可靠投递)
from services.common.outbox import OutboxPublisher

publisher = OutboxPublisher(db_session_factory)
message = publisher.save_message(
    db=db,
    aggregate_type="order",
    aggregate_id=order_no,
    event_type="order.paid",
    topic="order.paid",
    payload={"order_no": order_no, "amount": 9900},
)

# 消费事件
from services.common.events import EventConsumer, EventType

consumer = EventConsumer(
    bootstrap_servers=["kafka:9092"],
    group_id="notification-consumer",
)

@consumer.subscribe(EventType.ORDER_PAID)
async def on_order_paid(event: OrderPaidEvent):
    await send_notification(event.user_id, "您的订单已支付成功")
```

### 3.4 消费者要求

- 必须 **幂等** 处理（通过 `event_id` 去重）
- 必须处理 **重试** (最多 3 次，指数退避)
- 死信队列: 失败 3 次后进入 `*.dlq` topic
- 消费延迟监控: 通过 `consumer_lag` 指标告警

---

## 4. gRPC 通信规范

### 4.1 使用场景

gRPC 仅用于以下场景：
- 高频低延迟调用 (> 1000 QPS)
- 流式数据传输 (如向量同步)
- 双向通信 (如实时语音转写)

### 4.2 Proto 文件位置

所有 Proto 文件统一放在 `services/common/proto/`：

```
services/common/proto/
├── user/
│   └── user.proto
├── order/
│   └── order.proto
├── ai/
│   └── embedding.proto
└── common/
    └── metadata.proto
```

### 4.3 服务注册

```python
# 服务端注册
from services.common.grpc import GrpcService

service = GrpcService(
    service_name="embedding-service",
    port=50051,
)
service.register_service(EmbeddingServiceServicer())
await service.start()

# 客户端调用
from services.common.grpc import grpc_pool

async with grpc_pool.get_client("embedding-service") as stub:
    response = await stub.Embed(text="法律咨询")
```

---

## 5. 安全规范

### 5.1 认证

- 所有服务间调用使用 **JWT Token** 认证
- Token 由 BFF 层签发，通过 `Authorization: Bearer <token>` 传递
- 微服务通过 `services/common/middleware/auth.py` 验证 Token

### 5.2 网络隔离

- 内部服务通信使用 **内网 IP** (不暴露公网)
- API Gateway (APISIX) 作为唯一入口
- 数据库端口不对外开放

### 5.3 数据加密

- 敏感数据 (银行卡号、身份证) 使用 AES-256 加密存储
- TLS 1.3 用于所有服务间通信
- API Key 和密钥通过 Vault/Consul KV 管理

---

## 6. 监控与可观测性

### 6.1 指标

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `http_requests_total` | Counter | method, route, status | HTTP 请求数 |
| `http_request_duration_seconds` | Histogram | method, route | 请求延迟 |
| `kafka_messages_total` | Counter | topic, status | Kafka 消息数 |
| `grpc_requests_total` | Counter | method, status | gRPC 请求数 |

### 6.2 链路追踪

- 使用 **OpenTelemetry** 进行全链路追踪
- Trace ID 通过 `X-Trace-ID` 传递
- Span Context 自动注入 HTTP/gRPC/Kafka 请求头

### 6.3 日志规范

```json
{
    "timestamp": "2026-05-06T10:00:00Z",
    "level": "INFO",
    "service": "order-service",
    "trace_id": "0af7651916cd43dd",
    "span_id": "b7ad6b7169203331",
    "message": "订单创建成功",
    "order_no": "ORD202605060001",
    "user_id": 42
}
```

---

## 7. 熔断与降级

### 7.1 熔断策略

| 下游服务 | 熔断阈值 | 恢复时间 | 降级策略 |
|---------|---------|---------|---------|
| AI 服务 | 50% 失败率, 10 次 | 30s | 返回缓存结果 |
| 支付服务 | 30% 失败率, 5 次 | 60s | 排队等待 |
| 用户服务 | 50% 失败率, 20 次 | 15s | 使用本地缓存 |
| 推荐服务 | 50% 失败率, 10 次 | 30s | 返回默认推荐 |

### 7.2 实现

```python
from services.common.middleware.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(
    name="ai-service",
    failure_threshold=10,
    recovery_timeout=30,
    failure_ratio=0.5,
)

@breaker.protect
async def call_ai_service():
    return await ai_client.chat(prompt)
```

---

## 8. 版本管理

### 8.1 API 版本

- URL 版本: `/api/v1/orders/`, `/api/v2/orders/`
- 向后兼容: 新版本必须向后兼容至少一个版本
- 废弃通知: 提前 3 个月通知，通过 HTTP 响应头 `Sunset` 标记

### 8.2 事件版本

```json
{
    "event_type": "order.paid",
    "version": 2,
    "payload": { ... }
}
```

- 消费者必须处理多个版本
- 重大变更 (Breaking Change) 使用新事件类型

---

## 9. 检查清单

新微服务接入前检查：

- [ ] 服务注册到 Consul
- [ ] OpenTelemetry 追踪已集成
- [ ] Prometheus 指标已暴露
- [ ] 健康检查端点 `/health` 可用
- [ ] JWT 认证中间件已配置
- [ ] 日志格式符合规范
- [ ] 错误码遵循命名规则
- [ ] Kafka 消费者幂等处理
- [ ] 熔断器配置合理
- [ ] API 文档 (OpenAPI) 已生成
- [ ] 单元测试覆盖率 > 80%
- [ ] 契约测试已编写
