# 律师服务部署指南

## 1. 环境要求

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Python | 3.10 | 3.11+ |
| PostgreSQL | 13 | 15+ |
| Redis | 7.0 | 7.2+ |
| Kafka | 3.0 | 3.6+ |
| Docker | 24.0 | 25.0+ |
| Consul | 1.15 | 1.17+ |

## 2. 快速部署

### 2.1 使用 Docker Compose

```yaml
version: '3.8'

services:
  legal-service:
    build: .
    ports:
      - "8004:8004"
      - "50052:50052"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/legal_service
      - REDIS_URL=redis://redis:6379
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - KAFKA_ENABLED=true
      - USER_SERVICE_URL=http://user-service:8001
      - AI_SERVICE_URL=http://ai-service:8005
      - CONSUL_ENABLED=true
      - CONSUL_URL=http://consul:8500
      - GRPC_PORT=50052
      - SERVICE_HOST=legal-service
      - SERVICE_PORT=8004
    depends_on:
      - postgres
      - redis
      - kafka
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=legal_service
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      - KAFKA_BROKER_ID=1
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
      - KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
    depends_on:
      - zookeeper
    restart: unless-stopped

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      - ZOOKEEPER_CLIENT_PORT=2181
    restart: unless-stopped

  consul:
    image: consul:1.17
    ports:
      - "8500:8500"
    command: agent -server -ui -bootstrap-expect=1 -client=0.0.0.0
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f legal-service
```

### 2.2 直接部署

```bash
# 1. 克隆代码
git clone <repository>
cd services/legal-service

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 5. 数据库迁移
alembic upgrade head

# 6. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8004
```

## 3. 数据库初始化

### 3.1 运行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 降级一个版本
alembic downgrade -1

# 生成新迁移 (开发时)
alembic revision --autogenerate -m "add new table"
```

### 3.2 表结构

| 表名 | 说明 |
|------|------|
| consultations | 咨询表 |
| chat_messages | 聊天消息表 |
| lawyers | 律师表 |
| lawyer_schedules | 律师排班表 |
| lawfirms | 律所表 |
| lawyer_consultations | 预约表 |
| reviews | 评价表 |
| legal_documents | 法律文书表 |
| document_templates | 文书模板表 |
| outbox_events | Outbox 事件表 |

## 4. 配置说明

### 4.1 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| DATABASE_URL | 是 | - | 数据库连接 |
| REDIS_URL | 否 | redis://localhost:6379 | Redis连接 |
| KAFKA_BOOTSTRAP_SERVERS | 否 | localhost:9092 | Kafka地址 |
| KAFKA_ENABLED | 否 | false | 是否启用Kafka |
| KAFKA_CONSUMER_GROUP_ID | 否 | legal-service-user-events | 消费者组 |
| USER_SERVICE_URL | 否 | http://localhost:8001 | 用户服务地址 |
| AI_SERVICE_URL | 否 | http://localhost:8005 | AI服务地址 |
| CONSUL_ENABLED | 否 | false | 是否启用Consul |
| CONSUL_URL | 否 | http://localhost:8500 | Consul地址 |
| SERVICE_NAME | 否 | legal-service | 服务名称 |
| SERVICE_HOST | 否 | 0.0.0.0 | 监听地址 |
| SERVICE_PORT | 否 | 8004 | HTTP端口 |
| GRPC_PORT | 否 | 50052 | gRPC端口 |
| GRPC_USE_TLS | 否 | false | 是否启用gRPC TLS |
| RATE_LIMIT_ENABLED | 否 | true | 是否启用限流 |
| JWT_SECRET_KEY | 是 | - | JWT密钥 |
| OTEL_EXPORTER_OTLP_ENDPOINT | 否 | - | OpenTelemetry端点 |

### 4.2 端口映射

| Service | HTTP Port | gRPC Port |
|---------|-----------|-----------|
| legal-service | 8004 | 50052 |
| user-service | 8001 | 50051 |

### 4.3 分级限流规则

| 路径前缀 | 限制 | 时间窗口 |
|----------|------|----------|
| /api/v1/legal/consultations | 30次/分钟 | 60秒 |
| /api/v1/legal/appointments | 10次/分钟 | 60秒 |
| /api/v1/legal/lawyers/search | 60次/分钟 | 60秒 |
| /api/v1/legal/documents | 20次/分钟 | 60秒 |
| /api/v1/legal/admin | 5次/分钟 | 60秒 |
| /api/v1/legal/reviews | 15次/分钟 | 60秒 |

## 5. 健康检查

```bash
# 健康检查
curl http://localhost:8004/health

# 就绪检查 (依赖项检查)
curl http://localhost:8004/health/ready

# 存活检查
curl http://localhost:8004/health/live
```

## 6. 监控

### 6.1 Prometheus 指标

```bash
# 查看指标
curl http://localhost:8004/api/v1/legal/metrics
```

**主要指标:**

| 指标名 | 类型 | 说明 |
|--------|------|------|
| http_requests_total | Counter | HTTP请求总数 |
| http_request_duration_seconds | Histogram | 请求延迟 |
| consultations_created_total | Counter | 咨询创建数 |
| appointments_created_total | Counter | 预约创建数 |
| kafka_messages_produced_total | Counter | Kafka消息发送数 |
| kafka_messages_consumed_total | Counter | Kafka消息消费数 |
| kafka_dlq_messages_total | Counter | 死信队列消息数 |

### 6.2 日志

日志格式为 JSON，支持结构化输出:

```json
{
  "timestamp": "2026-03-23T10:00:00Z",
  "level": "INFO",
  "service": "legal-service",
  "trace_id": "abc123",
  "message": "Consultation created successfully",
  "consultation_id": 1,
  "user_id": 123
}
```

## 7. Kafka 主题

### 7.1 发布主题

| 主题名 | 说明 |
|--------|------|
| baixing.legal.events | 律师服务事件 |

### 7.2 消费主题

| 主题名 | 消费者组 | 说明 |
|--------|---------|------|
| baixing.user.events | legal-service-user-events | 用户事件 |
| user.profile.updated | legal-service-user-events | 个人信息更新 |
| user.lawyer.verified | legal-service-user-events | 律师认证 |

### 7.3 Kafka 事件格式

```json
{
  "event_type": "legal.consultation.created",
  "event_id": "uuid-v4",
  "timestamp": "2026-03-23T10:00:00Z",
  "user_id": "123",
  "payload": {
    "consultation_id": 1,
    "category": "婚姻家庭",
    "title": "标题"
  }
}
```

## 8. gRPC 服务

### 8.1 服务定义

```protobuf
service LegalService {
  rpc GetLawyer(GetLawyerRequest) returns (Lawyer);
  rpc GetLawyerSchedule(GetLawyerScheduleRequest) returns (LawyerSchedule);
}
```

### 8.2 调用示例

```python
import grpc
from services.common.proto import user_pb2, user_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.LegalServiceStub(channel)

response = stub.GetLawyer(
    user_pb2.GetLawyerRequest(lawyer_id="1")
)
print(response.name)
```

## 9. 幂等性保障

### 9.1 使用 Idempotency-Key

对于 POST/PUT/PATCH 请求，可以携带 `Idempotency-Key` 请求头：

```bash
curl -X POST http://localhost:8004/api/v1/legal/consultations/ \
  -H "Idempotency-Key: unique-request-id-12345" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"category":"婚姻继承","title":"离婚咨询","description":"..."}'
```

响应头会包含 `X-Idempotent-Replayed: true` 如果是重复请求。

### 9.2 缓存时间

幂等性结果缓存时间为 24 小时。

## 10. 运维

### 10.1 查看 DLQ 消息

```python
from app.events.consumer import user_event_consumer

# 获取 DLQ 数量
dlq_size = await user_event_consumer.get_dlq_size()
print(f"DLQ messages: {dlq_size}")
```

### 10.2 查看 Outbox 事件状态

```python
from app.services.outbox_service import OutboxPublisher

outbox = OutboxPublisher(session_factory, kafka_producer)
failed = await outbox.get_failed_events()
print(f"Failed events: {len(failed)}")
```

### 10.3 重试失败事件

```python
await outbox.retry_failed_event(event_id)
```

### 10.4 日志级别调整

```bash
# 通过环境变量
export LOG_LEVEL=DEBUG

# 或在代码中
import logging
logging.getLogger("app").setLevel(logging.DEBUG)
```

## 11. 故障排除

### 11.1 服务启动失败

1. 检查数据库连接
```bash
psql $DATABASE_URL -c "SELECT 1"
```

2. 检查 Redis 连接
```bash
redis-cli -u $REDIS_URL ping
```

3. 检查 Kafka 连接
```bash
kafka-topics.sh --bootstrap-server $KAFKA_BOOTSTRAP_SERVERS --list
```

### 11.2 数据库迁移失败

```bash
# 查看迁移状态
alembic current
alembic history

# 手动修复
alembic downgrade -1
alembic upgrade head
```

### 11.3 Kafka 消息堆积

1. 检查消费者是否正常运行
2. 增加消费者数量
3. 检查 DLQ 是否有大量消息
4. 检查 Outbox 事件是否有大量 pending

### 11.4 gRPC 调用失败

1. 检查 gRPC 端口是否开放
2. 检查防火墙规则
3. 检查 TLS 证书配置

## 12. 安全

### 12.1 认证

所有需要认证的 API 需要在请求头中携带:

```
Authorization: Bearer <jwt_token>
```

### 12.2 权限控制

| 角色 | 说明 |
|------|------|
| admin | 管理员 |
| lawyer | 律师 |
| user | 普通用户 |

### 12.3 CORS 配置

```python
# 允许的来源
CORS_ORIGINS = ["http://localhost:3000", "https://example.com"]
```

## 13. 扩展

### 13.1 增加 Kafka 消费者

在 `app/events/consumer.py` 中注册新的处理器:

```python
@user_event_consumer.register_handler("user.lawyer_verified")
async def handle_lawyer_verified(event):
    # 处理逻辑
    pass
```

### 13.2 增加 Outbox 事件

在业务逻辑中使用 Outbox:

```python
from app.services.outbox_service import OutboxPublisher

outbox = OutboxPublisher(session_factory, kafka_producer)

async with session.begin():
    # 业务操作
    consultation = Consultation(...)
    session.add(consultation)

    # 添加 Outbox 事件
    await outbox.add_event(
        event_type="consultation.created",
        topic="baixing.legal.events",
        payload={"consultation_id": consultation.id},
        session=session,
    )
```

## 14. 性能优化建议

### 14.1 数据库连接池

```bash
# 环境变量配置
LEGAL_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?pool_size=20&max_overflow=30
```

### 14.2 Redis 缓存

- 律师信息缓存 5 分钟
- 律所信息缓存 10 分钟
- 搜索结果缓存 1 分钟

### 14.3 限流调优

根据实际业务量调整 `RATE_LIMIT_RULES` 中的限制值。
