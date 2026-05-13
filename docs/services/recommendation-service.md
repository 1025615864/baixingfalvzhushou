# 推荐服务 (Recommendation Service)

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | recommendation-service |
| 端口 | 8010 |
| 基础路径 | /api/v1/recommendations |
| 技术栈 | FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis |
| 数据库 | recommendation_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |
| 存活检查 | GET /health/live |

## 服务描述

推荐服务基于用户行为和兴趣偏好，提供个性化内容推荐。支持律师推荐、新闻推荐、知识文章推荐等场景，通过 Kafka 消费用户行为事件实时更新推荐模型，使用 Redis 缓存推荐结果。

## API 端点

### 推荐路由 (recommendation_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /recommendations | 获取个性化推荐列表 | 是 |

## 数据模型

| 模型 | 说明 |
|------|------|
| UserBehavior | 用户行为（浏览、点击、收藏等） |
| UserInterest | 用户兴趣标签 |
| RecommendationLog | 推荐日志（推荐内容、用户反馈） |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| user-service | HTTP | 获取用户画像、兴趣标签 |
| news-service | HTTP | 获取新闻数据用于推荐 |
| community-service | HTTP | 获取帖子数据用于推荐 |
| legal-service | HTTP | 获取律师数据用于推荐 |
| knowledge-service | HTTP | 获取知识文章用于推荐 |
| backend-bff | HTTP | BFF 聚合推荐接口 |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| SERVICE_PORT | 8010 | 服务端口 |
| DATABASE_URL | - | PostgreSQL 连接串 |
| REDIS_URL | - | Redis 连接串 |
| KAFKA_BOOTSTRAP_SERVERS | kafka:9092 | Kafka 地址 |
| OTEL_EXPORTER_OTLP_ENDPOINT | - | OpenTelemetry 端点 |
| CONSUL_ENABLED | false | 是否启用 Consul 注册 |

## 部署信息

- Dockerfile: services/recommendation-service/Dockerfile
- 健康检查: /health
- 资源限制: CPU 0.5核 / 内存 512MB
