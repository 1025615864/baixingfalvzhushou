# 社区服务部署指南

## 1. 环境要求

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Python | 3.10 | 3.11+ |
| PostgreSQL | 13 | 15+ |
| Redis | 7.0 | 7.2+ |
| Kafka | 3.0 | 3.6+ |
| Docker | 24.0 | 25.0+ |

## 2. 快速部署

### 2.1 使用 Docker Compose

```yaml
version: '3.8'

services:
  community-service:
    build: .
    ports:
      - "8007:8007"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/community
      - REDIS_URL=redis://redis:6379
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - KAFKA_ENABLED=true
      - USER_SERVICE_URL=http://user-service:8001
      - AI_SERVICE_URL=http://ai-service:8005
    depends_on:
      - postgres
      - redis
      - kafka
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=community
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

volumes:
  postgres_data:
  redis_data:
```

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f community-service
```

### 2.2 直接部署

```bash
# 1. 克隆代码
git clone <repository>
cd services/community-service

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

# 6. 初始化数据 (可选)
python -m scripts.init_ops_data

# 7. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8007
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

### 3.2 初始化运营数据

```bash
# 创建初始话题、示例帖子、管理员角色等
python -m scripts.init_ops_data
```

**会创建:**
- 8 个初始话题分类
- 3 篇示例帖子
- 运营配置
- 敏感词库
- 管理员运营角色 (user_id=1)

## 4. 配置说明

### 4.1 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| DATABASE_URL | 是 | - | 数据库连接 |
| REDIS_URL | 否 | redis://localhost:6379 | Redis连接 |
| KAFKA_BOOTSTRAP_SERVERS | 否 | localhost:9092 | Kafka地址 |
| KAFKA_ENABLED | 否 | false | 是否启用Kafka |
| KAFKA_CONSUMER_GROUP_ID | 否 | community-service-user-events | 消费者组 |
| USER_SERVICE_URL | 否 | http://localhost:8001 | 用户服务地址 |
| AI_SERVICE_URL | 否 | http://localhost:8005 | AI服务地址 |
| SERVICE_NAME | 否 | community-service | 服务名称 |
| SERVICE_HOST | 否 | 0.0.0.0 | 监听地址 |
| SERVICE_PORT | 否 | 8007 | 监听端口 |
| JWT_SECRET_KEY | 是 | - | JWT密钥 |
| TELEMETRY_SERVICE_NAME | 否 | community-service | 链路追踪服务名 |

### 4.2 config.yaml 示例

```yaml
database:
  url: postgresql+asyncpg://user:pass@localhost:5432/community
  pool_size: 10
  max_overflow: 20

redis:
  url: redis://localhost:6379/0

kafka:
  bootstrap_servers: localhost:9092
  enabled: true
  consumer_group: community-service-user-events

service:
  name: community-service
  host: 0.0.0.0
  port: 8007

telemetry:
  enabled: true
  service_name: community-service
  otlp_endpoint: http://localhost:4317
```

## 5. 健康检查

```bash
# 健康检查
curl http://localhost:8007/api/v1/community/health

# 就绪检查 (依赖项检查)
curl http://localhost:8007/api/v1/community/health/ready

# 存活检查
curl http://localhost:8007/api/v1/community/health/live
```

## 6. 监控

### 6.1 Prometheus 指标

```bash
# 查看指标
curl http://localhost:8007/api/v1/community/metrics
```

**主要指标:**

| 指标名 | 类型 | 说明 |
|--------|------|------|
| http_requests_total | Counter | HTTP请求总数 |
| http_request_duration_seconds | Histogram | 请求延迟 |
| posts_created_total | Counter | 帖子创建数 |
| comments_created_total | Counter | 评论创建数 |
| kafka_messages_produced_total | Counter | Kafka消息发送数 |
| kafka_messages_consumed_total | Counter | Kafka消息消费数 |
| kafka_dlq_messages_total | Counter | 死信队列消息数 |

### 6.2 日志

日志格式为 JSON，支持结构化输出:

```json
{
  "timestamp": "2026-03-23T10:00:00Z",
  "level": "INFO",
  "service": "community-service",
  "trace_id": "abc123",
  "message": "Post created successfully",
  "post_id": 1,
  "user_id": 123
}
```

## 7. Kafka 主题

### 7.1 发布主题

| 主题名 | 说明 |
|--------|------|
| baixing.community.events | 社区事件 |
| baixing.community.ops.events | 运营事件 |

### 7.2 消费主题

| 主题名 | 消费者组 | 说明 |
|--------|---------|------|
| baixing.user.events | community-service-user-events | 用户事件 |
| user.profile.updated | community-service-user-events | 个人信息更新 |
| user.lawyer.verified | community-service-user-events | 律师认证 |

### 7.3 Kafka 事件格式

```json
{
  "event_type": "community.post.created",
  "event_id": "uuid-v4",
  "timestamp": "2026-03-23T10:00:00Z",
  "user_id": "123",
  "payload": {
    "post_id": 1,
    "title": "标题",
    "content": "内容"
  }
}
```

## 8. 运维

### 8.1 查看 DLQ 消息

```python
from app.events.consumer import user_event_consumer

# 获取 DLQ 数量
dlq_size = await user_event_consumer.get_dlq_size()
print(f"DLQ messages: {dlq_size}")
```

### 8.2 重试处理

DLQ 中的消息可以通过以下方式重试:

1. 手动修复问题
2. 重新发布到原主题
3. 使用 Kafka 消费者重置偏移量

### 8.3 日志级别调整

```bash
# 通过环境变量
export LOG_LEVEL=DEBUG

# 或在代码中
import logging
logging.getLogger("app").setLevel(logging.DEBUG)
```

## 9. 故障排除

### 9.1 服务启动失败

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

### 9.2 数据库迁移失败

```bash
# 查看迁移状态
alembic current
alembic history

# 手动修复
alembic downgrade -1
alembic upgrade head
```

### 9.3 Kafka 消息堆积

1. 检查消费者是否正常运行
2. 增加消费者数量
3. 检查 DLQ 是否有大量消息

## 10. 安全

### 10.1 认证

所有需要认证的 API 需要在请求头中携带:

```
Authorization: Bearer <jwt_token>
```

### 10.2 权限控制

| 角色 | 说明 |
|------|------|
| community_director | 最高权限 |
| content_mod | 内容审核 |
| topic_ops | 话题运营 |
| user_ops | 用户运营 |
| data_analyst | 数据分析 |

### 10.3 CORS 配置

```python
# 允许的来源
CORS_ORIGINS = ["http://localhost:3000", "https://example.com"]

# 允许的方法
CORS_METHODS = ["GET", "POST", "PUT", "DELETE"]

# 允许的头
CORS_HEADERS = ["*"]
```

## 11. 扩展

### 11.1 增加消费者

在 `app/events/consumer.py` 中注册新的处理器:

```python
@user_event_consumer.register_handler("user.new_event")
async def handle_new_event(event):
    # 处理逻辑
    pass
```

### 11.2 增加运营角色

在 `app/models/ops_models.py` 的 `VALID_OPS_ROLES` 字典中添加:

```python
VALID_OPS_ROLES = {
    ...
    "new_role": ["permission1", "permission2"],
}
```
