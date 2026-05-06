# 百姓法律助手 - 社区服务

## 1. 服务概述

社区服务是百姓法律助手微服务架构中的核心社区模块，为用户提供法律咨询社区功能，包括帖子发布、评论互动、话题分类、内容审核等能力。

### 1.1 服务定位

```
┌─────────────────────────────────────────────────────────┐
│                    百姓法律助手系统                        │
├─────────────────────────────────────────────────────────┤
│  用户服务  │  社区服务  │  AI服务  │  通知服务  │  积分服务  │
│  (8001)   │  (8007)   │  (8005)  │   (8008)   │   (8009)   │
└─────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 框架 | FastAPI | 0.100+ |
| ORM | SQLAlchemy | 2.0+ (Async) |
| 数据库 | PostgreSQL / SQLite | 13+ |
| 消息队列 | Kafka | 3.0+ |
| 缓存 | Redis | 7.0+ |
| 链路追踪 | OpenTelemetry | 1.22+ |
| 服务注册 | Consul | 1.15+ |

### 1.3 服务端口

```
社区服务: http://localhost:8007
```

---

## 2. 架构设计

### 2.1 目录结构

```
services/community-service/
├── app/
│   ├── main.py                    # FastAPI 主应用
│   ├── database.py                 # 数据库连接
│   ├── config/                    # 配置管理
│   │
│   ├── models/                    # 数据模型 (8个)
│   │   ├── post.py               # 帖子模型
│   │   ├── comment.py            # 评论模型
│   │   ├── topic.py              # 话题模型
│   │   ├── moderation.py         # 审核队列表
│   │   ├── draft.py              # 草稿模型
│   │   ├── report.py             # 举报模型
│   │   └── ops_models.py          # 运营7表
│   │
│   ├── routers/                   # API 路由 (20个)
│   │   ├── post.py               # 帖子路由
│   │   ├── comment.py            # 评论路由
│   │   ├── topic.py              # 话题路由
│   │   ├── hot.py                # 热门路由
│   │   ├── favorite.py           # 收藏路由
│   │   ├── report.py             # 举报路由
│   │   ├── admin.py              # 管理路由
│   │   ├── moderation.py         # 审核路由
│   │   ├── dashboard.py          # 看板路由
│   │   ├── metrics.py            # 指标路由
│   │   └── ops/                   # 运营后台 (8个)
│   │
│   ├── services/                  # 业务逻辑 (17个)
│   │   ├── post_service.py
│   │   ├── comment_service.py
│   │   ├── topic_service.py
│   │   ├── hot_service.py
│   │   ├── moderation_service.py
│   │   ├── moderation_queue_service.py
│   │   ├── mention_service.py
│   │   ├── draft_service.py
│   │   ├── share_service.py
│   │   ├── dashboard_service.py
│   │   ├── metrics.py
│   │   └── ops/                   # 运营服务 (7个)
│   │
│   ├── events/                    # 事件驱动 (5个)
│   │   ├── producer.py            # 事件发布
│   │   ├── consumer.py            # 事件消费
│   │   ├── community_events.py    # 事件定义
│   │   └── point_events.py        # 积分事件
│   │
│   ├── clients/                   # 服务调用 (3个)
│   │   ├── user_client.py         # 用户服务客户端
│   │   └── ai_client.py           # AI服务客户端
│   │
│   ├── middleware/                 # 中间件 (4个)
│   │   ├── auth.py                # JWT认证
│   │   ├── ops_auth.py            # 运营权限
│   │   └── rate_limit.py          # 限流
│   │
│   ├── utils/                     # 工具 (6个)
│   │   ├── markdown.py            # Markdown渲染
│   │   ├── sensitive_words.py     # 敏感词
│   │   ├── scoring.py             # 评分算法
│   │   └── logging_config.py      # 日志配置
│   │
│   ├── errors/                    # 错误处理 (2个)
│   │   ├── error_codes.py         # 错误码
│   │   └── exception_handlers.py  # 异常处理
│   │
│   ├── cache/                     # 缓存 (3个)
│   │   ├── post_cache.py
│   │   └── hot_cache.py
│   │
│   ├── schemas/                    # 数据校验 (3个)
│   │   └── *.py
│   │
│   └── scheduler/                 # 定时任务 (2个)
│       └── tasks.py
│
├── alembic/versions/              # 数据库迁移 (6个)
├── scripts/                        # 脚本
│   └── init_ops_data.py           # 初始化数据
└── tests/                         # 测试 (6个)
```

### 2.2 数据模型

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Post     │────<│   Comment   │     │    Topic    │
│    帖子     │1   N│    评论     │     │    话题     │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │              ┌─────────────┐          │
       │              │   Report    │          │
       │              │    举报     │          │
       │              └─────────────┘          │
       │                                       │
       │         ┌─────────────┐               │
       ├────────>│ Moderation  │               │
       │         │    审核     │               │
       │         └─────────────┘               │
       │                                       │
       │         ┌─────────────┐               │
       ├────────>│   Draft     │               │
       │         │    草稿     │               │
       │         └─────────────┘               │
       │                                       │
       │         ┌─────────────┐               │
       └────────>│  OpsRole    │               │
       │         │   运营角色   │               │
       │         └─────────────┘               │
       │                                       │
       │         ┌─────────────┐               │
       └────────>│ UserPenalty │               │
                 │   用户处罚   │               │
                 └─────────────┘               │
```

### 2.3 Kafka 事件流

```
                    ┌──────────────────┐
                    │   社区服务        │
                    │  (发布事件)       │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  积分服务   │     │  通知服务   │     │  搜索服务   │
│  (Points)   │     │ (Notify)   │     │ (Search)   │
└─────────────┘     └─────────────┘     └─────────────┘

                    ┌──────────────────┐
                    │   用户服务        │
                    │  (消费事件)       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   社区服务        │
                    │  (同步数据)       │
                    └──────────────────┘
```

---

## 3. API 接口

### 3.1 基础信息

| 属性 | 值 |
|------|-----|
| 基础路径 | `/api/v1/community` |
| 认证方式 | JWT Bearer Token |
| 数据格式 | JSON |
| 编码 | UTF-8 |

### 3.2 用户 API

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /posts | 创建帖子 | 用户 |
| GET | /posts | 帖子列表 | 公开 |
| GET | /posts/{id} | 帖子详情 | 公开 |
| PUT | /posts/{id} | 更新帖子 | 作者 |
| DELETE | /posts/{id} | 删除帖子 | 作者 |
| POST | /posts/{id}/like | 点赞 | 用户 |
| DELETE | /posts/{id}/like | 取消点赞 | 用户 |
| POST | /posts/{id}/favorite | 收藏 | 用户 |
| POST | /posts/{id}/report | 举报 | 用户 |
| GET | /posts/search | 搜索帖子 | 公开 |

### 3.3 评论 API

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /posts/{id}/comments | 创建评论 | 用户 |
| GET | /posts/{id}/comments | 评论列表 | 公开 |
| DELETE | /comments/{id} | 删除评论 | 作者 |

### 3.4 话题 API

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | /topics | 话题列表 | 公开 |
| GET | /topics/{slug} | 话题详情 | 公开 |
| POST | /topics/{slug}/posts | 话题发帖 | 用户 |
| POST | /topics/{slug}/best-answer | 标记最佳回答 | 作者 |

### 3.5 热门内容 API

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | /hot/posts | 热门帖子 | 公开 |
| GET | /hot/topics | 热门话题 | 公开 |

### 3.6 管理 API

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | /admin/moderation/queue | 审核队列 | 审核员 |
| POST | /admin/moderation/{id}/review | 审核操作 | 审核员 |
| GET | /admin/dashboard/stats | 统计数据 | 管理员 |

### 3.7 运营 API

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | /ops/roles | 角色列表 | 总监 |
| POST | /ops/roles/assign | 分配角色 | 总监 |
| GET | /ops/audit/logs | 审计日志 | 总监 |
| GET | /ops/content/queue | 审核工作台 | 审核员 |
| POST | /ops/content/queue/{id}/review | 审核内容 | 审核员 |
| POST | /ops/users/{id}/penalty | 处罚用户 | 用户运营 |
| GET | /ops/analytics/overview | 运营概览 | 数据分析 |
| GET | /ops/config/rules | 社区规则 | 总监 |

### 3.8 系统 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |
| GET | /health/ready | 就绪检查 |
| GET | /health/live | 存活检查 |
| GET | /metrics | Prometheus指标 |

---

## 4. 跨域调用

### 4.1 调用其他服务

#### 用户服务 (User Service)

```python
from app.clients.user_client import user_service_client

# 获取用户信息
user_info = await user_service_client.get_user_info(user_id=123)

# 验证Token
token_info = await user_service_client.verify_token(token)

# 获取用户权限
permissions = await user_service_client.get_user_permissions(user_id=123)
```

#### AI 服务 (AI Service)

```python
from app.clients.ai_client import ai_client

# 内容审核
result = await ai_client.analyze_content(content="待审核内容")

# 法律建议检查
legal_check = await ai_client.check_legal_advice(content="法律内容")
```

### 4.2 Kafka 事件发布

```python
from app.events.producer import event_bus

# 发布帖子创建事件
await event_bus.publish_post_created(
    post_id=1,
    user_id=123,
    title="标题",
    content="内容"
)

# 发布点赞事件
await event_bus.publish_post_liked(post_id=1, user_id=456)
```

### 4.3 Kafka 事件消费

```python
from app.events.consumer import user_event_consumer

# 消费用户事件
@user_event_consumer.register_handler("user.profile.updated")
async def handle_profile_updated(event):
    # 同步用户信息到帖子
    pass

@user_event_consumer.register_handler("user.lawyer.verified")
async def handle_lawyer_verified(event):
    # 更新帖子律师标识
    pass
```

### 4.4 运营事件

```python
from app.events.producer import ops_event_bus

# 发布处罚事件
await ops_event_bus.publish_user_penalized(
    user_id=123,
    penalty_type="mute",
    reason="违规发言"
)

# 发布公告事件
await ops_event_bus.publish_announcement(
    announcement_id=1,
    title="系统公告",
    content="内容"
)
```

---

## 5. 数据库

### 5.1 迁移

```bash
# 查看当前版本
alembic current

# 升级到最新
alembic upgrade head

# 降级
alembic downgrade -1

# 生成新迁移
alembic revision --autogenerate -m "描述"
```

### 5.2 表结构

| 表名 | 说明 |
|------|------|
| posts | 帖子表 |
| comments | 评论表 |
| topics | 话题表 |
| post_likes | 点赞表 |
| post_favorites | 收藏表 |
| reports | 举报表 |
| moderation_queue | 审核队列表 |
| draft_posts | 草稿表 |
| ops_role | 运营角色表 |
| ops_audit_log | 审计日志表 |
| user_penalty | 用户处罚表 |
| user_appeal | 用户申诉表 |
| announcement | 公告表 |
| ops_config | 运营配置表 |
| recommendation_slot | 推荐位表 |

---

## 6. 配置

### 6.1 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DATABASE_URL | sqlite+aiosqlite:///./community_service.db | 数据库连接 |
| KAFKA_BOOTSTRAP_SERVERS | localhost:9092 | Kafka地址 |
| KAFKA_ENABLED | false | 是否启用Kafka |
| REDIS_URL | redis://localhost:6379 | Redis地址 |
| USER_SERVICE_URL | http://localhost:8001 | 用户服务地址 |
| AI_SERVICE_URL | http://localhost:8005 | AI服务地址 |
| SERVICE_NAME | community-service | 服务名称 |
| SERVICE_HOST | 0.0.0.0 | 监听地址 |
| SERVICE_PORT | 8007 | 监听端口 |

### 6.2 ConfigManager

支持从 Consul KV 或 YAML 文件加载配置：

```yaml
# config.yaml
database:
  url: postgresql+asyncpg://user:pass@localhost/community
  pool_size: 10
  max_overflow: 20

kafka:
  bootstrap_servers: localhost:9092
  enabled: true

service:
  name: community-service
  host: 0.0.0.0
  port: 8007
```

---

## 7. 部署

### 7.1 Docker

```bash
# 构建镜像
docker build -t community-service:latest .

# 运行容器
docker run -d \
  --name community-service \
  -p 8007:8007 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  community-service:latest
```

### 7.2 直接运行

```bash
# 安装依赖
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 初始化数据
python -m scripts.init_ops_data

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8007
```

---

## 8. 运营

### 8.1 运营角色

| 角色 | 权限 | 说明 |
|------|------|------|
| community_director | 所有权限 | 社区运营总监 |
| content_mod | 内容审核 | 审核员 |
| topic_ops | 话题运营 | 置顶/加精/推荐 |
| user_ops | 用户运营 | 处罚/通知 |
| data_analyst | 数据分析 | 查看统计数据 |

### 8.2 内容审核流程

```
用户发帖
    │
    ▼
敏感词检测 ──> 命中 ──> 直接拒绝
    │
    │
    ▼
AI审核 ──> 高置信度违规 ──> 直接拒绝
    │
    │
    ▼
人工审核队列 ──> 审核员处理 ──> 通过/拒绝/修改
    │
    │
    ▼
发布
```

### 8.3 用户处罚

| 处罚类型 | 说明 | 时长 |
|---------|------|------|
| warning | 警告 | 永久 |
| mute | 禁言 | 可设置 |
| ban | 封禁 | 可设置 |

---

## 9. 监控

### 9.1 Prometheus 指标

```
# 请求指标
http_requests_total{method, endpoint, status}
http_request_duration_seconds{method, endpoint}

# 业务指标
posts_created_total
comments_created_total
likes_total

# Kafka 指标
kafka_messages_produced_total
kafka_messages_consumed_total
kafka_dlq_messages_total
```

### 9.2 日志

JSON格式日志，支持trace_id追踪：

```json
{
  "timestamp": "2026-03-23T10:00:00Z",
  "level": "INFO",
  "trace_id": "abc123",
  "service": "community-service",
  "message": "Post created",
  "post_id": 1,
  "user_id": 123
}
```

---

## 10. 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_community_service.py

# 带覆盖率
pytest --cov=app tests/
```

---

## 11. 常见问题

### Q: Kafka 未启用时服务能正常运行吗？
A: 可以，设置 `KAFKA_ENABLED=false` 即可。

### Q: 如何添加新的敏感词？
A: 通过运营 API `POST /api/v1/community/ops/config/sensitive-words` 添加。

### Q: 帖子审核被拒绝后会自动处罚用户吗？
A: 审核时可以勾选是否同时处罚用户。

### Q: 如何查看审计日志？
A: 通过运营 API `GET /api/v1/community/ops/audit/logs` 查看。
