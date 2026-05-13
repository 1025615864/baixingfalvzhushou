# 新闻服务 (News Service)

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | news-service |
| 端口 | 8006 |
| 基础路径 | /api/v1/news |
| 技术栈 | FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis |
| 数据库 | news_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |
| 存活检查 | GET /health/live |

## 服务描述

新闻服务负责法律新闻资讯的发布、分类、搜索与订阅管理。提供新闻文章 CRUD、评论管理、分类标签体系、用户订阅与收藏等功能，并通过 Kafka 发布新闻事件供其他服务消费。

## API 端点

### 新闻路由 (news_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /categories | 获取新闻分类列表 | 否 |
| GET | /tags | 获取标签列表 | 否 |
| GET | / | 获取新闻列表（分页） | 否 |
| GET | /category/{category_id} | 按分类获取新闻 | 否 |
| GET | /{news_id} | 获取新闻详情 | 否 |
| POST | /{news_id}/bookmark | 收藏新闻 | 是 |
| DELETE | /{news_id}/bookmark | 取消收藏 | 是 |
| GET | /user/bookmarks | 获取用户收藏列表 | 是 |
| GET | /search | 搜索新闻 | 否 |

### 评论路由 (comment_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /{news_id}/comments | 获取评论列表 | 否 |
| POST | /{news_id}/comments | 创建评论 | 是 |
| PATCH | /{comment_id}/approve | 审核通过评论 | 是 |
| PATCH | /{comment_id}/reject | 审核拒绝评论 | 是 |
| DELETE | /{comment_id} | 删除评论 | 是 |

### 订阅路由 (subscription_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | / | 获取订阅列表 | 是 |
| POST | / | 创建订阅 | 是 |
| PATCH | /{subscription_id}/toggle | 切换订阅状态 | 是 |
| DELETE | /{subscription_id} | 删除订阅 | 是 |

## 数据模型

| 模型 | 说明 |
|------|------|
| News | 新闻文章（标题、内容、分类、标签、浏览量、状态） |
| Comment | 评论（内容、用户ID、新闻ID、审核状态） |
| Category | 分类（名称、描述、排序） |
| Tag | 标签（名称、关联新闻） |
| Subscription | 订阅（用户ID、分类/标签、状态） |
| Bookmark | 收藏（用户ID、新闻ID） |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| recommendation-service | HTTP | 提供新闻数据用于个性化推荐 |
| community-service | Kafka | 新闻事件驱动社区讨论 |
| search-service | HTTP | 新闻搜索聚合 |
| backend-bff | HTTP | BFF 聚合新闻接口 |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| SERVICE_PORT | 8006 | 服务端口 |
| DATABASE_URL | - | PostgreSQL 连接串 |
| REDIS_URL | - | Redis 连接串 |
| KAFKA_BOOTSTRAP_SERVERS | kafka:9092 | Kafka 地址 |
| ENABLE_KAFKA_PRODUCER | false | 是否启用 Kafka 生产者 |
| OTEL_EXPORTER_OTLP_ENDPOINT | - | OpenTelemetry 端点 |
| CONSUL_ENABLED | false | 是否启用 Consul 注册 |

## 部署信息

- Dockerfile: services/news-service/Dockerfile
- 健康检查: /health
- 资源限制: CPU 0.5核 / 内存 512MB
